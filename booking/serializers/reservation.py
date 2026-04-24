from __future__ import annotations

from rest_framework import serializers

from booking.models import Reservation, Resource
from booking.services import create_reservation, ensure_no_conflicts, update_reservation, validate_reservation_window

from .resource import ResourceSerializer
from .user import UserSerializer


class ReservationReadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    resource = ResourceSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id",
            "user",
            "resource",
            "approved_by",
            "status",
            "start_at",
            "end_at",
            "quantity",
            "created_at",
            "updated_at",
        ]


class ReservationWriteSerializer(serializers.ModelSerializer):
    resource_id = serializers.PrimaryKeyRelatedField(
        source="resource",
        queryset=Resource.objects.all(),
    )

    class Meta:
        model = Reservation
        fields = ["resource_id", "start_at", "end_at", "quantity", "status"]
        extra_kwargs = {
            "quantity": {"required": False},
            "status": {"required": False},
        }

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        instance = getattr(self, "instance", None)

        resource = attrs.get("resource") or getattr(instance, "resource", None)
        start_at = attrs.get("start_at") or getattr(instance, "start_at", None)
        end_at = attrs.get("end_at") or getattr(instance, "end_at", None)
        quantity = attrs.get("quantity", getattr(instance, "quantity", 1))
        status = attrs.get("status", getattr(instance, "status", None))

        if resource is None or start_at is None or end_at is None:
            return attrs

        validate_reservation_window(resource, start_at, end_at)

        if not user.is_responsable:
            if "status" in attrs and status != Reservation.Status.PENDIENTE:
                raise serializers.ValidationError(
                    {"status": "Only responsables can change the reservation status."}
                )
            attrs["status"] = Reservation.Status.PENDIENTE
        elif instance is None and "status" not in attrs:
            attrs["status"] = Reservation.Status.ACEPTADO

        candidate = Reservation(
            user=instance.user if instance else user,
            resource=resource,
            status=attrs.get("status", Reservation.Status.PENDIENTE),
            start_at=start_at,
            end_at=end_at,
            quantity=quantity,
            approved_by=instance.approved_by if instance else None,
        )
        candidate.full_clean()

        effective_status = attrs.get("status", getattr(instance, "status", Reservation.Status.PENDIENTE))
        if effective_status in (Reservation.Status.PENDIENTE, Reservation.Status.ACEPTADO):
            ensure_no_conflicts(
                resource=resource,
                start_at=start_at,
                end_at=end_at,
                quantity=quantity,
                acting_user=user,
                exclude_id=instance.id if instance else None,
            )

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        return create_reservation(user=user, validated_data=validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        return update_reservation(reservation=instance, validated_data=validated_data, acting_user=user)
