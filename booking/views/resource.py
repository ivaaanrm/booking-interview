from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from booking.models import Resource
from booking.serializers import ResourceSerializer
from booking.services import get_availability


class ResourceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Resource.objects.all().order_by("id")
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="date",
                location=OpenApiParameter.QUERY,
                description="Date in YYYY-MM-DD format to check availability",
                required=True,
                type=OpenApiTypes.DATE,
            )
        ],
        description="Get availability for a resource on a specific date. Returns available time ranges for HOUR resources or availability status for DAY resources.",
        responses={200: dict},
    )
    @action(detail=True, methods=["get"])
    def availability(self, request, pk=None):
        date_param = request.query_params.get("date")
        if not date_param:
            return Response(
                {"date": ["This query parameter is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        date_value = parse_date(date_param)
        if date_value is None:
            return Response(
                {"date": ["Use the YYYY-MM-DD format."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resource = self.get_object()
        return Response(
            get_availability(resource, date_value), status=status.HTTP_200_OK
        )
