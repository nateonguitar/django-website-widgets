from website_widgets import Widget

from api.models import Rental
from website.widgets.timestamp import Timestamp, TimestampStyle


class WhoHasWhatRow(Widget):
    """One movie that's out, on the Who has what page: the movie, who has it, and for how long."""

    def __init__(self, rental: Rental, viewer_id: int):
        """`rental` with `copy.movie` and `user` loaded, since the template follows both."""
        super().__init__()
        self.rental = rental
        self.viewer_id = viewer_id

    def set_context(self):
        self.context.data['rental'] = self.rental
        self.context.data['is_viewers'] = self.rental.user_id == self.viewer_id
        self.context.children['out_for'] = Timestamp(value=self.rental.taken_at, style=TimestampStyle.DURATION)
