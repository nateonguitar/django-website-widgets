from website_widgets import SyncWidget

from api.models import Rental
from website.widgets.timestamp import Timestamp, TimestampStyle


class HistoryRow(SyncWidget):
    """One movie the signed-in user took, on My history: when, when it came back, and for how long."""

    def __init__(self, rental: Rental):
        """`rental` with `copy.movie` loaded, since the template follows it."""
        super().__init__()
        self.rental = rental

    def set_context(self):
        rental = self.rental
        self.context.data['rental'] = rental
        self.context.children['taken'] = Timestamp(value=rental.taken_at)
        if rental.returned_at:
            self.context.children['returned'] = Timestamp(value=rental.returned_at)
        else:
            # How long it's been out so far, the "for" of a movie still at home.
            self.context.children['out_for'] = Timestamp(value=rental.taken_at, style=TimestampStyle.DURATION)
