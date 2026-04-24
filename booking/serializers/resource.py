from rest_framework import serializers

from booking.models import Resource


class ResourceSerializer(serializers.ModelSerializer):
    attributes = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = [
            "id",
            "nombre",
            "descripcion",
            "resource_type",
            "booking_unit",
            "image_url",
            "attributes",
            "created_at",
            "updated_at",
        ]

    def get_attributes(self, obj: Resource) -> dict:
        attributes = dict(obj.metadata or {})
        if obj.resource_type == Resource.Type.SALA:
            attributes["capacity"] = obj.capacity
            attributes["shared_capacity"] = obj.shared_capacity
        return attributes
