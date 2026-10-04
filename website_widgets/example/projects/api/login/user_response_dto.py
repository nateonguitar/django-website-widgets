from dataclasses import dataclass

from website_widgets.example.projects.store import User


@dataclass(kw_only=True)
class UserResponseDto:
    id: int
    username: str
    name: str
    is_admin: bool

    @classmethod
    def from_user(cls, user: User) -> 'UserResponseDto':
        return cls(
            id=user.id,
            username=user.username,
            name=user.name,
            is_admin=user.is_admin)
