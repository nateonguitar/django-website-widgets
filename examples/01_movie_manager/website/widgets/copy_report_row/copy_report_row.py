from website_widgets import SyncWidget

from api.models import CopyReport
from website.widgets.timestamp import Timestamp, TimestampStyle


class CopyReportRow(SyncWidget):
    """One report in a copy's history: what was wrong, who said so, when, and the notes."""

    def __init__(self, report: CopyReport):
        """`report` with its `user` loaded, since the template names them."""
        super().__init__()
        self.report = report

    def set_context(self):
        self.context.data['report'] = self.report
        self.context.children['reported'] = Timestamp(value=self.report.reported_at, style=TimestampStyle.AGO)
