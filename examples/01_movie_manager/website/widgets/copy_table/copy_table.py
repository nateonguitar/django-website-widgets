from website_widgets import SyncWidget

from api.models import Copy
from website.widgets.copy_table_row import CopyTableRow


class CopyTable(SyncWidget):
    """
    Each copy of a movie, when it arrived and where it is. Rendered by MoviePage, and by the
    Movie admin's change page with render(), so its copies come in through the constructor: each
    caller queries them its own way, the page with the async ORM and the admin with the sync one.
    """

    def __init__(self, copies: list[Copy], show_who: bool, viewer_id: int | None = None):
        """
        `copies` each carry `open_rentals`, prefetched with the user. `show_who` names who has a
        copy, and `viewer_id` says "you" for the viewer's own.
        """
        super().__init__()
        self.copies = copies
        self.show_who = show_who
        self.viewer_id = viewer_id

    def set_context(self):
        self.context.children['rows'] = [
            CopyTableRow(copy=copy, show_who=self.show_who, viewer_id=self.viewer_id)
            for copy in self.copies
        ]
