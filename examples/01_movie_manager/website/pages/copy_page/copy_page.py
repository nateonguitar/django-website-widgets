from website_widgets import register_url

from api.models import Copy, Movie, Rental
from website.exceptions import NotFoundException
from website.pages.app_page import AppPage
from website.widgets.copy_report_row import CopyReportRow
from website.widgets.movie_card import MovieCard
from website.widgets.report_copy_dialog import ReportCopyDialog
from website.widgets.timestamp import Timestamp, TimestampStyle


@register_url('copies/<slug:label>')
class CopyPage(AppPage):
    """One copy: its movie, its label, where it is, and the problems reported with it."""

    def __init__(self, label: str):
        super().__init__()
        # The route's <slug:label>, the one printed on the case.
        self.label = label

    async def set_context(self):
        copy = await Copy.objects.filter(label=self.label).afirst()
        if copy is None:
            raise NotFoundException('No copy has that label. Check the sticker on the case.')
        movie = await Movie.objects.with_availability().aget(id=copy.movie_id)
        self.page_title = f'{movie.title}, copy {copy.label}'

        # The template names who has it, so the user comes in the same query.
        rental = await Rental.objects.filter(copy=copy, returned_at__isnull=True).select_related('user').afirst()
        reports = copy.reports.select_related('user')
        user = self.context.page['user']
        is_out_with_viewer = rental is not None and rental.user_id == user.id
        # The endpoint's rule: whoever has it out, or staff, while it is in rotation.
        can_report = copy.retired_at is None and (is_out_with_viewer or user.is_staff)

        self.context.data['copy'] = copy
        self.context.data['rental'] = rental
        self.context.data['is_out_with_viewer'] = is_out_with_viewer
        self.context.data['can_report'] = can_report
        self.context.children['card'] = MovieCard(movie=movie, key=movie.id)
        self.context.children['reports'] = [CopyReportRow(report=report) async for report in reports]
        if copy.retired_at is not None:
            self.context.children['retired'] = Timestamp(value=copy.retired_at, style=TimestampStyle.AGO)
        elif rental is not None:
            self.context.children['out_for'] = Timestamp(value=rental.taken_at, style=TimestampStyle.DURATION)
        if can_report:
            self.context.children['report_dialog'] = ReportCopyDialog()
