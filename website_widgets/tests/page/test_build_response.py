from django.test import RequestFactory

from website_widgets.tests.sample_widgets import AsyncContextWidget, DocumentPage, HolderWidget, SyncDocumentPage, WordWidget
from website_widgets.tests.widget_test_case import WidgetTestCase


class BuildResponseTestCase(WidgetTestCase):
    def make_request(self):
        request_factory = RequestFactory()
        return request_factory.get('/')

    async def test_build_response__returns_document_with_status__when_async_page_handles_request(self):
        document_template_filename = self.write_template('<body>{{ page_content_html }}</body>')
        template_filename = self.write_template('{{ data.word }} {{ children.child }}')
        child_template_filename = self.write_template('{{ data.word }}')
        page = DocumentPage(
            document_template_filename=document_template_filename,
            template_filename=template_filename,
            child_template_filename=child_template_filename)
        page.status_code = 404
        request = self.make_request()
        page._request = request

        response = await page.handle_request(request)

        html = response.content.decode()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(html, '<body>async child</body>')

    def test_build_response__returns_document_without_an_event_loop__when_sync_page_handles_request(self):
        document_template_filename = self.write_template('<body>{{ page_content_html }}</body>')
        template_filename = self.write_template('{{ data.word }} {{ children.child }}')
        child_template_filename = self.write_template('{{ data.word }}')
        child_widget = WordWidget('child', child_template_filename)
        view = SyncDocumentPage.as_view(
            document_template_filename=document_template_filename,
            template_filename=template_filename,
            child=child_widget)
        request = self.make_request()

        response = view(request)

        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(html, '<body>sync child</body>')

    def test_build_response__fails__when_sync_page_holds_async_widget(self):
        child_widget = AsyncContextWidget()
        child_widget.template_filename = self.write_template('{{ data.word }}')
        document_template_filename = self.write_template('{{ page_content_html }}')
        template_filename = self.write_template('{{ children.child }}')
        page = SyncDocumentPage(
            document_template_filename=document_template_filename,
            template_filename=template_filename,
            child=child_widget)
        request = self.make_request()
        page._request = request

        with self.assertRaisesMessage(TypeError, 'AsyncContextWidget.set_context() is async'):
            page.handle_request(request)

    def test_build_response__fails__when_sync_page_holds_async_widget_as_grandchild(self):
        async_template = self.write_template('{{ data.word }}')

        def place_async_grandchild(children):
            grandchild_widget = AsyncContextWidget()
            grandchild_widget.template_filename = async_template
            children['grandchild'] = grandchild_widget

        child_widget = HolderWidget(place_async_grandchild)
        child_widget.template_filename = self.write_template('{{ children.grandchild }}')
        document_template_filename = self.write_template('{{ page_content_html }}')
        template_filename = self.write_template('{{ children.child }}')
        page = SyncDocumentPage(
            document_template_filename=document_template_filename,
            template_filename=template_filename,
            child=child_widget)
        request = self.make_request()
        page._request = request

        with self.assertRaisesMessage(TypeError, 'AsyncContextWidget.set_context() is async'):
            page.handle_request(request)
