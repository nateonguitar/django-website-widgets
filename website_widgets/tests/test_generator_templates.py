import os

from django.test import SimpleTestCase

from website_widgets.management.starter_site import StarterSite


TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'generator_templates')


class GeneratorTemplatesTestCase(SimpleTestCase):
    def test_generator_templates__hold_no_project_opinions__when_shipped(self):
        for filename in os.listdir(TEMPLATES_DIR):
            with open(os.path.join(TEMPLATES_DIR, filename), encoding='utf-8') as file:
                content = file.read().lower()
            for opinion in ('nonce', 'logger', 'loglabel', 'gametabs', 'fetch('):
                with self.subTest(template=filename, opinion=opinion):
                    self.assertNotIn(opinion, content)

    def test_controller_template__has_the_controller_shape__when_shipped(self):
        with open(os.path.join(TEMPLATES_DIR, 'controller.ts.tmpl'), encoding='utf-8') as file:
            controller_ts = file.read()

        for expected in (
            'class Elements {\n    label: HTMLElement | null = null;\n',
            'public findIn(root: HTMLElement | null): void',
            "this.label = root.querySelector('.__css_name____label');",
            'private elements = new Elements();',
            'this.elements.findIn(this.rootElement);',
            'this.rootElement?.dataset.label',
            'this.elements.label.textContent = this.label;',
            'protected initializeListeners(): void',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, controller_ts)
        self.assertNotIn('super.', controller_ts)
        # The template's <script> starts it, so the controller has no static starter of its own.
        self.assertNotIn('static', controller_ts)

    def test_controller_html_templates__start_the_controller_on_their_root__when_shipped(self):
        for filename, root_attribute, selector in (
            ('page__controller.html.tmpl', 'id="__css_name__"', '#__css_name__'),
            ('widget__controller__single.html.tmpl', 'id="__css_name__"', '#__css_name__'),
            ('widget__controller__repeating.html.tmpl', 'data-key="{{ data.key }}"', '.__css_name__[data-key="{{ data.key }}"]'),
        ):
            with open(os.path.join(TEMPLATES_DIR, filename), encoding='utf-8') as file:
                html = file.read()
            with self.subTest(template=filename):
                self.assertIn(root_attribute, html)
                self.assertIn('data-label="{{ data.label }}"', html)
                self.assertIn("import { App, __ClassName__Controller } from", html)
                self.assertIn(f"await App.initController(new __ClassName__Controller(), '{selector}');", html)

    def test_repeating_widget_template__has_no_id__when_shipped(self):
        with open(os.path.join(TEMPLATES_DIR, 'widget__controller__repeating.html.tmpl'), encoding='utf-8') as file:
            html = file.read()

        self.assertNotIn('id=', html)

    def test_repeating_widget_templates__take_key_as_keyword_only__when_shipped(self):
        for filename in ('widget__async__repeating.py.tmpl', 'widget__sync__repeating.py.tmpl'):
            with open(os.path.join(TEMPLATES_DIR, filename), encoding='utf-8') as file:
                widget_py = file.read()
            with self.subTest(template=filename):
                self.assertIn('def __init__(self, *, key):', widget_py)
                self.assertIn("        super().__init__()\n        self.context.data['key'] = key\n", widget_py)

    def test_starter_site__holds_no_nonce_or_gametabs_code__when_shipped(self):
        # The starter shows conventions, so it may fetch and keep state, but a CSP is the site's call.
        for path, content in StarterSite('website').files().items():
            for opinion in ('nonce', 'gametabs'):
                with self.subTest(path=path, opinion=opinion):
                    self.assertNotIn(opinion, content.lower())
