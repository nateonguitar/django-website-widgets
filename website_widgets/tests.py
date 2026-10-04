import os
import tempfile
from types import SimpleNamespace
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


class SyncContextWidget(Widget):
    def set_context(self):
        self.context.data['word'] = 'sync'


class AsyncContextWidget(Widget):
    async def set_context(self):
        self.context.data['word'] = 'async'


class WordWidget(Widget):
    def __init__(self, word: str, template_filename: str):
        super().__init__()
        self.word = word
        self.template_filename = template_filename

    def set_context(self):
        self.context.data['word'] = self.word


class ParentWidget(Widget):
    def __init__(self, child_template_filename: str):
        super().__init__()
        self.child_template_filename = child_template_filename

    def set_context(self):
        self.context.children['single'] = WordWidget('one', self.child_template_filename)
        self.context.children['many'] = [
            WordWidget('two', self.child_template_filename),
            WordWidget('three', self.child_template_filename),
        ]
        self.context.children['absent'] = None


class WidgetTestCase(SimpleTestCase):
    def write_template(self, content: str) -> str:
        """Writes a template beside this module for one test and returns its bare file name."""
        with tempfile.NamedTemporaryFile('w', suffix='.html', dir=TESTS_DIR, delete=False) as template_file:
            template_file.write(content)
        self.addCleanup(os.remove, template_file.name)
        return os.path.basename(template_file.name)


class TemplateFilenameTestCase(WidgetTestCase):
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

    def test_render__test_sync__renders_chosen_template__when_template_filename_set(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('chosen {{ data.word }}')
        widget.context.data['word'] = 'template'

        self.assertEqual(widget.render__test_sync(), 'chosen template')


class RenderInPlaceTestCase(WidgetTestCase):
    async def test_render__test__runs_set_context__when_set_context_is_sync(self):
        widget = SyncContextWidget()
        widget.template_filename = self.write_template('{{ data.word }}')

        self.assertEqual(await widget.render__test(), 'sync')

    async def test_render__test__runs_set_context__when_set_context_is_async(self):
        widget = AsyncContextWidget()
        widget.template_filename = self.write_template('{{ data.word }}')

        self.assertEqual(await widget.render__test(), 'async')

    async def test_render__test__renders_children__when_nested_and_listed(self):
        widget = ParentWidget(self.write_template('{{ data.word }}'))
        widget.template_filename = self.write_template(
            '{{ children.single }}|{% for child in children.many %}{{ child }},{% endfor %}|'
            '{{ children.absent|default_if_none:"none" }}')

        self.assertEqual(await widget.render__test(), 'one|two,three,|none')

    async def test_render__test__shares_page_context_with_children__when_set_before_rendering(self):
        widget = ParentWidget(self.write_template('{{ page.nonce }}'))
        widget.template_filename = self.write_template('{{ children.single }}')
        widget.context.page['nonce'] = 'abc'

        self.assertEqual(await widget.render__test(), 'abc')

    async def test_render__test__renders_as_anonymous__when_no_user_given(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ user.is_authenticated }}')

        self.assertEqual(await widget.render__test(), 'False')

    async def test_render__test__renders_as_user__when_user_given(self):
        user = SimpleNamespace(is_authenticated=True, username='riley')
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ user.username }}')

        self.assertEqual(await widget.render__test(user=user), 'riley')

    async def test_render__standalone__renders_with_given_request__when_called(self):
        request = RequestFactory().get('/somewhere/')
        request.user = AnonymousUser()
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ request.path }}')

        self.assertEqual(await widget.render__standalone(request), '/somewhere/')

    async def test_render__test__fails__when_already_rendered(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('once')
        await widget.render__test()

        with self.assertRaises(RuntimeError):
            await widget.render__test()


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
