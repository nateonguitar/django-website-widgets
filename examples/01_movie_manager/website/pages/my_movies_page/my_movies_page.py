from website_widgets import register_url

from api.models import Rental
from website.exceptions import UnauthorizedException
from website.pages.app_page import AppPage
from website.widgets.rental_row import RentalRow


@register_url('my-movies')
class MyMoviesPage(AppPage):
    page_title = 'My movies'

    async def set_context(self):
        user = self.context.page['user']
        if not user.is_authenticated:
            raise UnauthorizedException('Sign in to see the movies you have.')

        # select_related, because each row's template reads rental.copy.movie: following the
        # foreign keys there would run a sync query inside the async page.
        rentals = (
            Rental.objects
            .filter(user=user, returned_at__isnull=True)
            .select_related('copy__movie')
        )
        self.context.children['rows'] = [RentalRow(rental=rental, key=rental.id) async for rental in rentals]
