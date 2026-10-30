from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Exists, OuterRef
from django.utils import timezone

from api.models import Copy, Movie, Rental, User


class CopyInline(admin.TabularInline):
    """A movie's discs, on its page. A new row is a new disc on the shelf."""

    model = Copy
    extra = 0
    readonly_fields = ['added_at']
    # A copy's rentals are its history; deleting one from here would delete them too.
    can_delete = False
    show_change_link = True


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'year', 'genre', 'rating', 'total_copies', 'available_copies']
    list_filter = ['genre', 'rating']
    search_fields = ['title']
    inlines = [CopyInline]

    def get_queryset(self, request):
        # The same counts the site's movie cards show, so the columns sort in the database.
        return super().get_queryset(request).with_availability()

    @admin.display(description='Copies', ordering='total_copies')
    def total_copies(self, movie):
        return movie.total_copies

    @admin.display(description='On the shelf', ordering='available_copies')
    def available_copies(self, movie):
        return movie.available_copies


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
    search_fields = ['copy__movie__title', 'user__username']
    # Copies are many and alike ("Die Hard, copy 12"), so the copy is picked by id from its own
    # list, where the shelf column shows which are free.
    raw_id_fields = ['copy']
    autocomplete_fields = ['user']
    date_hierarchy = 'taken_at'
    actions = ['mark_returned']

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


admin.site.register(User, UserAdmin)
