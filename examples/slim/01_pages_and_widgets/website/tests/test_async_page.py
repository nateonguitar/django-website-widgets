import re
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from website.slow_api import SlowApi


class AsyncPageTestCase(TestCase):
    def get_html(self, seconds: float) -> str:
        with patch.object(SlowApi, 'SECONDS', seconds):
            return self.client.get(reverse('website:AsyncPage')).content.decode()

    def timings(self, html: str) -> list[tuple[int, int]]:
        return [
            (int(started), int(finished))
            for started, finished in re.findall(r'Started at (\d+) ms, finished at (\d+) ms', html)
        ]

    def test_async_page__lists_books_from_async_orm__when_rendered(self):
        html = self.get_html(0)

        self.assertIn('<td>Dune</td>', html)
        self.assertIn('<td>The Hobbit</td>', html)

    def test_async_page__shows_synchronous_only_operation__when_widget_queries_synchronously(self):
        html = self.get_html(0)

        self.assertIn('SynchronousOnlyOperation:', html)

    def test_async_page__runs_parent_calls_together__when_gathered(self):
        together = self.timings(self.get_html(0.05))[:3]

        # All three start before any finishes.
        self.assertLess(max(started for started, _ in together), min(finished for _, finished in together))

    def test_async_page__runs_widget_calls_one_after_another__when_each_awaits_its_own(self):
        one_after_another = self.timings(self.get_html(0.05))[3:]

        self.assertEqual(len(one_after_another), 3)
        for previous, following in zip(one_after_another, one_after_another[1:]):
            self.assertGreaterEqual(following[0], previous[1])
