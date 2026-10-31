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
            'class Elements {\n    label: HTMLElement | null = null;\n}',
            'private elements = new Elements();',
            'protected buildElements(): void',
            'this.elements.label = this.__element?.querySelector',
            'this.__element?.dataset.label',
            'this.elements.label.textContent = this.label;',
            'protected initializeListeners(): void',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, controller_ts)
        self.assertNotIn('super.', controller_ts)
        # The template's <script> starts it, so the controller has no static starter of its own.
        self.assertNotIn('static', controller_ts)

    def test_controller_html_templates__start_the_controller_on_their_root__when_shipped(self):
        for filename in ('page__controller.html.tmpl', 'widget__controller.html.tmpl'):
            with open(os.path.join(TEMPLATES_DIR, filename), encoding='utf-8') as file:
                html = file.read()
            with self.subTest(template=filename):
                self.assertIn('id="__css_name__"', html)
                self.assertIn('data-label="{{ data.label }}"', html)
                self.assertIn("import { App, __ClassName__Controller } from", html)
                self.assertIn("await App.initController(new __ClassName__Controller(), '#__css_name__');", html)

    def test_starter_site__holds_no_nonce_or_gametabs_code__when_shipped(self):
        # The starter shows conventions, so it may fetch and keep state, but a CSP is the site's call.
        for path, content in StarterSite('website').files().items():
            for opinion in ('nonce', 'gametabs'):
                with self.subTest(path=path, opinion=opinion):
                    self.assertNotIn(opinion, content.lower())
