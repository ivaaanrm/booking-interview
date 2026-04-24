from rest_framework import serializers

from booking.models import User


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "role", "created_at"]

    def get_role(self, obj):
        return obj.role
