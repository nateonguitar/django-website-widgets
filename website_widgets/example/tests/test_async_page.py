import re
from unittest.mock import patch

from django.urls import reverse

from website_widgets.example.advanced.mock_query import MockQuery
from website_widgets.example.tests.example_test_case import ExampleTestCase


class AsyncPageTestCase(ExampleTestCase):
    def timings(self, html: str) -> list[tuple[int, int]]:
        return [
            (int(started), int(finished))
            for started, finished in re.findall(r'Started at (\d+) ms, finished at (\d+) ms', html)
        ]

    def test_async_page__renders_six_query_cards__when_rendered(self):
        with patch.object(MockQuery, 'SECONDS', 0):
            response = self.client.get(reverse('website_widgets_example_async'))

        self.assertContains(response, 'class="example-card example-query"', count=6)

    def test_async_page__runs_parent_queries_together__when_gathered(self):
        with patch.object(MockQuery, 'SECONDS', 0.05):
            html = self.client.get(reverse('website_widgets_example_async')).content.decode()

        together = self.timings(html)[:3]
        # All three start before any finishes.
        self.assertLess(max(started for started, _ in together), min(finished for _, finished in together))

    def test_async_page__runs_widget_queries_one_after_another__when_each_awaits_its_own(self):
        with patch.object(MockQuery, 'SECONDS', 0.05):
            html = self.client.get(reverse('website_widgets_example_async')).content.decode()

        one_after_another = self.timings(html)[3:]
        for previous, following in zip(one_after_another, one_after_another[1:]):
            self.assertGreaterEqual(following[0], previous[1])
