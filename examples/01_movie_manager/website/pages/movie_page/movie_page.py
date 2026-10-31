from django.db.models import Prefetch
from website_widgets import register_url

from api.models import Copy, Movie, Rental
from website.exceptions import NotFoundException
from website.pages.app_page import AppPage
from website.widgets.copy_table import CopyTable
from website.widgets.movie_card import MovieCard


@register_url('movies/<int:movie_id>')
class MoviePage(AppPage):
    """One movie: its card, and each copy with when it arrived and whether it's on the shelf."""

    def __init__(self, movie_id: int):
        super().__init__()
        # The route's <int:movie_id>, which WebPage.as_view() passes to the constructor.
        self.movie_id = movie_id

    async def set_context(self):
        movie = await Movie.objects.with_availability().filter(id=self.movie_id).afirst()
        if movie is None:
            # AppPage answers 404 with app_page__not_found.html, inside the site's own pages.
            raise NotFoundException('No movie has that number. It may have been taken off the shelf.')
        self.page_title = movie.title

        # Each copy with its open rental, if any, and who has it: the table reads both, and
        # following them there would run a sync query inside the async page.
        copies = (
            Copy.objects
            .filter(movie=movie)
            .order_by('added_at', 'id')
            .prefetch_related(Prefetch(
                'rentals',
                queryset=Rental.objects.filter(returned_at__isnull=True).select_related('user'),
                to_attr='open_rentals'))
        )
        copies = [copy async for copy in copies]
        user = self.context.page['user']
        self.context.children['card'] = MovieCard(movie=movie)
        # Names are for the family, so only someone signed in sees who has a copy.
        self.context.children['copies'] = CopyTable(
            copies=copies,
            show_who=user.is_authenticated,
            viewer_id=user.id)
