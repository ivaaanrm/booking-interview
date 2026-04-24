from __future__ import annotations

from datetime import datetime, time, timedelta

from booking.exceptions import CapacityExceededError, ConflictError, ReservationWindowError
from booking.models import Reservation, Resource, User


def validate_reservation_window(resource: Resource, start_at: datetime, end_at: datetime) -> None:
    if start_at >= end_at:
        raise ReservationWindowError("End must be after start.", field="end_at")

    if resource.booking_unit == Resource.BookingUnit.DAY:
        if start_at.timetz() != time(0, 0, tzinfo=start_at.timetz().tzinfo):
            raise ReservationWindowError("Day bookings must start at 00:00.", field="start_at")
        if end_at.timetz() != time(0, 0, tzinfo=end_at.timetz().tzinfo):
            raise ReservationWindowError("Day bookings must end at 00:00.", field="end_at")
        if (end_at - start_at) < timedelta(days=1):
            raise ReservationWindowError("Day bookings must reserve at least one full day.", field="end_at")

    if resource.booking_unit == Resource.BookingUnit.HOUR and start_at.date() != end_at.date():
        raise ReservationWindowError("Hour bookings must start and end on the same day.", field="end_at")


def get_blocking_reservations(
    *,
    resource: Resource,
    start_at: datetime,
    end_at: datetime,
    acting_user: User,
    exclude_id: int | None = None,
):
    statuses = [Reservation.Status.ACEPTADO]
    if not acting_user.is_responsable:
        statuses.append(Reservation.Status.PENDIENTE)

    qs = Reservation.objects.filter(
        resource=resource,
        status__in=statuses,
        start_at__lt=end_at,
        end_at__gt=start_at,
    )
    if exclude_id is not None:
        qs = qs.exclude(pk=exclude_id)
    return qs


def _segment_boundaries(window_start: datetime, window_end: datetime, reservations) -> list[datetime]:
    boundaries = {window_start, window_end}
    for r in reservations:
        boundaries.add(max(window_start, r.start_at))
        boundaries.add(min(window_end, r.end_at))
    return sorted(boundaries)


def ensure_no_conflicts(
    *,
    resource: Resource,
    start_at: datetime,
    end_at: datetime,
    quantity: int,
    acting_user: User,
    exclude_id: int | None = None,
) -> None:
    blockers = list(get_blocking_reservations(
        resource=resource, start_at=start_at, end_at=end_at,
        acting_user=acting_user, exclude_id=exclude_id,
    ))

    if not blockers:
        return

    if not resource.shared_capacity:
        raise ConflictError()

    if quantity > resource.capacity:
        raise CapacityExceededError("Requested quantity exceeds the resource capacity.")

    segments = _segment_boundaries(start_at, end_at, blockers)
    for seg_start, seg_end in zip(segments, segments[1:]):
        if seg_start >= seg_end:
            continue
        used = sum(b.quantity for b in blockers if b.start_at < seg_end and b.end_at > seg_start)
        if used + quantity > resource.capacity:
            raise CapacityExceededError("Requested quantity exceeds the remaining shared capacity.")


def get_reservations_for_user(user: User):
    qs = Reservation.objects.select_related("user", "resource", "approved_by").order_by("start_at", "id")
    return qs if user.is_responsable else qs.filter(user=user)


def create_reservation(*, user: User, validated_data: dict) -> Reservation:
    approved_by = user if validated_data["status"] == Reservation.Status.ACEPTADO and user.is_responsable else None
    return Reservation.objects.create(user=user, approved_by=approved_by, **validated_data)


def update_reservation(*, reservation: Reservation, validated_data: dict, acting_user: User) -> Reservation:
    for field, value in validated_data.items():
        setattr(reservation, field, value)
    if "status" in validated_data:
        reservation.approved_by = (
            acting_user if validated_data["status"] == Reservation.Status.ACEPTADO else None
        )
    reservation.save()
    return reservation
