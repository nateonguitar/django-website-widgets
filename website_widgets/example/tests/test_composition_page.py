from django.urls import reverse

from website_widgets.example.tests.example_test_case import ExampleTestCase


class CompositionPageTestCase(ExampleTestCase):
    def test_composition_page__renders_every_child__when_rendered(self):
        response = self.client.get(reverse('website_widgets_example_composition'))

        self.assertContains(response, 'Constructor data')
        self.assertContains(response, 'List child 3')
        self.assertContains(response, 'nothing\n            rendered here', html=False)
        self.assertContains(response, 'the page title is "Composition"')
