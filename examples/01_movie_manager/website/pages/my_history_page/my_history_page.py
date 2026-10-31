import json
from collections import Counter
from datetime import timedelta

from django.utils import timezone
from website_widgets import register_url

from api.models import Rental
from website.exceptions import UnauthorizedException
from website.pages.app_page import AppPage
from website.widgets.history_row import HistoryRow


@register_url('my-history')
class MyHistoryPage(AppPage):
    """
    Every movie the signed-in user has taken, newest first, whether it's back or not, under a
    chart of how many they took each day.
    """

    page_title = 'My history'
    CHART_DAYS = 90

    async def set_context(self):
        user = self.context.page['user']
        if not user.is_authenticated:
            raise UnauthorizedException('Sign in to see the movies you have taken.')

        # select_related, because the template reads each rental's movie: following the foreign
        # keys there would run a sync query inside the async page.
        rentals = (
            Rental.objects
            .filter(user=user)
            .select_related('copy__movie')
            .order_by('-taken_at')
        )
        rentals = [rental async for rental in rentals]
        # A widget per row, each nesting the Timestamps its dates are written with. A few hundred
        # rows is a few hundred small renders; a page listing thousands would paginate.
        self.context.children['rows'] = [HistoryRow(rental=rental) for rental in rentals]

        # Every day in the range, including the ones with nothing taken, so the chart's gaps
        # are real days.
        today = timezone.localdate()
        days = [today - timedelta(days=days_ago) for days_ago in range(self.CHART_DAYS - 1, -1, -1)]
        taken_per_day = Counter(timezone.localtime(rental.taken_at).date() for rental in rentals)
        counts = [taken_per_day[day] for day in days]
        self.context.data['chart_days'] = self.CHART_DAYS
        self.context.data['chart_total'] = sum(counts)
        # For the controller, in data- attributes on the page's root.
        self.context.data['chart_labels'] = json.dumps([f'{day:%a} {day.day} {day:%b}' for day in days])
        self.context.data['chart_counts'] = json.dumps(counts)
