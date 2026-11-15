import os

from django.test import SimpleTestCase

from website_widgets.management.starter_site import StarterSite


PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(PACKAGE_DIR, 'generator_templates')


class GeneratorTemplatesTestCase(SimpleTestCase):
    def read_template(self, filename: str) -> str:
        template_path = os.path.join(TEMPLATES_DIR, filename)
        with open(template_path, encoding='utf-8') as file:
            return file.read()

    def test_generator_templates__hold_no_project_opinions__when_shipped(self):
        filenames = os.listdir(TEMPLATES_DIR)

        for filename in filenames:
            template_text = self.read_template(filename)
            content = template_text.lower()
            for opinion in ('nonce', 'logger', 'loglabel', 'gametabs', 'fetch('):
                with self.subTest(template=filename, opinion=opinion):
                    self.assertNotIn(opinion, content)

    def test_controller_template__has_the_controller_shape__when_shipped(self):
        controller_ts = self.read_template('controller.ts.tmpl')

        expected_lines = (
            'class Elements {\n    label: HTMLElement | null = null;\n',
            'public findIn(root: HTMLElement | null): void',
            "this.label = root.querySelector('.__css_name____label');",
            'private elements = new Elements();',
            'this.elements.findIn(this.rootElement);',
            'this.rootElement?.dataset.label',
            'this.elements.label.textContent = this.label;',
            'protected initializeListeners(): void',
        )
        for expected in expected_lines:
            with self.subTest(expected=expected):
                self.assertIn(expected, controller_ts)
        self.assertNotIn('super.', controller_ts)
        # The template's <script> starts it, so the controller has no static starter of its own.
        self.assertNotIn('static', controller_ts)

    def test_controller_html_templates__start_the_controller_on_their_root__when_shipped(self):
        cases = (
            ('page__controller.html.tmpl', 'id="__css_name__"', '#__css_name__'),
            ('widget__controller__single.html.tmpl', 'id="__css_name__"', '#__css_name__'),
            ('widget__controller__repeating.html.tmpl', 'data-key="{{ data.key }}"', '.__css_name__[data-key="{{ data.key }}"]'),
        )
        for filename, root_attribute, selector in cases:
            html = self.read_template(filename)
            expected_start = f"await App.initController(new __ClassName__Controller(), '{selector}');"
            with self.subTest(template=filename):
                self.assertIn(root_attribute, html)
                self.assertIn('data-label="{{ data.label }}"', html)
                self.assertIn("import { App, __ClassName__Controller } from", html)
                self.assertIn(expected_start, html)

    def test_repeating_widget_template__has_no_id__when_shipped(self):
        html = self.read_template('widget__controller__repeating.html.tmpl')

        self.assertNotIn('id=', html)

    def test_repeating_widget_templates__take_key_as_keyword_only__when_shipped(self):
        expected_constructor_body = (
            "        super().__init__()\n"
            "        self.context.data['key'] = key\n"
        )
        for filename in ('widget__async__repeating.py.tmpl', 'widget__sync__repeating.py.tmpl'):
            widget_py = self.read_template(filename)
            with self.subTest(template=filename):
                self.assertIn('def __init__(self, *, key):', widget_py)
                self.assertIn(expected_constructor_body, widget_py)

    def test_dialog_html_template__renders_only_a_template_with_the_dialog_attributes__when_shipped(self):
        html = self.read_template('dialog.html.tmpl')

        starts_with_template = html.startswith('<template id="__css_name__-template"')
        trimmed_html = html.rstrip()
        ends_with_template = trimmed_html.endswith('</template>')
        # Each show() copies the content, so an id inside would repeat.
        id_count = html.count('id=')
        self.assertTrue(starts_with_template)
        self.assertTrue(ends_with_template)
        self.assertIn('data-dialog-class="__css_name__"', html)
        self.assertIn('data-dialog-label>{{ data.title }}', html)
        self.assertIn('data-dialog-close', html)
        self.assertEqual(id_count, 1)
        self.assertNotIn('<script', html)

    def test_dialog_controller_template__opens_the_dialog_template__when_shipped(self):
        controller_ts = self.read_template('dialog_controller.ts.tmpl')

        expected_lines = (
            'import { DialogController } from "django-website-widgets";',
            'export class __ClassName__Controller extends DialogController<void> {',
            'public static show(): Promise<void> {',
            'new __ClassName__Controller(),\n            "#__css_name__-template",',
            'protected answer(): void {}',
        )
        for expected in expected_lines:
            with self.subTest(expected=expected):
                self.assertIn(expected, controller_ts)

    def test_dialog_py_template__is_a_sync_widget__when_shipped(self):
        dialog_py = self.read_template('dialog.py.tmpl')

        self.assertIn('class __ClassName__(SyncWidget):', dialog_py)
        self.assertIn("self.context.data['title'] = '__ClassName__'", dialog_py)
        self.assertNotIn('async', dialog_py)

    def test_starter_site__holds_no_nonce_or_gametabs_code__when_shipped(self):
        # The starter shows conventions, so it may fetch and keep state, but a CSP is the site's call.
        starter_site = StarterSite('website')
        starter_files = starter_site.files()

        for path, content in starter_files.items():
            lowered_content = content.lower()
            for opinion in ('nonce', 'gametabs'):
                with self.subTest(path=path, opinion=opinion):
                    self.assertNotIn(opinion, lowered_content)
