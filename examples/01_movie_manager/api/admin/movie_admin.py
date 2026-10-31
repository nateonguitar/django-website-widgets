from django import forms
from django.contrib import admin
from django.db.models import Prefetch

from api.models import Copy, Movie, Rental
from website.widgets.copy_table import CopyTable
from website.widgets.rating_picker import RatingSelect


class CopyInline(admin.TabularInline):
    """A movie's discs, on its page. A new row is a new disc on the shelf."""

    model = Copy
    extra = 0
    readonly_fields = ['added_at']
    # A copy's rentals are its history; deleting one from here would delete them too.
    can_delete = False
    show_change_link = True


class MovieAdminForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = '__all__'
        # The site's own RatingPicker, which says what the chosen rating means.
        widgets = {'rating': RatingSelect()}


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    form = MovieAdminForm
    list_display = ['title', 'year', 'genre', 'rating', 'total_copies', 'available_copies']
    list_filter = ['genre', 'rating']
    search_fields = ['title']
    readonly_fields = ['where_each_copy_is']
    inlines = [CopyInline]

    @admin.display(description='Where each copy is')
    def where_each_copy_is(self, movie):
        if movie.pk is None:
            return 'Once the movie is saved.'
        # The movie page's own widget. The admin is sync, so the sync ORM loads its copies here,
        # and render() runs its sync set_context(); it needs no request.
        open_rentals = Rental.objects.filter(returned_at__isnull=True).select_related('user')
        copies = (
            movie.copies
            .order_by('added_at', 'id')
            .prefetch_related(Prefetch('rentals', queryset=open_rentals, to_attr='open_rentals'))
        )
        table = CopyTable(copies=list(copies), show_who=True)
        return table.render()

    def get_queryset(self, request):
        # The same counts the site's movie cards show, so the columns sort in the database.
        return super().get_queryset(request).with_availability()

    @admin.display(description='Copies', ordering='total_copies')
    def total_copies(self, movie):
        return movie.total_copies

    @admin.display(description='On the shelf', ordering='available_copies')
    def available_copies(self, movie):
        return movie.available_copies
