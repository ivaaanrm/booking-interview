from django.core.exceptions import ValidationError
from django.db import models

from .resource import Resource


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        ACEPTADO = "ACEPTADO", "Aceptado"
        DENEGADO = "DENEGADO", "Denegado"
        EXPIRADO = "EXPIRADO", "Expirado"

    user = models.ForeignKey("booking.User", on_delete=models.CASCADE, related_name="reservations")
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name="reservations")
    approved_by = models.ForeignKey(
        "booking.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_reservations",
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDIENTE,
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
