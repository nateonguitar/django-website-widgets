from django.contrib import admin

from api.models import CopyReport


@admin.register(CopyReport)
class CopyReportAdmin(admin.ModelAdmin):
    """Reports come from the site and are history, so here they are only read."""

    list_display = ['reported_at', 'copy', 'user', 'kind', 'unrecoverable']
    list_select_related = ['copy__movie', 'user']
    list_filter = ['kind', 'unrecoverable']
    search_fields = ['copy__label', 'copy__movie__title', 'user__username', 'notes']
    date_hierarchy = 'reported_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
