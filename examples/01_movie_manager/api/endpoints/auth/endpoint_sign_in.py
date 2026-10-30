from django.contrib.auth import aauthenticate, alogin
from django.http import HttpRequest
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from ninja import Schema, Status
from ninja.utils import check_csrf

from api.endpoints.auth import auth_router
from api.endpoints.error_responses import FieldErrorsResponseDto, MessageErrorResponseDto


# Loose types, checked in the endpoint, so a blank field gets a message for a person rather than
# Ninja's 422 (see CreateMovieRequestDto).
class SignInRequestDto(Schema):
    username: str = ''
    password: str = ''
    # Where the sign-in page was sent from, such as a members-only page's 401.
    next: str = ''


class SignInResponseDto(Schema):
    # Where the page goes next: `next` when it's on this site, otherwise the home page.
    redirect: str


@auth_router.post(
    path='/sign-in',
    url_name='sign_in',
    response={
        200: SignInResponseDto,
        400: FieldErrorsResponseDto,
        401: MessageErrorResponseDto,
        403: MessageErrorResponseDto,
    })
async def sign_in(
    request: HttpRequest,
    dto: SignInRequestDto,
) -> Status[SignInResponseDto | FieldErrorsResponseDto | MessageErrorResponseDto]:
    # Ninja checks the CSRF token only for an endpoint with cookie auth, and nobody is signed in
    # yet, so this one checks it itself.
    if check_csrf(request) is not None:
        out_of_date = MessageErrorResponseDto(message='This page is out of date. Reload it and try again.')
        return Status(status_code=403, value=out_of_date)

    username = dto.username.strip()
    errors = {}
    if not username:
        errors['username'] = 'Enter your username.'
    if not dto.password:
        errors['password'] = 'Enter your password.'
    if errors:
        invalid = FieldErrorsResponseDto(errors=errors)
        return Status(status_code=400, value=invalid)

    # Django doesn't limit how many times someone can guess. A public site adds that itself, with
    # a library such as django-axes or a rate limit in front of this endpoint.
    user = await aauthenticate(request, username=username, password=dto.password)
    if user is None:
        no_match = MessageErrorResponseDto(message="That username and password don't match.")
        return Status(status_code=401, value=no_match)
    await alogin(request, user)

    # A crafted link can carry any next, such as another site's sign-in page made to look like
    # this one, so only a path on this site is followed.
    next_is_safe = url_has_allowed_host_and_scheme(
        dto.next,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure())
    redirect_to = dto.next if next_is_safe else reverse('website:HomePage')
    signed_in = SignInResponseDto(redirect=redirect_to)
    return Status(status_code=200, value=signed_in)
