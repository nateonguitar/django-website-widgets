from website_widgets import AsyncWidget

from api.models import Rental
from website.widgets.timestamp import Timestamp


class RentalRow(AsyncWidget):
    """One movie the signed-in user has out, with the button that returns it."""

    def __init__(
        self,
        rental: Rental,
        *,
        key: int
    ):
        super().__init__()
        # Tells this row's root from the others' on the page, for its controller's selector.
        self.context.data['key'] = key
        # Loaded with select_related('copy__movie') by the page.
        self.rental = rental

    async def set_context(self):
        self.context.data['rental'] = self.rental
        self.context.children['taken'] = Timestamp(value=self.rental.taken_at)
