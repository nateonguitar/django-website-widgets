from django.test import SimpleTestCase

from website_widgets.config import GenerateComponentConfig, TestingConfig, WebsiteWidgetsConfig


class WebsiteWidgetsConfigTestCase(SimpleTestCase):
    def test_generate_component__defaults_app_page_class_under_website_app__when_not_given(self):
        config = WebsiteWidgetsConfig(website_app_name='storefront')

        app_page_class = config.generate_component.get_app_page_class(config.website_app_name)
        self.assertEqual(app_page_class, 'storefront.pages.app_page.AppPage')
        self.assertIsNone(config.generate_component.templates_dir)

    def test_generate_component__returns_given_settings__when_given(self):
        generate_component = GenerateComponentConfig(
            app_page_class='mysite.pages.base.BasePage',
            templates_dir='/srv/generator_templates')
        config = WebsiteWidgetsConfig(generate_component=generate_component)

        app_page_class = config.generate_component.get_app_page_class('website')
        self.assertEqual(app_page_class, 'mysite.pages.base.BasePage')
        self.assertEqual(config.generate_component.templates_dir, '/srv/generator_templates')

    def test_testing__defaults_to_npm_run_build_and_the_playwright_tag__when_not_given(self):
        config = WebsiteWidgetsConfig()

        self.assertEqual(config.testing.build_command, ['npm', 'run', 'build'])
        self.assertEqual(config.testing.browser_test_tag, 'playwright')

    def test_testing__returns_given_settings__when_given(self):
        pnpm_testing = TestingConfig(build_command=('pnpm', 'build'), browser_test_tag='browser')
        pnpm_config = WebsiteWidgetsConfig(testing=pnpm_testing)
        no_build_testing = TestingConfig(build_command=None)

        self.assertEqual(pnpm_config.testing.build_command, ['pnpm', 'build'])
        self.assertEqual(pnpm_config.testing.browser_test_tag, 'browser')
        self.assertIsNone(no_build_testing.build_command)

    def test_testing_build_command__fails_naming_the_list__when_given_a_string(self):
        with self.assertRaises(TypeError) as caught:
            TestingConfig(build_command='npm run build')

        message = str(caught.exception)
        self.assertIn("['npm', 'run', 'build']", message)

    def test_website_app_name__returns_website__when_not_given(self):
        config = WebsiteWidgetsConfig()

        self.assertEqual(config.website_app_name, 'website')

    def test_website_app_name__returns_given_label__when_given(self):
        config = WebsiteWidgetsConfig(website_app_name='storefront')

        self.assertEqual(config.website_app_name, 'storefront')
