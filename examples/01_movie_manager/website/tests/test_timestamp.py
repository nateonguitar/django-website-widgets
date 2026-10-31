from datetime import datetime, timedelta, timezone

from bs4 import BeautifulSoup
from django.test import TestCase
from django.utils import timezone as django_timezone

from website.widgets.timestamp import Timestamp, TimestampStyle


class TimestampTestCase(TestCase):
    def render(self, timestamp: Timestamp):
        return BeautifulSoup(timestamp.render(), 'html.parser').select_one('time')

    def test_timestamp__writes_the_moment_and_its_exact_time__in_every_style(self):
        moment = datetime(2026, 10, 27, 0, 53, tzinfo=timezone.utc)

        for style in TimestampStyle:
            with self.subTest(style=style):
                time = self.render(Timestamp(value=moment, style=style))

                self.assertEqual(time['datetime'], '2026-10-27T00:53:00+00:00')
                self.assertEqual(time['title'], 'Tue 27 Oct 2026, 00:53')

    def test_timestamp__writes_the_date__when_style_is_date(self):
        moment = datetime(2026, 10, 27, 0, 53, tzinfo=timezone.utc)

        time = self.render(Timestamp(value=moment))

        self.assertEqual(time.get_text(), 'Tue 27 Oct 2026')

    def test_timestamp__writes_how_long_ago__when_style_is_ago_or_duration(self):
        four_days_ago = django_timezone.now() - timedelta(days=4)

        ago = self.render(Timestamp(value=four_days_ago, style=TimestampStyle.AGO))
        duration = self.render(Timestamp(value=four_days_ago, style=TimestampStyle.DURATION))

        self.assertEqual(ago.get_text(), '4\xa0days ago')
        self.assertEqual(duration.get_text(), '4\xa0days')
