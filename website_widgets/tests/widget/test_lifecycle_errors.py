from django.test import RequestFactory

from website_widgets.tests.sample_widgets import (
    DefaultTemplateWidget,
    DocumentPage,
    EarlyPageWritingWidget,
    HolderWidget,
    PageValueWidget,
    PageWritingPage,
    RequestInConstructorPage,
    RequestInConstructorWidget,
)
from website_widgets.tests.widget_test_case import WidgetTestCase


class LifecycleErrorsTestCase(WidgetTestCase):
    def make_page(self) -> DocumentPage:
        return DocumentPage(
            document_template_filename='unused.html',
            template_filename='unused.html',
            child_template_filename='unused.html')

    def holder(self, fill) -> HolderWidget:
        widget = HolderWidget(fill)
        widget.template_filename = self.write_template('')
        return widget

    def test_render__fails_naming_the_key__when_page_assigned_as_child(self):
        def assign(children):
            children['header'] = self.make_page()

        with self.assertRaisesMessage(TypeError, "DocumentPage is a page in HolderWidget.context.children['header']"):
            self.holder(assign).render()

    def test_render__fails_naming_the_key__when_page_in_child_list(self):
        def assign_list(children):
            children['cards'] = [DefaultTemplateWidget(), self.make_page()]

        with self.assertRaisesMessage(TypeError, "context.children['cards']: a page is only ever the root"):
            self.holder(assign_list).render()

    def test_render__fails_naming_the_key__when_page_added_with_update(self):
        def update(children):
            children.update(sidebar=self.make_page())

        with self.assertRaisesMessage(TypeError, "context.children['sidebar']"):
            self.holder(update).render()

    async def test_arender__fails_naming_the_key__when_page_appended_to_list_after_assignment(self):
        def append_later(children):
            cards = []
            children['cards'] = cards
            cards.append(self.make_page())

        with self.assertRaisesMessage(TypeError, "context.children['cards']"):
            await self.holder(append_later).arender()

    def test_request__says_to_read_it_in_set_context__when_read_in_widget_constructor(self):
        with self.assertRaisesMessage(RuntimeError, "RequestInConstructorWidget.request isn't set until rendering starts, so it can't be read in __init__(); read it in set_context()"):
            RequestInConstructorWidget()

    def test_request__says_to_read_it_in_set_context__when_read_in_page_constructor(self):
        with self.assertRaisesMessage(RuntimeError, "RequestInConstructorPage.request isn't set until rendering starts"):
            RequestInConstructorPage()

    def test_render__fails_naming_lost_keys__when_child_wrote_context_page_in_constructor(self):
        def assign(children):
            children['card'] = EarlyPageWritingWidget()

        with self.assertRaisesMessage(RuntimeError, "EarlyPageWritingWidget.context.page was written before HolderWidget rendered it, so its keys ['early'] would be lost"):
            self.holder(assign).render()

    async def test_arender__fails__when_child_in_list_wrote_context_page_in_constructor(self):
        def assign_list(children):
            children['cards'] = [EarlyPageWritingWidget()]

        with self.assertRaisesMessage(RuntimeError, "keys ['early'] would be lost"):
            await self.holder(assign_list).arender()

    def test_render__shares_value_with_page_and_siblings__when_child_writes_context_page_in_set_context(self):
        page_value_template = self.write_template('{{ page.shared }}')
        reader_template = self.write_template('{{ page.shared }}')

        def assign(children):
            children['writer'] = PageValueWidget('shared', 'yes', page_value_template)
            reader = DefaultTemplateWidget()
            reader.template_filename = reader_template
            children['reader'] = reader

        widget = HolderWidget(assign)
        widget.template_filename = self.write_template('{{ children.writer }} {{ children.reader }} {{ page.shared }}')

        self.assertEqual(widget.render(), 'yes yes yes')

    def test_render__keeps_context_page__when_root_widget_given_one_before_render(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ page.foo }}')
        widget.context.page['foo'] = 'bar'

        self.assertEqual(widget.render(), 'bar')

    async def test_handle_request__renders_every_page_value__when_page_writes_context_page_before_and_in_set_context(self):
        page = PageWritingPage(
            document_template_filename=self.write_template('{{ page.user }}|{{ page_content_html }}'),
            template_filename=self.write_template('{{ page.title }}:{{ children.child }}'),
            child_template_filename=self.write_template('{{ page.user }}/{{ page.title }}'))
        request = RequestFactory().get('/')
        page._request = request

        response = await page.handle_request(request)

        self.assertEqual(response.content.decode(), 'ann|Home:ann/Home')
