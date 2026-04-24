from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import ReservationViewSet, ResourceViewSet

router = SimpleRouter(trailing_slash=False)
router.register("resources", ResourceViewSet, basename="resource")
router.register("reservations", ReservationViewSet, basename="reservation")

urlpatterns = [
    path("", include(router.urls)),
]
