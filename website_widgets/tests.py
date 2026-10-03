import os
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase

from website_widgets.page import Page
from website_widgets.widget import Widget


TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


class DefaultTemplateWidget(Widget):
    pass


class ClassLevelTemplateWidget(Widget):
    template_filename = 'tests.py'


class ContextChosenTemplateWidget(Widget):
    def set_context(self):
        self.template_filename = '__init__.py'


class BaseFolderWidget(Widget):
    pass


class SubfolderWidget(BaseFolderWidget):
    pass


class UnsetBasePage(Page):
    pass


class ClassLevelBasePage(Page):
    base_template_path = '../templates/base.html'


class TemplateFilenameTestCase(SimpleTestCase):
    """Existing files beside this module stand in for templates, since only the lookup is tested."""

    def test_get_template_path__returns_module_named_html__when_template_filename_unset(self):
        self.assertEqual(
            DefaultTemplateWidget().get_template_path(),
            os.path.join(TESTS_DIR, 'tests.html'))

    def test_get_template_path__returns_sibling_file__when_template_filename_set_on_class(self):
        self.assertEqual(
            ClassLevelTemplateWidget().get_template_path(),
            os.path.join(TESTS_DIR, 'tests.py'))

    def test_get_template_path__returns_sibling_file__when_template_filename_set_in_set_context(self):
        widget = ContextChosenTemplateWidget()
        widget.set_context()

        self.assertEqual(widget.get_template_path(), os.path.join(TESTS_DIR, '__init__.py'))

    def test_get_template_path__fails__when_template_filename_is_a_path(self):
        for filename in ('/srv/templates/absolute.html', 'sub/child.html', '../up.html', 'a\\b.html', '..'):
            with self.subTest(filename=filename):
                widget = DefaultTemplateWidget()
                widget.template_filename = filename
                with self.assertRaises(ValueError):
                    widget.get_template_path()

    def test_get_template_path__fails_naming_the_searched_folders__when_file_is_missing(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = 'missing.html'

        with self.assertRaises(FileNotFoundError) as caught:
            widget.get_template_path()
        self.assertIn(TESTS_DIR, str(caught.exception))

    def test_get_template_path__returns_base_class_file__when_only_the_base_folder_has_it(self):
        with tempfile.TemporaryDirectory() as root:
            base_dir = os.path.join(root, 'base')
            sub_dir = os.path.join(root, 'base', 'sub')
            os.makedirs(sub_dir)
            with open(os.path.join(base_dir, 'base__variant.html'), 'w') as template_file:
                template_file.write('')
            fake_files = {
                SubfolderWidget: os.path.join(sub_dir, 'sub.py'),
                BaseFolderWidget: os.path.join(base_dir, 'base.py'),
            }
            widget = SubfolderWidget()
            widget.template_filename = 'base__variant.html'

            with patch('website_widgets.widget.inspect.getfile', side_effect=fake_files.__getitem__):
                path = widget.get_template_path()

        self.assertEqual(path, os.path.join(base_dir, 'base__variant.html'))

    def test_get_template_path__prefers_own_folder__when_class_and_base_both_have_the_file(self):
        with tempfile.TemporaryDirectory() as root:
            base_dir = os.path.join(root, 'base')
            sub_dir = os.path.join(root, 'base', 'sub')
            os.makedirs(sub_dir)
            for folder in (base_dir, sub_dir):
                with open(os.path.join(folder, 'shared.html'), 'w') as template_file:
                    template_file.write('')
            fake_files = {
                SubfolderWidget: os.path.join(sub_dir, 'sub.py'),
                BaseFolderWidget: os.path.join(base_dir, 'base.py'),
            }
            widget = SubfolderWidget()
            widget.template_filename = 'shared.html'

            with patch('website_widgets.widget.inspect.getfile', side_effect=fake_files.__getitem__):
                path = widget.get_template_path()

        self.assertEqual(path, os.path.join(sub_dir, 'shared.html'))

    def test_render_html__renders_chosen_template__when_template_filename_set(self):
        with tempfile.NamedTemporaryFile('w', suffix='.html', dir=TESTS_DIR, delete=False) as template_file:
            template_file.write('chosen {{ data.word }}')
        self.addCleanup(os.remove, template_file.name)

        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        widget = DefaultTemplateWidget()
        widget._request = request
        widget.template_filename = os.path.basename(template_file.name)
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
