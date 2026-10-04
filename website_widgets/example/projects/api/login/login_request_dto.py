from dataclasses import dataclass

from website_widgets.example.api.errors import UnprocessableEntityException


@dataclass(kw_only=True)
class LoginRequestDto:
    """The login endpoint's body. Any password is accepted, so none is read."""

    username: str
    next: str = ''

    @classmethod
    def from_dict(cls, data: dict) -> 'LoginRequestDto':
        return cls(
            username=data.get('username'),
            next=data.get('next', ''))

    def validate(self):
        errors = {}
        if not self.username:
            errors['username'] = ['The username is required.']
        elif not isinstance(self.username, str):
            errors['username'] = ['The username must be text.']
        if not isinstance(self.next, str):
            errors['next'] = ['The next URL must be text.']
        if errors:
            raise UnprocessableEntityException(errors)
