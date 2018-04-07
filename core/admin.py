from django.contrib import admin
from django.contrib.auth import models as auth_models
from django.conf.urls import url
from django.urls import reverse
from django.utils.html import format_html
from django.template.response import TemplateResponse

from core import models
from core.generator import CodeGenerator


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
    icon = '<i class="material-icons">language</i>'


@admin.register(models.Function)
class FunctionAdmin(admin.ModelAdmin):
    search_fields = ("name", "value")
    list_display = ("language", "name", "value",)
    list_filter = ("language",)
    icon = '<i class="material-icons">build</i>'
    ordering = ("language", "value")


@admin.register(models.Keyword)
class KeywordAdmin(admin.ModelAdmin):
    search_fields = ("name", "value")
    list_display = ("language", "name", "value",)
    list_filter = ("language",)
    icon = '<i class="material-icons">vpn_key</i>'
    ordering = ("language", "value")


class AddOnesInline(admin.StackedInline):
    extra = 1
    fields = ('name', 'v_type', 'default')
    model = models.AddOnes


class AddOnesFuncInline(admin.StackedInline):
    extra = 1
    fields = ('name', 'f_type')
    model = models.FuncAddOnes


@admin.register(models.CodeTemplate)
class CodeTemplateAdmin(RemovePermissionMixin, admin.ModelAdmin):
    CLOSED_PERMISSIONS = ["delete"]
    search_fields = ("language__name", "name")
    list_display = ("language", "name", "create_dt", "view_actions")
    icon = '<i class="material-icons">code</i>'
    inlines = [AddOnesInline, AddOnesFuncInline]

    def process_view(self, request, template_id):
        code = self.get_object(request, template_id)
        context = {
            "code": CodeGenerator(code).generate(),
            "title": "{} | {}".format(code.language, code.name)
        }
        return TemplateResponse(request, 'code_view.html', context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url(
                r'^(?P<template_id>.+)/view-code/$',
                self.admin_site.admin_view(self.process_view),
                name='view-code',
            )
        ]
        return custom_urls + urls

    def view_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Згенерувати код</a>',
            reverse('admin:view-code', args=[obj.pk])
        )

    view_actions.short_description = 'Дії'
    view_actions.allow_tags = True


admin.site.unregister(auth_models.Group)
# admin.site.unregister(auth_models.User)
