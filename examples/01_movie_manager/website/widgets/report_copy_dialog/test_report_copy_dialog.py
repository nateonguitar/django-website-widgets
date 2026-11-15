from bs4 import BeautifulSoup

from api.models import CopyReport, CopyReportKind
from website.tests.app_widget_test_case import AppWidgetTestCase
from website.widgets.report_copy_dialog import ReportCopyDialog


class ReportCopyDialogTestCase(AppWidgetTestCase):
    async def test_report_copy_dialog__offers_every_kind_and_the_notes_limit__when_rendered(self):
        report_copy_dialog = ReportCopyDialog()
        html = await self.arender_document(report_copy_dialog)
        soup = BeautifulSoup(html, 'html.parser')
        dialog_template = soup.select_one('template#report-copy-dialog-template')
        kinds = [
            radio['value']
            for radio in dialog_template.select('input[type="radio"][name="kind"]')
        ]
        expected_kinds = list(CopyReportKind.values)
        self.assertEqual(kinds, expected_kinds)
        notes_textarea = dialog_template.select_one('textarea[name="notes"]')
        expected_max_length = str(CopyReport.NOTES_MAX_LENGTH)
        self.assertEqual(notes_textarea['maxlength'], expected_max_length)
        # Beside the confirm dialog's <template>, which the document holds as every page does.
        confirm_dialog_template = soup.select_one('template#confirm-dialog-template')
        self.assertIsNotNone(confirm_dialog_template)
