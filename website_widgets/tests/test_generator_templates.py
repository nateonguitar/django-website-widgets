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

    def test_starter_site__holds_no_nonce_or_gametabs_code__when_shipped(self):
        # The starter shows conventions, so it may fetch and keep state, but a CSP is the site's call.
        for path, content in StarterSite('website').files().items():
            for opinion in ('nonce', 'gametabs'):
                with self.subTest(path=path, opinion=opinion):
                    self.assertNotIn(opinion, content.lower())
