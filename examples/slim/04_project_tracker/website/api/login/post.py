import dataclasses
from dataclasses import dataclass

from django.contrib.auth import aauthenticate, alogin
from django.contrib.auth.models import AbstractUser
from django.http import JsonResponse
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from website.api.endpoint import Endpoint
from website.api.errors import UnprocessableEntityException


@dataclass(kw_only=True)
class LoginRequestDto:
    """The login endpoint's body."""

    username: str
    password: str
    next: str = ''

    @classmethod
    def from_dict(cls, data: dict) -> 'LoginRequestDto':
        return cls(
            username=data.get('username'),
            password=data.get('password'),
            next=data.get('next', ''))

    def validate(self):
        errors = {}
        if not self.username:
            errors['username'] = ['The username is required.']
        elif not isinstance(self.username, str):
            errors['username'] = ['The username must be text.']
        if not self.password:
            errors['password'] = ['The password is required.']
        elif not isinstance(self.password, str):
            errors['password'] = ['The password must be text.']
        if not isinstance(self.next, str):
            errors['next'] = ['The next URL must be text.']
        if errors:
            raise UnprocessableEntityException(errors)


@dataclass(kw_only=True)
class UserResponseDto:
    id: int
    username: str
    name: str
    is_staff: bool

    @classmethod
    def from_user(cls, user: AbstractUser) -> 'UserResponseDto':
        return cls(
            id=user.pk,
            username=user.username,
            name=user.get_full_name() or user.username,
            is_staff=user.is_staff)


@dataclass(kw_only=True)
class LoginResponseDto:
    """The user now logged in, and the safe URL to go to next."""

    user: UserResponseDto
    next: str

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class LoginPostEndpoint(Endpoint):
    """Logs in with Django's auth, through its async API, and starts a session."""

    method = 'POST'

    async def handle(self):
        request_data = self.read_json()
        dto = LoginRequestDto.from_dict(request_data)
        dto.validate()
        user = await aauthenticate(self.request, username=dto.username, password=dto.password)
        if user is None:
            raise UnprocessableEntityException(errors={
                'password': ["That username and password don't match."],
            })
        await alogin(self.request, user)
        response_dto = LoginResponseDto(
            user=UserResponseDto.from_user(user),
            next=self._safe_next(dto.next))
        response_data = response_dto.to_dict()
        return JsonResponse(response_data)

    @staticmethod
    def _safe_next(next_url: str) -> str:
        """Only a path on this site, so the login can't be used to send someone elsewhere."""
        if next_url.startswith('/') and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
            return next_url
        return reverse('website:ProjectsPage')
