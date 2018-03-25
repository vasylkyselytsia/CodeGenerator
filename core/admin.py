from django.contrib import admin
from django.contrib.auth import models as auth_models
# from django.template.loader import render_to_string

from core import models


class RemovePermissionMixin(object):

    CLOSED_PERMISSIONS = ["add", "change", "delete"]

    def has_add_permission(self, request):
        if "add" in self.CLOSED_PERMISSIONS:
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        if "delete" in self.CLOSED_PERMISSIONS:
            return False
        return super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if "change" in self.CLOSED_PERMISSIONS:
            return False
        return super().has_change_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete" in self.CLOSED_PERMISSIONS:
            actions.pop('delete_selected', None)
        return actions


@admin.register(models.Language)
class LanguageAdmin(RemovePermissionMixin, admin.ModelAdmin):
    CLOSED_PERMISSIONS = ["add", "delete"]
    search_fields = ("name",)
    list_display = ("name",)
    readonly_fields = list_display
    icon = '<i class="material-icons">settings</i>'


admin.site.unregister(auth_models.Group)
admin.site.unregister(auth_models.User)
