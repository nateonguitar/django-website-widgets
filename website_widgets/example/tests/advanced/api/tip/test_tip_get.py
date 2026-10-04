from unittest.mock import patch

from django.urls import reverse

from website_widgets.example.advanced.api.tip.get import TipGetEndpoint
from website_widgets.example.advanced.widgets.tip_card.tip_card import TipCard
from website_widgets.example.tests.example_test_case import ExampleTestCase


class TipGetEndpointTestCase(ExampleTestCase):
    def setUp(self):
        super().setUp()
        no_wait = patch.object(TipGetEndpoint, 'MOCK_QUERY_SECONDS', 0)
        no_wait.start()
        self.addCleanup(no_wait.stop)

    def tip_url(self, number) -> str:
        return f"{reverse('website_widgets_example_api_tip')}?number={number}"

    def test_tip__returns_requested_tip__when_number_given(self):
        response = self.client.get(self.tip_url(3))

        self.assertEqual(response.status_code, 200)
        self.assertIn('data-tip-number="3"', response.json()['html'])
        self.assertIn('Tip 3', response.json()['html'])

    def test_tip__wraps_around__when_number_past_last_tip(self):
        number = len(TipCard.TIPS)

        html = self.client.get(self.tip_url(number)).json()['html']

        self.assertIn(f'Tip {number}', html)
        self.assertIn('through its constructor', html)

    def test_tip__returns_the_markup_the_page_renders__when_same_number(self):
        endpoint_html = self.client.get(self.tip_url(0)).json()['html']
        page_html = self.client.get(reverse('website_widgets_example_widget_from_endpoint')).content.decode()

        self.assertIn(endpoint_html, page_html)

    def test_tip__fails__when_number_missing(self):
        response = self.client.get(reverse('website_widgets_example_api_tip'))

        self.assertEqual(response.status_code, 422)
        self.assertIn('number', response.json()['errors'])

    def test_tip__fails__when_number_negative(self):
        self.assertEqual(self.client.get(self.tip_url(-1)).status_code, 422)
