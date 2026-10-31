from asgiref.sync import sync_to_async
from django.http import HttpRequest
from django.utils import timezone
from ninja import Schema, Status
from ninja.security import django_auth

from api.endpoints.error_responses import MessageErrorResponseDto
from api.endpoints.rentals import rentals_router
from api.models import Rental, User
from website.emails.return_receipt_email import ReturnReceiptEmail


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
    # The person who has it can bring it back, and so can staff, from the Rental admin's Return
    # button. Anyone else's rental is a 404, not a 403 that would confirm it exists.
    rentals = Rental.objects.filter(id=rental_id, returned_at__isnull=True)
    if not request.auth.is_staff:
        rentals = rentals.filter(user=request.auth)
    rental = await rentals.select_related('copy__movie', 'user').afirst()
    if rental is None:
        not_found = MessageErrorResponseDto(message="That movie isn't out with you any more.")
        return Status(status_code=404, value=not_found)

    rental.returned_at = timezone.now()
    await rental.asave(update_fields=['returned_at'])
    # To whoever had it, which isn't the person asking when staff return it.
    await _send_receipt(rental.user, rental)
    returned = ReturnRentalResponseDto(title=rental.copy.movie.title)
    return Status(status_code=200, value=returned)


# Building and sending an email is sync (render() refuses async widgets), so it runs in Django's
# sync thread, as the checkout receipt does.
@sync_to_async
def _send_receipt(user: User, rental: Rental) -> None:
    if not user.email:
        return
    ReturnReceiptEmail(user=user, rental=rental).send()
