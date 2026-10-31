import os

from django.core.management import CommandError

from website_widgets.tests.commands.component_test_case import ComponentTestCase


class WwCreatePageTestCase(ComponentTestCase):
    def create_page(self, *args: str) -> str:
        return self.run_command('ww_create_page', *args)

    def test_create_page__extends_app_page_class__when_created(self):
        self.create_page('home_page', '--tscontroller=false', '--stylesheet=false')

        page_py = self.read(self.app_folder, 'pages', 'home_page', 'home_page.py')
        self.assertIn('from website_widgets.web_page import WebPage', page_py)
        self.assertIn('class HomePage(WebPage):', page_py)

    def test_create_page__writes_async_set_context_without_super__when_created(self):
        self.create_page('home_page', '--tscontroller=false', '--stylesheet=false')

        page_py = self.read(self.app_folder, 'pages', 'home_page', 'home_page.py')
        self.assertIn('    async def set_context(self):', page_py)
        self.assertNotIn('super()', page_py)

    def test_create_page__writes_main_root_with_heading__when_no_controller(self):
        self.create_page('home_page', '--tscontroller=false', '--stylesheet=false')

        html = self.read(self.app_folder, 'pages', 'home_page', 'home_page.html')
        self.assertIn('<main id="home-page"', html)
        self.assertIn('<h1>{{ data.label }}</h1>', html)
        self.assertNotIn('<script', html)

    def test_create_page__starts_controller_on_main_root__when_controller_generated(self):
        self.create_page('home_page', '--tscontroller=true', '--stylesheet=false')

        html = self.read(self.app_folder, 'pages', 'home_page', 'home_page.html')
        self.assertIn('<main id="home-page"', html)
        self.assertIn("await App.initController(new HomePageController(), '#home-page');", html)

    def test_create_page__uses_project_page_template_only_for_pages__when_templates_dir_has_one(self):
        self.write('<div class="app-page">{{ data.label }}</div>\n', self.templates_dir, 'page.html.tmpl')

        self.create_page('home_page', '--tscontroller=false', '--stylesheet=false')
        self.run_command('ww_create_widget', 'like_button', '--tscontroller=false', '--stylesheet=false')

        self.assertEqual(
            self.read(self.app_folder, 'pages', 'home_page', 'home_page.html'),
            '<div class="app-page">{{ data.label }}</div>\n')
        self.assertIn(
            '<div id="like-button"',
            self.read(self.app_folder, 'widgets', 'like_button', 'like_button.html'))

    def test_create_page__touches_pages_init_leaving_its_content__when_created(self):
        pages_init = os.path.join(self.app_folder, 'pages', '__init__.py')
        os.makedirs(os.path.dirname(pages_init))
        self.write('# the developer\'s\n', pages_init)
        os.utime(pages_init, (0, 0))

        self.create_page('home_page', '--tscontroller=false', '--stylesheet=false')

        self.assertGreater(os.path.getmtime(pages_init), 0)
        self.assertEqual(self.read(pages_init), '# the developer\'s\n')

    def test_create_page__registers_in_page_sections__when_both_generated(self):
        self.create_page('home_page', '--tscontroller=true', '--stylesheet=true')

        main_ts = self.read(self.app_folder, 'ts', 'main.ts')
        self.assertIn(
            "// {{ PAGE STYLES START }}\n"
            "import '../pages/home_page/home_page.scss';\n",
            main_ts)
        self.assertIn(
            "// {{ PAGE CONTROLLERS START }}\n"
            "export { HomePageController } from '../pages/home_page/home_page';\n",
            main_ts)

    def test_create_page__fails_naming_the_path__when_app_page_class_does_not_exist(self):
        self.config.generate_component.app_page_class = 'website.pages.app_page.AppPage'

        with self.assertRaisesMessage(CommandError, 'website.pages.app_page.AppPage'):
            self.create_page('home_page', '--tscontroller=false', '--stylesheet=false')

        self.assertFalse(os.path.exists(os.path.join(self.app_folder, 'pages', 'home_page')))

    def test_create_page__fails__when_app_page_class_is_not_a_page(self):
        self.config.generate_component.app_page_class = 'website_widgets.widget.Widget'

        with self.assertRaises(CommandError):
            self.create_page('home_page', '--tscontroller=false', '--stylesheet=false')

    def test_create_page__fails_writing_nothing__when_a_part_of_the_name_cannot_be_a_module(self):
        for name in ('Bad-Name', 'account/Settings', 'return', '../escape_page'):
            with self.subTest(name=name):
                with self.assertRaisesMessage(CommandError, "can't be a component name"):
                    self.create_page(name, '--tscontroller=false', '--stylesheet=false')

        self.assertFalse(os.path.exists(os.path.join(self.app_folder, 'pages')))
        self.assertFalse(os.path.exists(os.path.join(self.app_folder, 'escape_page')))

    def test_create_page__nests_the_page__when_name_has_a_folder(self):
        self.create_page('account/settings_page', '--tscontroller=false', '--stylesheet=false')

        page_py = self.read(self.app_folder, 'pages', 'account', 'settings_page', 'settings_page.py')
        self.assertIn('class SettingsPage(WebPage):', page_py)

    def test_create_page__fails__when_folder_exists(self):
        os.makedirs(os.path.join(self.app_folder, 'pages', 'home_page'))

        with self.assertRaisesMessage(CommandError, 'already exists'):
            self.create_page('home_page', '--tscontroller=false', '--stylesheet=false')
