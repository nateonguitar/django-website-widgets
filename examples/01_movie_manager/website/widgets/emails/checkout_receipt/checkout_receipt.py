from website_widgets import SyncWidget

from api.models import Rental


class CheckoutReceipt(SyncWidget):
    """The checkout receipt's own part: what someone just took home, and where to bring it back."""

    def __init__(self, username: str, rentals: list[Rental]):
        """`rentals` each with `copy.movie` loaded, since the template follows it."""
        super().__init__()
        self.username = username
        self.rentals = rentals

    def set_context(self):
        self.context.data['username'] = self.username
        self.context.data['rentals'] = self.rentals
