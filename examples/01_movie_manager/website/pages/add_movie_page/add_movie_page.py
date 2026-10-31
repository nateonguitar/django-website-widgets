from website_widgets import register_url

from api.models import Genre
from website.exceptions import UnauthorizedException
from website.pages.app_page import AppPage
from website.widgets.rating_picker import RatingPicker


@register_url('add-movie')
class AddMoviePage(AppPage):
    page_title = 'Add to inventory'

    async def set_context(self):
        if not self.context.page['user'].is_authenticated:
            raise UnauthorizedException('Sign in to add movies to the shelf.')
        self.context.data['genres'] = Genre.choices
        self.context.children['rating'] = RatingPicker(name='rating')
