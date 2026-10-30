from django.contrib.auth import alogout
from django.http import HttpRequest
from django.urls import reverse
from ninja import Schema
from ninja.security import django_auth

from api.endpoints.auth import auth_router


class SignOutResponseDto(Schema):
    # Where the page goes once signed out.
    redirect: str


# A POST, never a link: a GET that signs people out could be fired by any page they visit, such
# as an <img> pointing here.
@auth_router.post(
    path='/sign-out',
    auth=django_auth,
    url_name='sign_out',
    response=SignOutResponseDto)
async def sign_out(request: HttpRequest) -> SignOutResponseDto:
    await alogout(request)
    # With one response schema there's one status, 200, so the schema is returned as it is.
    home_page = reverse('website:HomePage')
    return SignOutResponseDto(redirect=home_page)
