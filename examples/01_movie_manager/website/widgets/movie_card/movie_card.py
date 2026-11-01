from website_widgets import AsyncWidget

from api.models import Movie


class MovieCard(AsyncWidget):
    """
    One movie and how many copies are on the shelf, its title linking to its own page. For the
    pages that list movies its button adds the movie to the cart; for the add-to-inventory page
    (`purpose='choose'`) it picks the movie to add copies of.
    """

    def __init__(
        self,
        movie: Movie,
        purpose: str = 'cart',
        note: str | None = None,
        *,
        key: int
    ):
        super().__init__()
        # Tells this card's root from the others' on the page, for its controller's selector.
        self.context.data['key'] = key
        # From Movie.objects.with_availability(), for total_copies and available_copies.
        self.movie = movie
        self.purpose = purpose
        # A line about why it's listed, such as the home page's "1 new copy, 2 weeks ago".
        self.note = note

    async def set_context(self):
        self.context.data['movie'] = self.movie
        self.context.data['purpose'] = self.purpose
        self.context.data['note'] = self.note
