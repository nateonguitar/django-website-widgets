from website_widgets import Widget

from api.models import Movie


class MovieCard(Widget):
    """
    One movie and how many copies are on the shelf, its title linking to its own page. For the
    pages that list movies its button adds the movie to the cart; for the add-to-inventory page
    (`purpose='choose'`) it picks the movie to add copies of.
    """

    def __init__(
        self,
        movie: Movie,
        purpose: str = 'cart',
        note: str | None = None
    ):
        super().__init__()
        # From Movie.objects.with_availability(), for total_copies and available_copies.
        self.movie = movie
        self.purpose = purpose
        # A line about why it's listed, such as the home page's "1 new copy, 2 weeks ago".
        self.note = note

    async def set_context(self):
        self.context.data['movie'] = self.movie
        self.context.data['purpose'] = self.purpose
        self.context.data['note'] = self.note
