from website_widgets import register_url

from api.models import Genre, MovieRating
from website.pages.app_page import AppPage
from website.widgets.movie_results import MovieResults


@register_url('find')
class FindMoviePage(AppPage):
    """
    The search, driven by the URL's query string (`?q=die&genre=action&rating=R`), so a search can
    be bookmarked or shared. The page renders the results for it on the server, so a bookmark
    opens already filled in; after that, the controller searches through the endpoint and
    rewrites the URL to match.
    """

    page_title = 'Find a movie'

    async def set_context(self):
        query = self.request.GET.get('q', '').strip()
        # A value that isn't a choice, from an edited or outdated URL, is treated as "Any".
        genre = self.request.GET.get('genre')
        genre = genre if genre in Genre.values else ''
        rating = self.request.GET.get('rating')
        rating = rating if rating in MovieRating.values else ''

        self.context.data['query'] = query
        self.context.data['genre'] = genre
        self.context.data['rating'] = rating
        self.context.data['genres'] = Genre.choices
        self.context.data['ratings'] = MovieRating.choices
        self.context.children['results'] = MovieResults(
            query=query,
            genre=genre or None,
            rating=rating or None)
