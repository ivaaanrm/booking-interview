from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

GROUP_TRABAJADOR = "Trabajador"
GROUP_RESPONSABLE = "Responsable"


class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_responsable(self):
        return self.groups.filter(name=GROUP_RESPONSABLE).exists()

    @property
    def role(self):
        return GROUP_RESPONSABLE.upper() if self.is_responsable else GROUP_TRABAJADOR.upper()

class Resource(models.Model):
    class Type(models.TextChoices):
        SALA = "SALA", "Sala"
        VEHICULO = "VEHICULO", "Vehiculo"
        EQUIPAMIENTO = "EQUIPAMIENTO", "Equipamiento"

    class BookingUnit(models.TextChoices):
        HOUR = "HOUR", "Hour"
        DAY = "DAY", "Day"

    nombre = models.CharField(max_length=50)
    descripcion = models.TextField()
    resource_type = models.CharField(max_length=20, choices=Type.choices)
    booking_unit = models.CharField(max_length=10, choices=BookingUnit.choices)
    image_url = models.URLField(blank=True)
    capacity = models.PositiveIntegerField(default=1)
    shared_capacity = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.capacity < 1:
            raise ValidationError({"capacity": "Capacity must be at least 1."})

        if self.resource_type == self.Type.SALA and self.booking_unit != self.BookingUnit.HOUR:
            raise ValidationError({"booking_unit": "Meeting rooms can only be booked by hour."})

        if self.resource_type == self.Type.VEHICULO:
            if self.booking_unit != self.BookingUnit.DAY:
                raise ValidationError({"booking_unit": "Vehicles can only be booked by full day."})
            if self.shared_capacity:
                raise ValidationError({"shared_capacity": "Vehicles do not support shared capacity."})
            if self.capacity != 1:
                raise ValidationError({"capacity": "Vehicles must have a capacity of 1 reservation unit."})

        if not self.shared_capacity and self.capacity != 1:
            raise ValidationError(
                {"capacity": "Non-shared resources must have a capacity of 1 reservation unit."}
            )

    def __str__(self):
        return self.nombre


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        ACEPTADO = "ACEPTADO", "Aceptado"
        DENEGADO = "DENEGADO", "Denegado"
        EXPIRADO = "EXPIRADO", "Expirado"

    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="reservations")
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name="reservations")
    approved_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_reservations",
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDIENTE
    )

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_at", "id"]

    def clean(self):
        if self.start_at >= self.end_at:
            raise ValidationError("Reservation end must be after start.")

        if self.quantity < 1:
            raise ValidationError({"quantity": "Quantity must be at least 1."})

        if self.resource_id and not self.resource.shared_capacity and self.quantity != 1:
            raise ValidationError(
                {"quantity": "Quantity must be 1 when the resource does not have shared capacity."}
            )

    def __str__(self):
        return f"{self.resource.nombre} [{self.start_at} - {self.end_at}]"
