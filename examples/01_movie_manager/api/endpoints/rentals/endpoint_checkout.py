from dataclasses import dataclass, field

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef
from django.http import HttpRequest
from ninja import Schema, Status
from ninja.security import django_auth

from api.endpoints.error_responses import MessageErrorResponseDto
from api.endpoints.rentals import rentals_router
from api.models import Copy, Rental, User
from website.emails.checkout_receipt_email import CheckoutReceiptEmail


class CheckoutRequestDto(Schema):
    movie_ids: list[int] = []


class CheckoutResponseDto(Schema):
    rental_ids: list[int]


class CheckoutConflictResponseDto(Schema):
    message: str
    # The cart page marks these, and offers to take the rest.
    unavailable_movie_ids: list[int]


@dataclass
class CheckoutOutcome:
    rental_ids: list[int] = field(default_factory=list)
    # Movies with no copy left on the shelf, because someone else took the last one while it sat
    # in this cart.
    unavailable_movie_ids: list[int] = field(default_factory=list)


@rentals_router.post(
    path='/checkout',
    auth=django_auth,
    url_name='checkout',
    response={
        200: CheckoutResponseDto,
        400: MessageErrorResponseDto,
        409: CheckoutConflictResponseDto,
    })
async def checkout(
    request: HttpRequest,
    dto: CheckoutRequestDto,
) -> Status[CheckoutResponseDto | MessageErrorResponseDto | CheckoutConflictResponseDto]:
    movie_ids = list(dict.fromkeys(dto.movie_ids))
    if not movie_ids:
        empty = MessageErrorResponseDto(message='Your cart is empty.')
        return Status(status_code=400, value=empty)

    outcome = await _take_a_copy_of_each(request.auth, movie_ids)
    if outcome.unavailable_movie_ids:
        conflict = CheckoutConflictResponseDto(
            message="Someone took the last copy of something in your cart. Nothing was recorded.",
            unavailable_movie_ids=outcome.unavailable_movie_ids)
        return Status(status_code=409, value=conflict)
    await _send_receipt(request.auth, outcome.rental_ids)
    taken = CheckoutResponseDto(rental_ids=outcome.rental_ids)
    return Status(status_code=200, value=taken)


# All or nothing, in one transaction: either every movie in the cart is recorded as taken, or
# none is and the 409 says which ran out. transaction.atomic() has no async form, so this runs
# in Django's sync thread.
@sync_to_async
def _take_a_copy_of_each(user: User, movie_ids: list[int]) -> CheckoutOutcome:
    outcome = CheckoutOutcome()
    # Not .exclude(rentals__returned_at__isnull=True): across a relation, isnull=True also
    # matches a copy with no rentals at all, so a copy nobody ever took would look taken.
    is_out = Exists(Rental.objects.filter(copy=OuterRef('pk'), returned_at__isnull=True))
    with transaction.atomic():
        for movie_id in movie_ids:
            copy = Copy.objects.filter(~is_out, movie_id=movie_id).first()
            if copy is None:
                outcome.unavailable_movie_ids.append(movie_id)
                continue
            try:
                # A savepoint, so a lost race leaves the outer transaction usable.
                with transaction.atomic():
                    rental = Rental.objects.create(copy=copy, user=user)
            except IntegrityError:
                # Another checkout took this copy between the lookup and the insert, and the
                # one-open-rental-per-copy constraint refused the second.
                outcome.unavailable_movie_ids.append(movie_id)
                continue
            outcome.rental_ids.append(rental.id)
        if outcome.unavailable_movie_ids:
            transaction.set_rollback(True)
            outcome.rental_ids = []
    return outcome


# Building and sending an email is sync (render() refuses async widgets), so it runs in Django's
# sync thread. A public site would hand this to a task queue, so a slow mail server never holds
# up the checkout.
@sync_to_async
def _send_receipt(user: User, rental_ids: list[int]) -> None:
    if not user.email:
        return
    rentals = Rental.objects.filter(id__in=rental_ids).select_related('copy__movie').order_by('copy__movie__title')
    CheckoutReceiptEmail(user=user, rentals=list(rentals)).send()
