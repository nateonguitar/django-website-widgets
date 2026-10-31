from website_widgets import Widget

from api.models import Genre, Movie, MovieRating
from website.widgets.movie_card import MovieCard


class MovieResults(Widget):
    """
    The movies matching a search, one `MovieCard` each. `FindMoviePage` renders it for the search
    in its URL, and the search endpoint renders it with `arender()` for every search after, so the
    page and the endpoint can't drift apart.
    """

    LIMIT = 50

    def __init__(
        self,
        query: str = '',
        genre: Genre | None = None,
        rating: MovieRating | None = None,
        purpose: str = 'cart'
    ):
        super().__init__()
        self.query = query
        self.genre = genre
        self.rating = rating
        self.purpose = purpose

    async def set_context(self):
        searched = bool(self.query or self.genre or self.rating)
        self.context.data['searched'] = searched
        if not searched:
            self.context.children['cards'] = []
            return

        movies = Movie.objects.with_availability()
        if self.query:
            movies = movies.filter(title__icontains=self.query)
        if self.genre:
            movies = movies.filter(genre=self.genre)
        if self.rating:
            movies = movies.filter(rating=self.rating)
        # Evaluated here with the async ORM: a queryset left for the template would run a sync
        # query inside the async pipeline.
        found = [movie async for movie in movies[:self.LIMIT]]
        self.context.children['cards'] = [
            MovieCard(movie=movie, purpose=self.purpose, key=movie.id) for movie in found
        ]
