from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Reservation, Resource, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "first_name", "last_name", "role", "is_staff", "created_at"]
    list_filter = ["groups", "is_staff"]
    search_fields = ["username", "first_name", "last_name"]
    ordering = ["username"]

    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {"fields": ("created_at",)}),
    )
    readonly_fields = ["created_at"]


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ["nombre", "resource_type", "booking_unit", "capacity", "shared_capacity"]
    list_filter = ["resource_type", "booking_unit", "shared_capacity"]
    search_fields = ["nombre", "descripcion"]


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ["resource", "user", "status", "start_at", "end_at", "quantity", "approved_by"]
    list_filter = ["status", "resource__resource_type"]
    search_fields = ["user__username", "resource__nombre"]
    raw_id_fields = ["user", "resource", "approved_by"]
