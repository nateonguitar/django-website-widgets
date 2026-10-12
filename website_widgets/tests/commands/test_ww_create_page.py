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

    def test_create_page__fails__when_folder_exists(self):
        os.makedirs(os.path.join(self.app_folder, 'pages', 'home_page'))

        with self.assertRaisesMessage(CommandError, 'already exists'):
            self.create_page('home_page', '--tscontroller=false', '--stylesheet=false')
