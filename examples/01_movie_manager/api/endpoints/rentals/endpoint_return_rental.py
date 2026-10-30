from django.http import HttpRequest
from django.utils import timezone
from ninja import Schema, Status
from ninja.security import django_auth

from api.endpoints.error_responses import MessageErrorResponseDto
from api.endpoints.rentals import rentals_router
from api.models import Rental


class ReturnRentalResponseDto(Schema):
    # The movie that went back, for the page's confirmation.
    title: str


@rentals_router.post(
    path='/{int:rental_id}/return',
    auth=django_auth,
    url_name='return_rental',
    response={
        200: ReturnRentalResponseDto,
        404: MessageErrorResponseDto,
    })
async def return_rental(
    request: HttpRequest,
    rental_id: int,
) -> Status[ReturnRentalResponseDto | MessageErrorResponseDto]:
    # Only the person who has it can bring it back, so another user's rental is a 404, not a 403
    # that would confirm it exists.
    rental = await (
        Rental.objects
        .filter(id=rental_id, user=request.auth, returned_at__isnull=True)
        .select_related('copy__movie')
        .afirst()
    )
    if rental is None:
        not_found = MessageErrorResponseDto(message="That movie isn't out with you any more.")
        return Status(status_code=404, value=not_found)

    rental.returned_at = timezone.now()
    await rental.asave(update_fields=['returned_at'])
    returned = ReturnRentalResponseDto(title=rental.copy.movie.title)
    return Status(status_code=200, value=returned)
