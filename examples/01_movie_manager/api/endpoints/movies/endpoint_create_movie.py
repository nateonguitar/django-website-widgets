from datetime import date

from asgiref.sync import sync_to_async
from django.db import transaction
from django.http import HttpRequest
from ninja import Schema, Status
from ninja.security import django_auth

from api.endpoints.error_responses import FieldErrorsResponseDto
from api.endpoints.movies import movies_router
from api.models import Copy, Genre, Movie, MovieRating


# Loose types, checked in the endpoint: a person fills this form in, so each mistake gets a
# message for them, keyed by field for the page. Pydantic constraints here would answer a 422 in
# Ninja's own shape and wording instead. The search endpoint, which only code calls, is strict.
class CreateMovieRequestDto(Schema):
    title: str = ''
    year: int | None = None
    genre: str = ''
    rating: str = ''
    copies: int = 1


class CreateMovieResponseDto(Schema):
    movie_id: int
    title: str


@movies_router.post(
    path='',
    auth=django_auth,
    url_name='create_movie',
    response={
        201: CreateMovieResponseDto,
        400: FieldErrorsResponseDto,
    })
async def create_movie(
    request: HttpRequest,
    dto: CreateMovieRequestDto,
) -> Status[CreateMovieResponseDto | FieldErrorsResponseDto]:
    title = dto.title.strip()
    errors = {}
    if not title:
        errors['title'] = 'Enter a title.'
    if dto.year is None or not 1888 <= dto.year <= date.today().year + 1:
        errors['year'] = 'Enter the year it came out.'
    if dto.genre not in Genre.values:
        errors['genre'] = 'Pick a category.'
    if dto.rating not in MovieRating.values:
        errors['rating'] = 'Pick a rating.'
    if not 1 <= dto.copies <= 20:
        errors['copies'] = 'Between 1 and 20 copies.'
    if not errors and await Movie.objects.filter(title__iexact=title, year=dto.year).aexists():
        errors['title'] = "That movie is already here. Add another copy of it instead."
    if errors:
        invalid = FieldErrorsResponseDto(errors=errors)
        return Status(status_code=400, value=invalid)

    movie = await _create_movie_with_copies(dto, title)
    created = CreateMovieResponseDto(movie_id=movie.id, title=movie.title)
    return Status(status_code=201, value=created)


# transaction.atomic() has no async form, so the two writes run together in Django's sync thread:
# a movie is never saved without its copies.
@sync_to_async
def _create_movie_with_copies(dto: CreateMovieRequestDto, title: str) -> Movie:
    with transaction.atomic():
        movie = Movie.objects.create(
            title=title,
            year=dto.year,
            genre=dto.genre,
            rating=dto.rating)
        Copy.objects.create_copies(movie, dto.copies)
    return movie
