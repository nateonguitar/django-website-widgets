import os

from django.test import SimpleTestCase


TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'generator_templates')


class GeneratorTemplatesTestCase(SimpleTestCase):
    def test_generator_templates__hold_no_project_opinions__when_shipped(self):
        for filename in os.listdir(TEMPLATES_DIR):
            with open(os.path.join(TEMPLATES_DIR, filename), encoding='utf-8') as file:
                content = file.read().lower()
            for opinion in ('nonce', 'logger', 'loglabel', 'gametabs', 'fetch('):
                with self.subTest(template=filename, opinion=opinion):
                    self.assertNotIn(opinion, content)
