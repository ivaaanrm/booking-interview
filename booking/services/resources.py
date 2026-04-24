from __future__ import annotations

from datetime import datetime, time, timedelta

from django.utils import timezone

from booking.models import Reservation, Resource

_BLOCKING_STATUSES = [Reservation.Status.PENDIENTE, Reservation.Status.ACEPTADO]


def get_availability(resource: Resource, date_value) -> dict:
    day_start = timezone.make_aware(datetime.combine(date_value, time.min))
    day_end = day_start + timedelta(days=1)

    reservations = list(
        Reservation.objects.filter(
            resource=resource,
            status__in=_BLOCKING_STATUSES,
            start_at__lt=day_end,
            end_at__gt=day_start,
        ).order_by("start_at", "id")
    )

    payload = {
        "resource_id": resource.id,
        "date": date_value.isoformat(),
        "booking_unit": resource.booking_unit,
        "shared_capacity": resource.shared_capacity,
        "capacity": resource.capacity,
        "blocking_reservations": [_reservation_block(r) for r in reservations],
    }

    if resource.booking_unit == Resource.BookingUnit.DAY:
        used = sum(r.quantity for r in reservations)
        payload.update({
            "is_available": used < resource.capacity if resource.shared_capacity else not reservations,
            "remaining_capacity": max(resource.capacity - used, 0) if resource.shared_capacity else None,
        })
        return payload

    available, blocked = [], []
    segments = _segment_boundaries(day_start, day_end, reservations)
    for seg_start, seg_end in zip(segments, segments[1:]):
        if seg_start >= seg_end:
            continue
        overlapping = [r for r in reservations if r.start_at < seg_end and r.end_at > seg_start]
        if resource.shared_capacity:
            used = sum(r.quantity for r in overlapping)
            remaining = max(resource.capacity - used, 0)
            seg = {
                "start_at": seg_start.isoformat(),
                "end_at": seg_end.isoformat(),
                "remaining_capacity": remaining,
                "blocking_reservation_ids": [r.id for r in overlapping],
            }
            (available if remaining > 0 else blocked).append(seg)
        else:
            seg = {
                "start_at": seg_start.isoformat(),
                "end_at": seg_end.isoformat(),
                "blocking_reservation_ids": [r.id for r in overlapping],
            }
            (blocked if overlapping else available).append(seg)

    payload.update({"is_available": bool(available), "available_ranges": available, "blocked_ranges": blocked})
    return payload


def _segment_boundaries(window_start: datetime, window_end: datetime, reservations) -> list[datetime]:
    boundaries = {window_start, window_end}
    for r in reservations:
        boundaries.add(max(window_start, r.start_at))
        boundaries.add(min(window_end, r.end_at))
    return sorted(boundaries)


def _reservation_block(r: Reservation) -> dict:
    return {
        "id": r.id,
        "status": r.status,
        "user_id": r.user_id,
        "start_at": r.start_at.isoformat(),
        "end_at": r.end_at.isoformat(),
        "quantity": r.quantity,
    }
