from django.http import HttpRequest
from ninja import Schema, Status
from ninja.security import django_auth

from api.endpoints.error_responses import FieldErrorsResponseDto, MessageErrorResponseDto
from api.endpoints.movies import movies_router
from api.models import Copy, Movie


# A loose type, checked in the endpoint, so an out-of-range count gets a message for a person
# rather than Ninja's 422 (see CreateMovieRequestDto).
class AddCopiesRequestDto(Schema):
    copies: int = 1


class AddCopiesResponseDto(Schema):
    title: str
    total_copies: int


@movies_router.post(
    path='/{int:movie_id}/copies',
    auth=django_auth,
    url_name='add_copies',
    response={
        201: AddCopiesResponseDto,
        400: FieldErrorsResponseDto,
        404: MessageErrorResponseDto,
    })
async def add_copies(
    request: HttpRequest,
    movie_id: int,
    dto: AddCopiesRequestDto,
) -> Status[AddCopiesResponseDto | FieldErrorsResponseDto | MessageErrorResponseDto]:
    movie = await Movie.objects.filter(id=movie_id).afirst()
    if movie is None:
        not_found = MessageErrorResponseDto(message='That movie is gone. Search for it again.')
        return Status(status_code=404, value=not_found)
    if not 1 <= dto.copies <= 20:
        errors = FieldErrorsResponseDto(errors={'copies': 'Between 1 and 20 copies.'})
        return Status(status_code=400, value=errors)

    new_copies = [Copy(movie=movie) for _ in range(dto.copies)]
    await Copy.objects.abulk_create(new_copies)
    total = await movie.copies.acount()
    added = AddCopiesResponseDto(title=movie.title, total_copies=total)
    return Status(status_code=201, value=added)
