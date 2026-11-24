from django.contrib import admin


class SomenteLeituraAdmin(admin.ModelAdmin):
    """Admin que só exibe. A gravação desses models passa pelos services (ou pela trigger)."""

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
