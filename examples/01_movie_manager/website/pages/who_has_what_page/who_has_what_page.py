from website_widgets import register_url

from api.models import Rental
from website.exceptions import UnauthorizedException
from website.pages.app_page import AppPage
from website.widgets.who_has_what_row import WhoHasWhatRow


@register_url('who-has-what')
class WhoHasWhatPage(AppPage):
    """Every movie that's out right now, who has it, and for how long."""

    page_title = 'Who has what'

    async def set_context(self):
        # Names the family, so it's for people who are signed in.
        if not self.context.page['user'].is_authenticated:
            raise UnauthorizedException("Sign in to see who has what.")

        # select_related, because each row reads its rental's movie and user: following the
        # foreign keys there would run a sync query inside the async page.
        rentals = (
            Rental.objects
            .filter(returned_at__isnull=True)
            .select_related('copy__movie', 'user')
            .order_by('copy__movie__title', 'taken_at')
        )
        viewer_id = self.context.page['user'].id
        self.context.children['rows'] = [
            WhoHasWhatRow(rental=rental, viewer_id=viewer_id)
            async for rental in rentals
        ]
