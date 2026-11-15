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

        html = widget.render()

        self.assertEqual(html, 'sync')

    def test_render__renders_chosen_template__when_template_filename_set(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('chosen {{ data.word }}')
        widget.context.data['word'] = 'template'

        html = widget.render()

        self.assertEqual(html, 'chosen template')

    def test_render__renders_children__when_nested_and_listed(self):
        child_template_filename = self.write_template('{{ data.word }}')
        widget = ParentWidget(child_template_filename)
        widget.template_filename = self.write_template(
            '{{ children.single }}|{% for child in children.many %}{{ child }},{% endfor %}|'
            '{{ children.absent|default_if_none:"none" }}')

        html = widget.render()

        self.assertEqual(html, 'one|two,three,|none')

    def test_render__shares_page_context_with_children__when_set_before_rendering(self):
        child_template_filename = self.write_template('{{ page.foo }}')
        widget = ParentWidget(child_template_filename)
        widget.template_filename = self.write_template('{{ children.single }}')
        widget.context.page['foo'] = 'abc'

        html = widget.render()

        self.assertEqual(html, 'abc')

    def test_render__runs_set_context_without_event_loop__when_called_from_sync_code(self):
        widget = LoopCheckingWidget()
        widget.template_filename = self.write_template('{{ data.loop }}')

        html = widget.render()

        self.assertEqual(html, 'none')

    def test_render__fails_naming_widget__when_set_context_is_async(self):
        widget = AsyncContextWidget()
        widget.template_filename = self.write_template('{{ data.word }}')

        with self.assertRaisesMessage(TypeError, 'AsyncContextWidget'):
            widget.render()

    def test_render__fails_naming_widget__when_child_set_context_is_async(self):
        child_template_filename = self.write_template('{{ data.word }}')
        widget = AsyncChildParentWidget(child_template_filename)
        widget.template_filename = self.write_template('{{ children.child }}')

        with self.assertRaisesMessage(TypeError, 'AsyncContextWidget'):
            widget.render()

    def test_render__renders_with_given_request__when_called(self):
        request_factory = RequestFactory()
        request = request_factory.get('/somewhere/')
        request.user = AnonymousUser()
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ request.path }}')

        html = widget.render(request)

        self.assertEqual(html, '/somewhere/')

    def test_render__renders__when_no_request_given_and_widget_needs_none(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ request|default_if_none:"none" }}')

        html = widget.render()

        self.assertEqual(html, 'none')

    def test_render__fails__when_no_request_given_and_widget_reads_request(self):
        widget = RequestReadingWidget()
        widget.template_filename = self.write_template('{{ data.path }}')

        with self.assertRaises(RuntimeError):
            widget.render()

    def test_render__drops_into_django_template_unescaped__when_output_is_in_its_context(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('<b>{{ data.word }}</b>')
        widget.context.data['word'] = '<i>'
        widget_html = widget.render()
        django_template = Template('<div>{{ widget_html }}</div>')
        django_context = Context({'widget_html': widget_html})

        html = django_template.render(django_context)

        self.assertEqual(html, '<div><b>&lt;i&gt;</b></div>')

    def test_render__fails__when_already_rendered(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('once')
        widget.render()

        with self.assertRaises(RuntimeError):
            widget.render()

    def test_render__test__renders_as_anonymous__when_no_user_given(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ request.user.is_authenticated }}')

        html = widget.render__test()

        self.assertEqual(html, 'False')

    def test_render__test__renders_as_user__when_user_given(self):
        user = SimpleNamespace(is_authenticated=True, username='riley')
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ request.user.username }}')

        html = widget.render__test(user=user)

        self.assertEqual(html, 'riley')
