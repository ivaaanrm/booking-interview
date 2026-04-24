from datetime import datetime, timedelta
from django.db import migrations
from django.utils import timezone

GROUP_TRABAJADOR = "Trabajador"
GROUP_RESPONSABLE = "Responsable"


def seed(apps, schema_editor):
    User = apps.get_model("booking", "User")
    Resource = apps.get_model("booking", "Resource")
    Reservation = apps.get_model("booking", "Reservation")
    Group = apps.get_model("auth", "Group")

    worker_group, _ = Group.objects.get_or_create(name=GROUP_TRABAJADOR)
    manager_group, _ = Group.objects.get_or_create(name=GROUP_RESPONSABLE)

    worker = User.objects.create_user(
        username="ivan.romero",
        password="worker123",
        first_name="Ivan",
        last_name="Romero",
    )
    worker.groups.add(worker_group)

    manager = User.objects.create_user(
        username="admin",
        password="manager123",
        first_name="Admin",
        last_name="Prueba",
    )
    manager.groups.add(manager_group)

    Resource.objects.bulk_create([
        # Sales de reunions — HOUR, non-shared
        Resource(
            nombre="Sala Nexus",
            descripcion="Sala de reunions principal amb projector i pantalla gran.",
            resource_type="SALA",
            booking_unit="HOUR",
            capacity=1,
            shared_capacity=False,
            metadata={"max_people": 8, "projector": True, "whiteboard": True},
        ),
        Resource(
            nombre="Sala Àgora",
            descripcion="Sala petita per a reunions de fins a 4 persones.",
            resource_type="SALA",
            booking_unit="HOUR",
            capacity=1,
            shared_capacity=False,
            metadata={"max_people": 4, "projector": False, "whiteboard": True},
        ),
        # Sales de reunions — HOUR, shared capacity
        Resource(
            nombre="Auditori Central",
            descripcion="Auditori gran amb aforament compartit, ideal per a formacions.",
            resource_type="SALA",
            booking_unit="HOUR",
            capacity=10,
            shared_capacity=True,
            metadata={"max_people": 80, "projector": True, "microphone": True},
        ),
        Resource(
            nombre="Espai Coworking",
            descripcion="Zona de treball compartida amb llocs individuals reservables.",
            resource_type="SALA",
            booking_unit="HOUR",
            capacity=6,
            shared_capacity=True,
            metadata={"max_people": 6, "standing_desks": True, "monitors": True},
        ),
        # Vehicles — DAY
        Resource(
            nombre="Furgoneta Ford Transit",
            descripcion="Furgoneta de càrrega per a transport de materials.",
            resource_type="VEHICULO",
            booking_unit="DAY",
            capacity=1,
            shared_capacity=False,
            metadata={"seats": 3, "cargo_volume_m3": 8, "license_required": "B"},
        ),
        Resource(
            nombre="Turisme Seat León",
            descripcion="Cotxe de turisme per a desplaçaments comercials.",
            resource_type="VEHICULO",
            booking_unit="DAY",
            capacity=1,
            shared_capacity=False,
            metadata={"seats": 5, "fuel": "diesel", "license_required": "B"},
        ),
        Resource(
            nombre="Furgó Renault Master",
            descripcion="Furgó gran per a mudances i transports voluminosos.",
            resource_type="VEHICULO",
            booking_unit="DAY",
            capacity=1,
            shared_capacity=False,
            metadata={"seats": 2, "cargo_volume_m3": 17, "license_required": "C"},
        ),
        # Equipaments — HOUR
        Resource(
            nombre="Projector Portàtil",
            descripcion="Projector Full HD per a presentacions externes.",
            resource_type="EQUIPAMIENTO",
            booking_unit="HOUR",
            capacity=1,
            shared_capacity=False,
            metadata={"resolution": "1080p", "lumens": 3000, "includes_hdmi_cable": True},
        ),
        Resource(
            nombre="Kit Videoconferència",
            descripcion="Càmera 4K amb micròfon omnidireccional i altaveu.",
            resource_type="EQUIPAMIENTO",
            booking_unit="HOUR",
            capacity=1,
            shared_capacity=False,
            metadata={"camera_resolution": "4K", "max_participants": 20},
        ),
        # Equipaments — DAY
        Resource(
            nombre="Portàtil Dell XPS",
            descripcion="Portàtil d'alt rendiment per a treballs en mobilitat.",
            resource_type="EQUIPAMIENTO",
            booking_unit="DAY",
            capacity=1,
            shared_capacity=False,
            metadata={"ram_gb": 32, "storage_gb": 512, "os": "Windows 11"},
        ),
    ])

    # Create sample reservations for ivan.romero (worker)
    base_date = timezone.make_aware(datetime(2026, 5, 1, 0, 0, 0))

    Reservation.objects.bulk_create([
        # SALA HOUR non-shared
        Reservation(
            user=worker,
            resource=Resource.objects.get(id=1),
            start_at=base_date.replace(hour=9),
            end_at=base_date.replace(hour=11),
            quantity=1,
        ),
        # SALA HOUR shared
        Reservation(
            user=worker,
            resource=Resource.objects.get(id=3),
            start_at=base_date.replace(day=2, hour=10),
            end_at=base_date.replace(day=2, hour=12),
            quantity=3,
        ),
        # VEHICULO DAY
        Reservation(
            user=worker,
            resource=Resource.objects.get(id=5),
            start_at=(base_date + timedelta(days=3)).replace(hour=0),
            end_at=(base_date + timedelta(days=5)).replace(hour=0),
            quantity=1,
        ),
        # EQUIPAMIENTO HOUR
        Reservation(
            user=worker,
            resource=Resource.objects.get(id=8),
            start_at=base_date.replace(day=6, hour=14),
            end_at=base_date.replace(day=6, hour=15, minute=30),
            quantity=1,
        ),
        # EQUIPAMIENTO DAY
        Reservation(
            user=worker,
            resource=Resource.objects.get(id=10),
            start_at=(base_date + timedelta(days=7)).replace(hour=0),
            end_at=(base_date + timedelta(days=8)).replace(hour=0),
            quantity=1,
        ),
    ])


def unseed(apps, schema_editor):
    User = apps.get_model("booking", "User")
    Resource = apps.get_model("booking", "Resource")
    Reservation = apps.get_model("booking", "Reservation")
    Group = apps.get_model("auth", "Group")

    Reservation.objects.all().delete()
    User.objects.filter(username__in=["ivan.romero", "admin"]).delete()
    Resource.objects.all().delete()
    Group.objects.filter(name__in=[GROUP_TRABAJADOR, GROUP_RESPONSABLE]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("booking", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
