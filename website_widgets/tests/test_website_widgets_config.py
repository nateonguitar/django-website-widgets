from django.test import SimpleTestCase

from website_widgets.config import GenerateComponentConfig, WebsiteWidgetsConfig


class WebsiteWidgetsConfigTestCase(SimpleTestCase):
    def test_generate_component__defaults_app_page_class_under_website_app__when_not_given(self):
        config = WebsiteWidgetsConfig(website_app_name='storefront')

        self.assertEqual(
            config.generate_component.get_app_page_class(config.website_app_name),
            'storefront.pages.app_page.AppPage')
        self.assertIsNone(config.generate_component.templates_dir)

    def test_generate_component__returns_given_settings__when_given(self):
        config = WebsiteWidgetsConfig(generate_component=GenerateComponentConfig(
            app_page_class='mysite.pages.base.BasePage',
            templates_dir='/srv/generator_templates'))

        self.assertEqual(config.generate_component.get_app_page_class('website'), 'mysite.pages.base.BasePage')
        self.assertEqual(config.generate_component.templates_dir, '/srv/generator_templates')

    def test_test_build_command__returns_npm_run_build__when_not_given(self):
        config = WebsiteWidgetsConfig()

        self.assertEqual(config.test_build_command, ['npm', 'run', 'build'])

    def test_test_build_command__returns_given_command_or_none__when_given(self):
        pnpm_config = WebsiteWidgetsConfig(test_build_command=('pnpm', 'build'))
        no_build_config = WebsiteWidgetsConfig(test_build_command=None)

        self.assertEqual(pnpm_config.test_build_command, ['pnpm', 'build'])
        self.assertIsNone(no_build_config.test_build_command)

    def test_test_build_command__fails_naming_the_list__when_given_a_string(self):
        with self.assertRaises(TypeError) as caught:
            WebsiteWidgetsConfig(test_build_command='npm run build')

        message = str(caught.exception)
        self.assertIn("['npm', 'run', 'build']", message)

    def test_website_app_name__returns_website__when_not_given(self):
        self.assertEqual(WebsiteWidgetsConfig().website_app_name, 'website')

    def test_website_app_name__returns_given_label__when_given(self):
        config = WebsiteWidgetsConfig(website_app_name='storefront')

        self.assertEqual(config.website_app_name, 'storefront')
