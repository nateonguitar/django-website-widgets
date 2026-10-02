import os
import tempfile

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase

from website_widgets.page import Page
from website_widgets.widget import Widget


TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


class DefaultTemplateWidget(Widget):
    pass


class ClassLevelTemplateWidget(Widget):
    template_path = 'other.html'


class ContextChosenTemplateWidget(Widget):
    def set_context(self):
        self.template_path = 'chosen.html'


class UnsetBasePage(Page):
    pass


class ClassLevelBasePage(Page):
    base_template_path = '../templates/base.html'


class TemplatePathTestCase(SimpleTestCase):
    def test_get_template_path__returns_module_named_html__when_template_path_unset(self):
        self.assertEqual(
            DefaultTemplateWidget().get_template_path(),
            os.path.join(TESTS_DIR, 'tests.html'))

    def test_get_template_path__returns_sibling_file__when_template_path_set_on_class(self):
        self.assertEqual(
            ClassLevelTemplateWidget().get_template_path(),
            os.path.join(TESTS_DIR, 'other.html'))

    def test_get_template_path__returns_sibling_file__when_template_path_set_in_set_context(self):
        widget = ContextChosenTemplateWidget()
        widget.set_context()

        self.assertEqual(widget.get_template_path(), os.path.join(TESTS_DIR, 'chosen.html'))

    def test_get_template_path__returns_path_unchanged__when_template_path_absolute(self):
        widget = DefaultTemplateWidget()
        widget.template_path = '/srv/templates/absolute.html'

        self.assertEqual(widget.get_template_path(), '/srv/templates/absolute.html')

    def test_render_html__renders_chosen_template__when_template_path_set(self):
        with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as template_file:
            template_file.write('chosen {{ data.word }}')
        self.addCleanup(os.remove, template_file.name)

        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        widget = DefaultTemplateWidget()
        widget._request = request
        widget.template_path = template_file.name
        widget.context.data['word'] = 'template'

        self.assertEqual(widget.render_html(), 'chosen template')


class BaseTemplatePathTestCase(SimpleTestCase):
    def test_get_base_template_path__fails__when_base_template_path_unset(self):
        with self.assertRaises(NotImplementedError):
            UnsetBasePage().get_base_template_path()

    def test_get_base_template_path__returns_path_beside_class__when_base_template_path_relative(self):
        self.assertEqual(
            ClassLevelBasePage().get_base_template_path(),
            os.path.join(TESTS_DIR, '../templates/base.html'))

    def test_get_base_template_path__returns_path_unchanged__when_base_template_path_absolute(self):
        page = UnsetBasePage()
        page.base_template_path = '/srv/templates/base.html'

        self.assertEqual(page.get_base_template_path(), '/srv/templates/base.html')
