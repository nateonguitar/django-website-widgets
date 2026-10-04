import dataclasses
from dataclasses import dataclass

from website_widgets.example.projects.api.login.user_response_dto import UserResponseDto


@dataclass(kw_only=True)
class LoginResponseDto:
    """The user now logged in, and the safe URL to go to next."""

    user: UserResponseDto
    next: str

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)
