from django.contrib.auth.models import AbstractUser
from django.db import models

GROUP_TRABAJADOR = "Trabajador"
GROUP_RESPONSABLE = "Responsable"


class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_responsable(self):
        return self.groups.filter(name=GROUP_RESPONSABLE).exists()

    @property
    def role(self):
        return GROUP_RESPONSABLE.upper() if self.is_responsable else GROUP_TRABAJADOR.upper()
