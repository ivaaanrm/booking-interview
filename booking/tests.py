from datetime import datetime, timedelta

from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import GROUP_RESPONSABLE, GROUP_TRABAJADOR, Reservation, Resource, User


class BookingApiTests(APITestCase):
    def setUp(self):
        worker_group, _ = Group.objects.get_or_create(name=GROUP_TRABAJADOR)
        manager_group, _ = Group.objects.get_or_create(name=GROUP_RESPONSABLE)

        self.worker = User.objects.create_user(username="worker", password="secret123")
        self.worker.groups.add(worker_group)

        self.other_worker = User.objects.create_user(username="worker2", password="secret123")
        self.other_worker.groups.add(worker_group)

        self.manager = User.objects.create_user(username="manager", password="secret123")
        self.manager.groups.add(manager_group)

        self.room = Resource.objects.create(
            nombre="Sala Nexus",
            descripcion="Sala de reuniones principal",
            resource_type=Resource.Type.SALA,
            booking_unit=Resource.BookingUnit.HOUR,
            capacity=1,
            shared_capacity=False,
            metadata={"max_people": 8},
        )
        self.shared_room = Resource.objects.create(
            nombre="Auditorio",
            descripcion="Sala con aforo compartido",
            resource_type=Resource.Type.SALA,
            booking_unit=Resource.BookingUnit.HOUR,
            capacity=5,
            shared_capacity=True,
            metadata={"max_people": 40},
        )
        self.vehicle = Resource.objects.create(
            nombre="Furgoneta 1",
            descripcion="Vehiculo de empresa",
            resource_type=Resource.Type.VEHICULO,
            booking_unit=Resource.BookingUnit.DAY,
            capacity=1,
            shared_capacity=False,
        )

    def _dt(self, hour, minute=0, *, day=24):
        return timezone.make_aware(datetime(2026, 4, day, hour, minute))

    def test_worker_creates_pending_reservation(self):
        client = APIClient()
        client.force_authenticate(user=self.worker)

        response = client.post(
            "/reservations",
            {
                "resource_id": self.room.id,
                "start_at": self._dt(10).isoformat(),
                "end_at": self._dt(12).isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Reservation.Status.PENDIENTE)
        self.assertTrue(Reservation.objects.filter(id=response.data["id"]).exists())

    def test_worker_cannot_overlap_existing_pending_reservation(self):
        Reservation.objects.create(
            user=self.other_worker,
            resource=self.room,
            status=Reservation.Status.PENDIENTE,
            start_at=self._dt(10),
            end_at=self._dt(12),
        )
        client = APIClient()
        client.force_authenticate(user=self.worker)

        response = client.post(
            "/reservations",
            {
                "resource_id": self.room.id,
                "start_at": self._dt(11).isoformat(),
                "end_at": self._dt(13).isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_responsable_can_book_over_pending_reservation(self):
        Reservation.objects.create(
            user=self.worker,
            resource=self.room,
            status=Reservation.Status.PENDIENTE,
            start_at=self._dt(10),
            end_at=self._dt(12),
        )
        client = APIClient()
        client.force_authenticate(user=self.manager)

        response = client.post(
            "/reservations",
            {
                "resource_id": self.room.id,
                "start_at": self._dt(10).isoformat(),
                "end_at": self._dt(12).isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Reservation.Status.ACEPTADO)
        self.assertEqual(response.data["approved_by"]["id"], self.manager.id)

    def test_responsable_can_approve_with_patch(self):
        reservation = Reservation.objects.create(
            user=self.worker,
            resource=self.room,
            status=Reservation.Status.PENDIENTE,
            start_at=self._dt(14),
            end_at=self._dt(15),
        )
        client = APIClient()
        client.force_authenticate(user=self.manager)

        response = client.patch(
            f"/reservations/{reservation.id}",
            {"status": Reservation.Status.ACEPTADO},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.ACEPTADO)
        self.assertEqual(reservation.approved_by_id, self.manager.id)

    def test_worker_only_sees_own_reservations(self):
        own_reservation = Reservation.objects.create(
            user=self.worker,
            resource=self.room,
            status=Reservation.Status.PENDIENTE,
            start_at=self._dt(9),
            end_at=self._dt(10),
        )
        Reservation.objects.create(
            user=self.other_worker,
            resource=self.room,
            status=Reservation.Status.PENDIENTE,
            start_at=self._dt(11),
            end_at=self._dt(12),
        )
        client = APIClient()
        client.force_authenticate(user=self.worker)

        response = client.get("/reservations")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], own_reservation.id)

    def test_availability_reports_remaining_capacity_and_pending_blocks(self):
        Reservation.objects.create(
            user=self.worker,
            resource=self.shared_room,
            status=Reservation.Status.PENDIENTE,
            start_at=self._dt(10),
            end_at=self._dt(12),
            quantity=3,
        )
        client = APIClient()
        client.force_authenticate(user=self.worker)

        response = client.get(f"/resources/{self.shared_room.id}/availability?date=2026-04-24")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["capacity"], 5)
        self.assertEqual(response.data["blocking_reservations"][0]["status"], Reservation.Status.PENDIENTE)
        matching_segments = [
            segment
            for segment in response.data["available_ranges"]
            if segment["start_at"].startswith("2026-04-24T10:00:00")
        ]
        self.assertEqual(matching_segments[0]["remaining_capacity"], 2)

    def test_worker_blocked_by_accepted_reservation(self):
        Reservation.objects.create(
            user=self.other_worker,
            resource=self.room,
            status=Reservation.Status.ACEPTADO,
            start_at=self._dt(10),
            end_at=self._dt(12),
        )
        client = APIClient()
        client.force_authenticate(user=self.worker)

        response = client.post(
            "/reservations",
            {
                "resource_id": self.room.id,
                "start_at": self._dt(11).isoformat(),
                "end_at": self._dt(13).isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_responsable_blocked_by_accepted_reservation(self):
        Reservation.objects.create(
            user=self.worker,
            resource=self.room,
            status=Reservation.Status.ACEPTADO,
            start_at=self._dt(10),
            end_at=self._dt(12),
        )
        client = APIClient()
        client.force_authenticate(user=self.manager)

        response = client.post(
            "/reservations",
            {
                "resource_id": self.room.id,
                "start_at": self._dt(10).isoformat(),
                "end_at": self._dt(12).isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_shared_room_blocks_when_at_full_capacity(self):
        Reservation.objects.create(
            user=self.other_worker,
            resource=self.shared_room,
            status=Reservation.Status.ACEPTADO,
            start_at=self._dt(10),
            end_at=self._dt(12),
            quantity=5,
        )
        client = APIClient()
        client.force_authenticate(user=self.worker)

        response = client.post(
            "/reservations",
            {
                "resource_id": self.shared_room.id,
                "start_at": self._dt(10).isoformat(),
                "end_at": self._dt(11).isoformat(),
                "quantity": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", response.data)

    def test_vehicle_blocked_when_already_booked_for_day(self):
        day_start = timezone.make_aware(datetime(2026, 4, 25, 0, 0))
        day_end = timezone.make_aware(datetime(2026, 4, 26, 0, 0))
        Reservation.objects.create(
            user=self.other_worker,
            resource=self.vehicle,
            status=Reservation.Status.ACEPTADO,
            start_at=day_start,
            end_at=day_end,
        )
        client = APIClient()
        client.force_authenticate(user=self.worker)

        response = client.post(
            "/reservations",
            {
                "resource_id": self.vehicle.id,
                "start_at": day_start.isoformat(),
                "end_at": day_end.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_vehicle_requires_full_day_window(self):
        client = APIClient()
        client.force_authenticate(user=self.worker)

        response = client.post(
            "/reservations",
            {
                "resource_id": self.vehicle.id,
                "start_at": self._dt(10).isoformat(),
                "end_at": (self._dt(10) + timedelta(hours=8)).isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("start_at", response.data)
