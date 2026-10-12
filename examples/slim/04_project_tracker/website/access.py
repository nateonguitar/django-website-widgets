from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from website.api.errors import ForbiddenException, UnauthorizedException


class UserAccessControl:
    """Checks shared by pages and endpoints, so both answer the same request the same way."""

    @staticmethod
    def require_user(user: AbstractBaseUser | AnonymousUser) -> AbstractBaseUser:
        if not user.is_authenticated:
            raise UnauthorizedException()
        return user

    @staticmethod
    def require_staff(user: AbstractBaseUser | AnonymousUser) -> AbstractBaseUser:
        user = UserAccessControl.require_user(user)
        if not user.is_staff:
            raise ForbiddenException()
        return user
