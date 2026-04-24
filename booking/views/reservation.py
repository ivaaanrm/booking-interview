from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from typing import TYPE_CHECKING

from booking.serializers import ReservationReadSerializer, ReservationWriteSerializer
from booking.services import get_reservations_for_user

if TYPE_CHECKING:
    from booking.models import Reservation


class ReservationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = get_reservations_for_user(self.request.user)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='status',
                location=OpenApiParameter.QUERY,
                description='Filter by reservation status: PENDIENTE, ACEPTADO, DENEGADO, EXPIRADO',
                required=False,
                type=OpenApiTypes.STR,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action in {"list", "retrieve"}:
            return ReservationReadSerializer
        return ReservationWriteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = serializer.save()
        output = ReservationReadSerializer(reservation, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance: Reservation = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        reservation = serializer.save()
        output = ReservationReadSerializer(reservation, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_200_OK)
