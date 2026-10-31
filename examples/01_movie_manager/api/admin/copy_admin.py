from django.contrib import admin
from django.db.models import Exists, OuterRef

from api.models import Copy, Rental


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


@admin.register(Copy)
class CopyAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'movie', 'added_at', 'on_the_shelf']
    list_filter = [OnTheShelfFilter]
    list_select_related = ['movie']
    search_fields = ['movie__title']
    autocomplete_fields = ['movie']
    date_hierarchy = 'added_at'

    def get_queryset(self, request):
        open_rental = Rental.objects.filter(copy=OuterRef('pk'), returned_at__isnull=True)
        return super().get_queryset(request).annotate(is_out=Exists(open_rental))

    @admin.display(description='On the shelf', boolean=True, ordering='is_out')
    def on_the_shelf(self, copy):
        return not copy.is_out
