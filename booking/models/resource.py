from django.core.exceptions import ValidationError
from django.db import models


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
