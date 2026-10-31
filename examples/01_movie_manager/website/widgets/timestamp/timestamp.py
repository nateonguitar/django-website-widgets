from datetime import datetime, timedelta
from enum import StrEnum

from django.utils import timezone
from website_widgets import Widget


class TimestampStyle(StrEnum):
    # Tue 27 Oct 2026
    DATE = 'date'
    # 4 days ago
    AGO = 'ago'
    # 4 days, as in "out for 4 days"
    DURATION = 'duration'


class Timestamp(Widget):
    """
    Every date the site shows, written one way: a <time> with the moment in its `datetime`, for
    screen readers and anything reading the page, the exact time on hover, and the text in one
    of a few styles. A widget, not a template filter, since it's markup; a page's table nests one
    per row, and so does the admin.
    """

    def __init__(self, value: datetime, style: TimestampStyle = TimestampStyle.DATE):
        super().__init__()
        self.value = value
        self.style = style

    def set_context(self):
        self.context.data['value'] = self.value
        self.context.data['style'] = self.style.value
        # timesince counts whole minutes, so under one it says "0 minutes".
        self.context.data['under_a_minute'] = timezone.now() - self.value < timedelta(minutes=1)
