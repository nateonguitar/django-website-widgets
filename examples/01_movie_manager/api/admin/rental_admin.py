from django.contrib import admin
from django.utils import timezone

from api.admin.widgets.return_rental_field import ReturnRentalField
from api.models import Rental


class StillOutFilter(admin.SimpleListFilter):
    """Open rentals are the ones with no return date, which a plain field filter can't name."""

    title = 'status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return [('out', 'Still out'), ('returned', 'Returned')]

    def queryset(self, request, queryset):
        if self.value() == 'out':
            return queryset.filter(returned_at__isnull=True)
        if self.value() == 'returned':
            return queryset.filter(returned_at__isnull=False)
        return queryset


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ['movie', 'copy', 'user', 'taken_at', 'returned_at', 'is_out']
    list_select_related = ['copy__movie', 'user']
    list_filter = [StillOutFilter, 'user', 'copy__movie__genre']
    search_fields = ['copy__movie__title', 'copy__label', 'user__username']
    # Copies are many and alike ("Die Hard, copy asdf-1234"), so the copy is picked from its own
    # list, where the shelf column shows which are free.
    raw_id_fields = ['copy']
    autocomplete_fields = ['user']
    # returned_at is shown by ReturnRentalField and never an input, so saving a form opened
    # before its Return button was clicked can't put an empty date back.
    fields = ['copy', 'user', 'taken_at', 'returned']
    readonly_fields = ['taken_at', 'returned']
    date_hierarchy = 'taken_at'
    actions = ['mark_returned']

    @admin.display(description='Returned')
    def returned(self, rental):
        if rental.pk is None:
            return 'Once the rental is saved.'
        return ReturnRentalField(rental=rental).render()

    @admin.display(description='Movie', ordering='copy__movie__title')
    def movie(self, rental):
        return rental.copy.movie.title

    @admin.display(description='Still out', boolean=True, ordering='returned_at')
    def is_out(self, rental):
        return rental.returned_at is None

    @admin.action(description='Mark the selected rentals returned')
    def mark_returned(self, request, queryset):
        # Only the open ones, so an old return date is never overwritten.
        returned = queryset.filter(returned_at__isnull=True).update(returned_at=timezone.now())
        self.message_user(request, f'Marked {returned} returned.')
