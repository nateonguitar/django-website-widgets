from website_widgets.example.api.errors import ForbiddenException, UnauthorizedException
from website_widgets.example.projects.store import User


class UserAccessControl:
    """Checks shared by pages and endpoints, so both answer the same request the same way."""

    @staticmethod
    def require_user(user: User | None) -> User:
        if user is None:
            raise UnauthorizedException()
        return user

    @staticmethod
    def require_admin_user(user: User | None) -> User:
        user = UserAccessControl.require_user(user)
        if not user.is_admin:
            raise ForbiddenException()
        return user
