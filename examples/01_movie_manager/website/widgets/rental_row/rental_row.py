from website_widgets import Widget

from api.models import Rental


class RentalRow(Widget):
    """One movie the signed-in user has out, with the button that returns it."""

    def __init__(self, rental: Rental):
        super().__init__()
        # Loaded with select_related('copy__movie') by the page.
        self.rental = rental

    async def set_context(self):
        self.context.data['rental'] = self.rental
