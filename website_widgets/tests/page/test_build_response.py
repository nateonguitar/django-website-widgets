from django.test import RequestFactory

from website_widgets.tests.sample_widgets import AsyncContextWidget, DocumentPage, HolderWidget, SyncDocumentPage, WordWidget
from website_widgets.tests.widget_test_case import WidgetTestCase


class BuildResponseTestCase(WidgetTestCase):
    async def test_build_response__returns_document_with_status__when_async_page_handles_request(self):
        page = DocumentPage(
            document_template_filename=self.write_template('<body>{{ page_content_html }}</body>'),
            template_filename=self.write_template('{{ data.word }} {{ children.child }}'),
            child_template_filename=self.write_template('{{ data.word }}'))
        page.status_code = 404
        request = RequestFactory().get('/')
        page._request = request

        response = await page.handle_request(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode(), '<body>async child</body>')

    def test_build_response__returns_document_without_an_event_loop__when_sync_page_handles_request(self):
        page = SyncDocumentPage(
            document_template_filename=self.write_template('<body>{{ page_content_html }}</body>'),
            template_filename=self.write_template('{{ data.word }} {{ children.child }}'),
            child=WordWidget('child', self.write_template('{{ data.word }}')))
        request = RequestFactory().get('/')

        response = SyncDocumentPage.as_view(
            document_template_filename=page.document_template_path,
            template_filename=page.template_filename,
            child=page.child)(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), '<body>sync child</body>')

    def test_build_response__fails__when_sync_page_holds_async_widget(self):
        child = AsyncContextWidget()
        child.template_filename = self.write_template('{{ data.word }}')
        page = SyncDocumentPage(
            document_template_filename=self.write_template('{{ page_content_html }}'),
            template_filename=self.write_template('{{ children.child }}'),
            child=child)
        request = RequestFactory().get('/')
        page._request = request

        with self.assertRaisesMessage(TypeError, 'AsyncContextWidget.set_context() is async'):
            page.handle_request(request)

    def test_build_response__fails__when_sync_page_holds_async_widget_as_grandchild(self):
        async_template = self.write_template('{{ data.word }}')

        def place_async_grandchild(children):
            grandchild = AsyncContextWidget()
            grandchild.template_filename = async_template
            children['grandchild'] = grandchild

        child = HolderWidget(place_async_grandchild)
        child.template_filename = self.write_template('{{ children.grandchild }}')
        page = SyncDocumentPage(
            document_template_filename=self.write_template('{{ page_content_html }}'),
            template_filename=self.write_template('{{ children.child }}'),
            child=child)
        request = RequestFactory().get('/')
        page._request = request

        with self.assertRaisesMessage(TypeError, 'AsyncContextWidget.set_context() is async'):
            page.handle_request(request)
