from website_widgets import SyncWidget

from api.models import Rental


class ReturnReceipt(SyncWidget):
    """The return receipt's own part: which movie went back on the shelf."""

    def __init__(self, username: str, rental: Rental):
        """`rental` with `copy.movie` loaded, since the template follows it."""
        super().__init__()
        self.username = username
        self.rental = rental

    def set_context(self):
        self.context.data['username'] = self.username
        self.context.data['rental'] = self.rental
