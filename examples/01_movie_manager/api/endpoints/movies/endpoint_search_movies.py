import asyncio
from typing import Literal

from django.http import HttpRequest, HttpResponse

from api.endpoints.movies import movies_router
from api.models import Genre, MovieRating
from website.widgets.movie_results import MovieResults


SEARCH_DELAY_SECONDS = 0.5


# Strict types: only a controller builds these parameters, from the form's own options, so a value
# outside them is a bug, and Ninja's automatic 422 is the right answer.
@movies_router.get(
    path='/search',
    url_name='search_movies',
    # No response schema, since a schema describes JSON. Ninja passes a returned HttpResponse
    # through as it is, so this only tells the API docs what comes back.
    openapi_extra={
        'responses': {
            200: {
                'description': "The MovieResults widget's HTML",
                'content': {'text/html': {'schema': {'type': 'string'}}},
            },
        },
    })
async def search_movies(
    request: HttpRequest,
    q: str = '',
    genre: Genre | None = None,
    rating: MovieRating | None = None,
    # 'cart' cards add to the cart; 'choose' cards pick a movie for the add-to-inventory page.
    purpose: Literal['cart', 'choose'] = 'cart',
) -> HttpResponse:
    """
    Answers with HTML, not JSON: the result cards are the same `MovieCard` widgets a page would
    render, so their markup lives in one template.
    """
    # A local SQLite search answers almost at once, so the spinner the page shows in place of
    # the results would only flicker. Held back a little, it shows the way it would on a real
    # server.
    await asyncio.sleep(SEARCH_DELAY_SECONDS)
    results = MovieResults(
        query=q.strip(),
        genre=genre,
        rating=rating,
        purpose=purpose)
    # There's no page here, so the endpoint fills context.page itself, before rendering, and
    # every card reads it.
    results.context.page['user'] = await request.auser()
    html = await results.arender(request)
    return HttpResponse(html)
