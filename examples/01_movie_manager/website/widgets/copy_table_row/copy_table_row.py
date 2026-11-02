from website_widgets import SyncWidget

from api.models import Copy
from website.widgets.timestamp import Timestamp, TimestampStyle


class CopyTableRow(SyncWidget):
    """One copy in a CopyTable: its label, when it arrived, and where it is."""

    def __init__(self, copy: Copy, show_who: bool, viewer_id: int | None):
        super().__init__()
        self.copy = copy
        self.show_who = show_who
        self.viewer_id = viewer_id

    def set_context(self):
        # At most one open rental per copy, prefetched by the caller.
        rental = self.copy.open_rentals[0] if self.copy.open_rentals else None
        self.context.data['label'] = self.copy.label
        self.context.data['retired'] = self.copy.retired_at is not None
        self.context.data['rental'] = rental
        self.context.data['show_who'] = self.show_who
        self.context.data['is_viewers'] = rental is not None and rental.user_id == self.viewer_id
        self.context.children['arrived'] = Timestamp(value=self.copy.added_at)
        if rental is not None:
            self.context.children['out_for'] = Timestamp(value=rental.taken_at, style=TimestampStyle.DURATION)
