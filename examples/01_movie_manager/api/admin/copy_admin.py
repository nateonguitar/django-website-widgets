from django.contrib import admin
from django.db.models import Exists, OuterRef

from api.models import Copy, CopyReport, Rental


class OnTheShelfFilter(admin.SimpleListFilter):
    """Filters on `is_out`, which CopyAdmin.get_queryset() annotates before any filter runs."""

    title = 'on the shelf'
    parameter_name = 'on_the_shelf'

    def lookups(self, request, model_admin):
        return [('yes', 'Yes'), ('no', 'No, someone has it')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(is_out=False)
        if self.value() == 'no':
            return queryset.filter(is_out=True)
        return queryset


class InRotationFilter(admin.SimpleListFilter):
    title = 'in rotation'
    parameter_name = 'in_rotation'

    def lookups(self, request, model_admin):
        return [('yes', 'Yes'), ('no', 'No, retired')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(retired_at__isnull=True)
        if self.value() == 'no':
            return queryset.filter(retired_at__isnull=False)
        return queryset


class CopyReportInline(admin.TabularInline):
    """The copy's reports, as history: added from the site, never here."""

    model = CopyReport
    fields = ['reported_at', 'user', 'kind', 'notes', 'unrecoverable']
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Copy)
class CopyAdmin(admin.ModelAdmin):
    list_display = ['label', 'movie', 'added_at', 'on_the_shelf', 'in_rotation']
    list_filter = [OnTheShelfFilter, InRotationFilter]
    list_select_related = ['movie']
    search_fields = ['label', 'movie__title']
    autocomplete_fields = ['movie']
    readonly_fields = ['label', 'retired_at']
    date_hierarchy = 'added_at'
    inlines = [CopyReportInline]

    def get_queryset(self, request):
        open_rental = Rental.objects.filter(copy=OuterRef('pk'), returned_at__isnull=True)
        return super().get_queryset(request).annotate(is_out=Exists(open_rental))

    @admin.display(description='On the shelf', boolean=True, ordering='is_out')
    def on_the_shelf(self, copy):
        return not copy.is_out

    @admin.display(description='In rotation', boolean=True, ordering='retired_at')
    def in_rotation(self, copy):
        return copy.retired_at is None
