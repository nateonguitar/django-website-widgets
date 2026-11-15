from types import SimpleNamespace

from django.test import SimpleTestCase

from website_widgets.testing import WidgetDocumentTestMixin
from website_widgets.tests.sample_widgets import (
    AsyncStringWidget,
    PageReadingWidget,
    StringTemplateWidget,
    UserReadingWidget,
)


class AppBarWidget(StringTemplateWidget):
    template_string = '<nav>appbar</nav>'


class FooterWidget(StringTemplateWidget):
    template_string = '<footer>footer</footer>'


class ChromeDocumentMixin(WidgetDocumentTestMixin):
    """A project's own document, as a subclass would write it: chrome around the widget, and page values."""

    document_template = '<main>{{ children.appbar }}{{ children.widget }}</main>'

    def document_children(self) -> dict:
        return {'appbar': AppBarWidget()}

    def page_context(self, user) -> dict:
        return {'word': 'hook'}


class WidgetDocumentTestMixinTestCase(SimpleTestCase):
    def test_render_document__wraps_widget_in_default_document__when_not_overridden(self):
        mixin = WidgetDocumentTestMixin()
        widget = StringTemplateWidget()

        html = mixin.render_document(widget)

        starts_with_doctype = html.startswith('<!DOCTYPE html>')
        self.assertTrue(starts_with_doctype)
        self.assertIn('<meta charset="utf-8">', html)
        self.assertIn('<body>\nstring template\n</body>', html)

    def test_render_document__uses_subclass_document_and_children__when_overridden(self):
        mixin = ChromeDocumentMixin()
        widget = StringTemplateWidget()

        html = mixin.render_document(widget)

        self.assertEqual(html, '<main><nav>appbar</nav>string template</main>')

    def test_render_document__merges_call_children_over_hook__when_both_given(self):
        mixin = ChromeDocumentMixin()
        mixin.document_template = '{{ children.appbar }}|{{ children.footer }}|{{ children.widget }}'
        widget = StringTemplateWidget()
        footer_widget = FooterWidget()

        html = mixin.render_document(widget, document_children={'appbar': None, 'footer': footer_widget})

        self.assertEqual(html, 'None|<footer>footer</footer>|string template')

    def test_render_document__fails__when_a_document_child_is_named_widget(self):
        mixin = WidgetDocumentTestMixin()
        widget = StringTemplateWidget()
        footer_widget = FooterWidget()

        with self.assertRaises(ValueError):
            mixin.render_document(widget, document_children={'widget': footer_widget})

    def test_render_document__gives_page_context_to_every_descendant__when_set_by_hook(self):
        mixin = ChromeDocumentMixin()
        mixin.document_template = '{{ children.widget }}'
        widget = PageReadingWidget()

        html = mixin.render_document(widget)

        self.assertEqual(html, 'hook[inner hook]')

    def test_render_document__merges_call_page_context_over_hook__when_both_given(self):
        mixin = ChromeDocumentMixin()
        mixin.document_template = '{{ children.widget }}'
        widget = PageReadingWidget()

        html = mixin.render_document(widget, page_context={'word': 'call'})

        self.assertEqual(html, 'call[inner call]')

    def test_render_document__leaves_hook_dicts_unchanged__when_call_merges_over_them(self):
        shared_page = {'word': 'shared'}

        class SharedHookMixin(WidgetDocumentTestMixin):
            def page_context(self, user) -> dict:
                return shared_page

        mixin = SharedHookMixin()
        widget = PageReadingWidget()

        mixin.render_document(widget, page_context={'word': 'call'})

        self.assertEqual(shared_page, {'word': 'shared'})

    def test_render_document__sets_request_user__when_user_given(self):
        mixin = WidgetDocumentTestMixin()
        mixin.document_template = '{{ children.widget }}'
        widget = UserReadingWidget()
        user = SimpleNamespace(username='ann')

        html = mixin.render_document(widget, user=user)

        self.assertEqual(html, 'ann')

    def test_render_document__hands_user_to_page_context_hook__when_user_given(self):
        class UserPageMixin(WidgetDocumentTestMixin):
            document_template = '{{ children.widget }}'

            def page_context(self, user) -> dict:
                return {'word': user.username}

        mixin = UserPageMixin()
        widget = PageReadingWidget()
        user = SimpleNamespace(username='ann')

        html = mixin.render_document(widget, user=user)

        self.assertEqual(html, 'ann[inner ann]')

    def test_render_document__fails__when_widget_wrote_its_own_page_context(self):
        mixin = WidgetDocumentTestMixin()
        widget = PageReadingWidget()
        widget.context.page['word'] = 'early'

        with self.assertRaises(RuntimeError):
            mixin.render_document(widget)

    def test_render_document__fails__when_widget_is_async(self):
        mixin = WidgetDocumentTestMixin()
        widget = AsyncStringWidget()

        with self.assertRaises(TypeError):
            mixin.render_document(widget)

    async def test_arender_document__renders_async_widget__when_awaited(self):
        mixin = ChromeDocumentMixin()
        widget = AsyncStringWidget()

        html = await mixin.arender_document(widget)

        self.assertEqual(html, '<main><nav>appbar</nav>async widget</main>')

    async def test_arender_document__renders_sync_widget__when_awaited(self):
        mixin = WidgetDocumentTestMixin()
        mixin.document_template = '{{ children.widget }}'
        widget = StringTemplateWidget()

        html = await mixin.arender_document(widget)

        self.assertEqual(html, 'string template')
