from django.test import RequestFactory

from website_widgets.tests.sample_widgets import DocumentPage
from website_widgets.tests.widget_test_case import WidgetTestCase


class BuildResponseTestCase(WidgetTestCase):
    async def test_build_response__returns_document_with_status__when_page_handles_request(self):
        page = DocumentPage(
            document_template_filename=self.write_template('<body>{{ page_content_html }}</body>'),
            template_filename=self.write_template('{{ data.word }} {{ children.child }}'),
            child_template_filename=self.write_template('{{ data.word }}'))
        page.status_code = 404
        request = RequestFactory().get('/')
        page._request = request

        response = await page.handle_request(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode(), '<body>sync child</body>')
