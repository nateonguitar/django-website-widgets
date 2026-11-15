import os
import tempfile
from unittest.mock import patch

from website_widgets.tests.sample_widgets import (
    SAMPLE_WIDGETS_DIR,
    BaseFolderWidget,
    ClassLevelTemplateWidget,
    ContextChosenTemplateWidget,
    DefaultTemplateWidget,
    SubfolderWidget,
)
from website_widgets.tests.widget_test_case import WidgetTestCase


class GetTemplatePathTestCase(WidgetTestCase):
    def test_get_template_path__returns_module_named_html__when_template_filename_unset(self):
        widget = DefaultTemplateWidget()

        path = widget.get_template_path()

        expected_path = os.path.join(SAMPLE_WIDGETS_DIR, 'sample_widgets.html')
        self.assertEqual(path, expected_path)

    def test_get_template_path__returns_sibling_file__when_template_filename_set_on_class(self):
        widget = ClassLevelTemplateWidget()

        path = widget.get_template_path()

        expected_path = os.path.join(SAMPLE_WIDGETS_DIR, 'sample_widgets.py')
        self.assertEqual(path, expected_path)

    def test_get_template_path__returns_sibling_file__when_template_filename_set_in_set_context(self):
        widget = ContextChosenTemplateWidget()
        widget.set_context()

        path = widget.get_template_path()

        expected_path = os.path.join(SAMPLE_WIDGETS_DIR, '__init__.py')
        self.assertEqual(path, expected_path)

    def test_get_template_path__fails__when_template_filename_is_a_path(self):
        filenames = ('/srv/templates/absolute.html', 'sub/child.html', '../up.html', 'a\\b.html', '..')
        for filename in filenames:
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

        message = str(caught.exception)
        self.assertIn(SAMPLE_WIDGETS_DIR, message)

    def test_get_template_path__returns_base_class_file__when_only_the_base_folder_has_it(self):
        with tempfile.TemporaryDirectory() as root:
            base_dir = os.path.join(root, 'base')
            sub_dir = os.path.join(root, 'base', 'sub')
            os.makedirs(sub_dir)
            variant_path = os.path.join(base_dir, 'base__variant.html')
            with open(variant_path, 'w') as template_file:
                template_file.write('')
            fake_files = {
                SubfolderWidget: os.path.join(sub_dir, 'sub.py'),
                BaseFolderWidget: os.path.join(base_dir, 'base.py'),
            }
            widget = SubfolderWidget()
            widget.template_filename = 'base__variant.html'

            with patch('website_widgets.widget.inspect.getfile', side_effect=fake_files.__getitem__):
                path = widget.get_template_path()

        self.assertEqual(path, variant_path)

    def test_get_template_path__prefers_own_folder__when_class_and_base_both_have_the_file(self):
        with tempfile.TemporaryDirectory() as root:
            base_dir = os.path.join(root, 'base')
            sub_dir = os.path.join(root, 'base', 'sub')
            os.makedirs(sub_dir)
            for folder in (base_dir, sub_dir):
                shared_path = os.path.join(folder, 'shared.html')
                with open(shared_path, 'w') as template_file:
                    template_file.write('')
            fake_files = {
                SubfolderWidget: os.path.join(sub_dir, 'sub.py'),
                BaseFolderWidget: os.path.join(base_dir, 'base.py'),
            }
            widget = SubfolderWidget()
            widget.template_filename = 'shared.html'

            with patch('website_widgets.widget.inspect.getfile', side_effect=fake_files.__getitem__):
                path = widget.get_template_path()

        expected_path = os.path.join(sub_dir, 'shared.html')
        self.assertEqual(path, expected_path)
