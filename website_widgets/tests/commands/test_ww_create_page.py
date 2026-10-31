import os
from types import ModuleType
from unittest.mock import patch

from django.core.management import CommandError
from django.test import override_settings
from django.urls import path

from website_widgets import PageRoutes
from website_widgets.tests.commands.component_test_case import ComponentTestCase


class WwCreatePageTestCase(ComponentTestCase):
    def create_page(self, *args: str) -> str:
        return self.run_command('ww_create_page', *args)

    def use_urlconf(self, urlpatterns: list):
        urlconf = ModuleType('ww_create_page_test_urlconf')
        urlconf.urlpatterns = urlpatterns
        self.enterContext(override_settings(ROOT_URLCONF=urlconf))

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

    def test_create_page__routes_to_route_made_from_name__when_no_route_is_given(self):
        for name, page_py_path, route in (
            ('about', ('about', 'about.py'), 'about'),
            ('login_page', ('login_page', 'login_page.py'), 'login'),
            ('manage_auth_tokens_page', ('manage_auth_tokens_page', 'manage_auth_tokens_page.py'), 'manage-auth-tokens'),
            ('account/settings_page', ('account', 'settings_page', 'settings_page.py'), 'account/settings'),
        ):
            with self.subTest(name=name):
                self.create_page(name, '--tscontroller=false', '--stylesheet=false')

                page_py = self.read(self.app_folder, 'pages', *page_py_path)
                self.assertIn('from website_widgets import register_url\n', page_py)
                self.assertIn(f"@register_url('{route}')\nclass ", page_py)

    def test_create_page__routes_to_given_route_asking_nothing__when_route_is_given(self):
        for name, route in (
            ('login_page', 'Account/Sign-In'),
            ('home_page', ''),
        ):
            with self.subTest(name=name):
                with patch('builtins.input') as mock_input:
                    self.create_page(name, '--tscontroller=false', '--stylesheet=false', f'--route={route}')

                mock_input.assert_not_called()
                page_py = self.read(self.app_folder, 'pages', name, f'{name}.py')
                self.assertIn(f"@register_url('{route}')", page_py)

    def test_create_page__warns__when_route_ties_with_another_pages(self):
        self.create_page('about_page', '--tscontroller=false', '--stylesheet=false', '--route=about/<int:id>')

        output = self.create_page('info_page', '--tscontroller=false', '--stylesheet=false', '--route=about/<int:pk>')

        self.assertIn("'about/<int:id>' (AboutPage) can match the same URLs as 'about/<int:pk>'", output)
        self.assertIn("@register_url('about/<int:pk>')", self.read(self.app_folder, 'pages', 'info_page', 'info_page.py'))

    def test_create_page__fails_writing_nothing__when_another_route_has_the_class_name(self):
        self.create_page('account/settings_page', '--tscontroller=false', '--stylesheet=false')

        with self.assertRaisesMessage(CommandError, "A route is already named 'SettingsPage'"):
            self.create_page('settings_page', '--tscontroller=false', '--stylesheet=false')

        self.assertFalse(os.path.exists(os.path.join(self.app_folder, 'pages', 'settings_page')))

    def test_create_page__fails_writing_nothing__when_route_has_an_unknown_converter(self):
        with self.assertRaisesMessage(CommandError, "invalid converter 'bogus'"):
            self.create_page('login_page', '--tscontroller=false', '--stylesheet=false', '--route=<bogus:x>')

        self.assertFalse(os.path.exists(os.path.join(self.app_folder, 'pages', 'login_page')))

    def test_create_page__lists_each_file_with_url_and_view_name__when_created(self):
        self.use_urlconf([path('', PageRoutes.urls())])

        output = self.create_page('account/settings_page', '--tscontroller=true', '--stylesheet=true')

        page_folder = os.path.join(self.app_folder, 'pages', 'account', 'settings_page')
        self.assertIn(
            f'Created the page SettingsPage in {page_folder}/:\n'
            '  __init__.py\n'
            '  settings_page.py     class SettingsPage(WebPage), routed to /account/settings, reversed as website:SettingsPage\n'
            '  settings_page.html   root #settings-page\n'
            '  settings_page.ts     SettingsPageController, exported from ts/main.ts\n'
            '  settings_page.scss   imported in ts/main.ts\n',
            output)

    def test_create_page__shows_url_after_prefix__when_routes_are_included_under_one(self):
        self.use_urlconf([path('site/', PageRoutes.urls())])

        output = self.create_page('login_page', '--tscontroller=false', '--stylesheet=false')

        self.assertIn('routed to /site/login, reversed as website:LoginPage', output)

    def test_create_page__says_route_waits_for_urls_py__when_routes_are_not_included(self):
        self.use_urlconf([])

        output = self.create_page('login_page', '--tscontroller=false', '--stylesheet=false')

        self.assertIn("routed to 'login' once urls.py includes PageRoutes.urls(), reversed as website:LoginPage", output)

    def test_create_page__writes_page_with_no_route_or_route_checks__when_project_page_py_template_has_no_route(self):
        self.create_page('account/settings_page', '--tscontroller=false', '--stylesheet=false')
        self.write(
            'from __app_page_module__ import __AppPageClass__\n\n\nclass __ClassName__(__AppPageClass__):\n    pass\n',
            self.templates_dir,
            'page.py.tmpl')

        self.create_page('settings_page', '--tscontroller=false', '--stylesheet=false')

        self.assertNotIn('register_url', self.read(self.app_folder, 'pages', 'settings_page', 'settings_page.py'))

    def test_create_page__suggests_decorator_and_urls_py_lines__when_project_page_py_template_has_no_route(self):
        self.write(
            'from __app_page_module__ import __AppPageClass__\n\n\nclass __ClassName__(__AppPageClass__):\n    pass\n',
            self.templates_dir,
            'page.py.tmpl')

        output = self.create_page('account/settings_page', '--tscontroller=false', '--stylesheet=false')

        self.assertIn(
            "settings_page.py     class SettingsPage(WebPage), not routed: the project's page.py.tmpl has "
            "no @register_url('__route__')\n",
            output)
        self.assertIn(
            "To serve it, add @register_url('account/settings') above its class, or route it in urls.py:\n"
            "  from website.pages.account.settings_page import SettingsPage\n"
            "  path('account/settings', SettingsPage.as_view(), name='SettingsPage'),\n",
            output)
