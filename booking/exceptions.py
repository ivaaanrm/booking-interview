from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class BookingError(Exception):
    """Base class for domain errors raised in the service layer."""
    status_code = 400
    field: str | None = None
    default_detail = "Booking error."

    def __init__(self, detail: str | None = None, field: str | None = None):
        self.detail = detail or self.default_detail
        if field is not None:
            self.field = field


class ReservationWindowError(BookingError):
    """Raised when start/end times violate the resource booking unit rules."""
    def __init__(self, detail: str, field: str):
        super().__init__(detail=detail, field=field)


class ConflictError(BookingError):
    """Raised when a reservation overlaps an existing blocking reservation."""
    default_detail = "The resource is not available in the selected time range."


class CapacityExceededError(BookingError):
    """Raised when the requested quantity exceeds available shared capacity."""
    field = "quantity"
    default_detail = "Requested quantity exceeds the available capacity."


def booking_exception_handler(exc, context):
    if isinstance(exc, BookingError):
        key = exc.field or "non_field_errors"
        return Response({key: [exc.detail]}, status=exc.status_code)

    if isinstance(exc, DjangoValidationError):
        data = exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}
        return Response(data, status=400)

    return drf_exception_handler(exc, context)
