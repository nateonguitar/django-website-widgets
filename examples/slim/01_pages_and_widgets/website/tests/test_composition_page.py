from django.test import TestCase
from django.urls import reverse


class CompositionPageTestCase(TestCase):
    def test_composition_page__renders_every_child__when_rendered(self):
        response = self.client.get(reverse('website:CompositionPage'))

        self.assertContains(response, 'Constructor data')
        self.assertContains(response, 'List child 3')
        self.assertContains(response, 'nothing\n            rendered here', html=False)

    def test_composition_page__shares_page_context_with_child__when_child_reads_it(self):
        response = self.client.get(reverse('website:CompositionPage'))

        self.assertContains(response, 'the page title is "Composition"')
        self.assertContains(response, 'site name is "Pages and widgets"')
