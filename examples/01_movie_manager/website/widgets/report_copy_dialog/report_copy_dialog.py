from website_widgets import SyncWidget

from api.models import CopyReport, CopyReportKind


class ReportCopyDialog(SyncWidget):
    """
    The <template> of the form that reports a problem with a copy, placed on the copy page for
    ReportCopyDialogController.show() to copy into a dialog.
    """

    def set_context(self):
        self.context.data['kinds'] = CopyReportKind.choices
        self.context.data['notes_max_length'] = CopyReport.NOTES_MAX_LENGTH
