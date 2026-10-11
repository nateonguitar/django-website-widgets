from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.test import RequestFactory

from website_widgets.tests.sample_widgets import (
    AsyncChildParentWidget,
    AsyncContextWidget,
    DefaultTemplateWidget,
    LoopCheckingWidget,
    ParentWidget,
    RequestReadingWidget,
    SyncContextWidget,
)
from website_widgets.tests.widget_test_case import WidgetTestCase


class RenderTestCase(WidgetTestCase):
    def test_render__runs_set_context__when_set_context_is_sync(self):
        widget = SyncContextWidget()
        widget.template_filename = self.write_template('{{ data.word }}')

        self.assertEqual(widget.render(), 'sync')

    def test_render__renders_chosen_template__when_template_filename_set(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('chosen {{ data.word }}')
        widget.context.data['word'] = 'template'

        self.assertEqual(widget.render(), 'chosen template')

    def test_render__renders_children__when_nested_and_listed(self):
        widget = ParentWidget(self.write_template('{{ data.word }}'))
        widget.template_filename = self.write_template(
            '{{ children.single }}|{% for child in children.many %}{{ child }},{% endfor %}|'
            '{{ children.absent|default_if_none:"none" }}')

        self.assertEqual(widget.render(), 'one|two,three,|none')

    def test_render__shares_page_context_with_children__when_set_before_rendering(self):
        widget = ParentWidget(self.write_template('{{ page.foo }}'))
        widget.template_filename = self.write_template('{{ children.single }}')
        widget.context.page['foo'] = 'abc'

        self.assertEqual(widget.render(), 'abc')

    def test_render__runs_set_context_without_event_loop__when_called_from_sync_code(self):
        widget = LoopCheckingWidget()
        widget.template_filename = self.write_template('{{ data.loop }}')

        self.assertEqual(widget.render(), 'none')

    def test_render__fails_naming_widget__when_set_context_is_async(self):
        widget = AsyncContextWidget()
        widget.template_filename = self.write_template('{{ data.word }}')

        with self.assertRaisesMessage(TypeError, 'AsyncContextWidget'):
            widget.render()

    def test_render__fails_naming_widget__when_child_set_context_is_async(self):
        widget = AsyncChildParentWidget(self.write_template('{{ data.word }}'))
        widget.template_filename = self.write_template('{{ children.child }}')

        with self.assertRaisesMessage(TypeError, 'AsyncContextWidget'):
            widget.render()

    def test_render__renders_with_given_request__when_called(self):
        request = RequestFactory().get('/somewhere/')
        request.user = AnonymousUser()
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ request.path }}')

        self.assertEqual(widget.render(request), '/somewhere/')

    def test_render__renders__when_no_request_given_and_widget_needs_none(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template(
            '{{ request|default_if_none:"none" }} {{ user|default_if_none:"none" }}')

        self.assertEqual(widget.render(), 'none none')

    def test_render__fails__when_no_request_given_and_widget_reads_request(self):
        widget = RequestReadingWidget()
        widget.template_filename = self.write_template('{{ data.path }}')

        with self.assertRaises(RuntimeError):
            widget.render()

    def test_render__drops_into_django_template_unescaped__when_output_is_in_its_context(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('<b>{{ data.word }}</b>')
        widget.context.data['word'] = '<i>'

        html = Template('<div>{{ widget_html }}</div>').render(Context({'widget_html': widget.render()}))

        self.assertEqual(html, '<div><b>&lt;i&gt;</b></div>')

    def test_render__fails__when_already_rendered(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('once')
        widget.render()

        with self.assertRaises(RuntimeError):
            widget.render()

    def test_render__test__renders_as_anonymous__when_no_user_given(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ user.is_authenticated }}')

        self.assertEqual(widget.render__test(), 'False')

    def test_render__test__renders_as_user__when_user_given(self):
        user = SimpleNamespace(is_authenticated=True, username='riley')
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ user.username }}')

        self.assertEqual(widget.render__test(user=user), 'riley')
