from django.apps import AppConfig
from django.db.models import CharField, TextField
from django.db.models.functions import Length


class ComumConfig(AppConfig):
    name = "comum"

    def ready(self) -> None:
        # Permite escrever Q(campo__length__gte=n) nas CheckConstraints (skill postgresql).
        CharField.register_lookup(Length)
        TextField.register_lookup(Length)
