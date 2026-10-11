from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from website_widgets.tests.sample_widgets import (
    AsyncChildParentWidget,
    AsyncContextWidget,
    DefaultTemplateWidget,
    ParentWidget,
    RequestReadingWidget,
    SyncContextWidget,
)
from website_widgets.tests.widget_test_case import WidgetTestCase


class ARenderTestCase(WidgetTestCase):
    async def test_arender__runs_set_context__when_set_context_is_sync(self):
        widget = SyncContextWidget()
        widget.template_filename = self.write_template('{{ data.word }}')

        self.assertEqual(await widget.arender(), 'sync')

    async def test_arender__runs_set_context__when_set_context_is_async(self):
        widget = AsyncContextWidget()
        widget.template_filename = self.write_template('{{ data.word }}')

        self.assertEqual(await widget.arender(), 'async')

    async def test_arender__renders_async_child__when_parent_is_sync(self):
        widget = AsyncChildParentWidget(self.write_template('{{ data.word }}'))
        widget.template_filename = self.write_template('{{ children.child }}')

        self.assertEqual(await widget.arender(), 'async')

    async def test_arender__renders_children__when_nested_and_listed(self):
        widget = ParentWidget(self.write_template('{{ data.word }}'))
        widget.template_filename = self.write_template(
            '{{ children.single }}|{% for child in children.many %}{{ child }},{% endfor %}|'
            '{{ children.absent|default_if_none:"none" }}')

        self.assertEqual(await widget.arender(), 'one|two,three,|none')

    async def test_arender__renders_with_given_request__when_called(self):
        request = RequestFactory().get('/somewhere/')
        request.user = AnonymousUser()
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ request.path }}')

        self.assertEqual(await widget.arender(request), '/somewhere/')

    async def test_arender__fails__when_no_request_given_and_widget_reads_request(self):
        widget = RequestReadingWidget()
        widget.template_filename = self.write_template('{{ data.path }}')

        with self.assertRaises(RuntimeError):
            await widget.arender()

    async def test_arender__fails__when_already_rendered(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('once')
        await widget.arender()

        with self.assertRaises(RuntimeError):
            await widget.arender()

    async def test_arender__test__renders_as_user__when_user_given(self):
        user = SimpleNamespace(is_authenticated=True, username='riley')
        widget = AsyncContextWidget()
        widget.template_filename = self.write_template('{{ user.username }} {{ data.word }}')

        self.assertEqual(await widget.arender__test(user=user), 'riley async')
