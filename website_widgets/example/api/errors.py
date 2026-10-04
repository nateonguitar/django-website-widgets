"""
One exception per HTTP status. `Endpoint.route()` turns any of them into a JSON error response,
and the projects app's base page turns the access ones into its variant templates.
"""


class HttpException(Exception):
    status_code: int | None = None

    def __init__(self, message: str = "Http Exception"):
        super().__init__(message)
        self.message = message


class BadRequestException(HttpException):
    status_code = 400

    def __init__(self, message: str = "Bad Request"):
        super().__init__(message)


class UnauthorizedException(HttpException):
    status_code = 401

    def __init__(self, message: str = 'Unauthorized'):
        super().__init__(message)


class ForbiddenException(HttpException):
    status_code = 403

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message)


class NotFoundException(HttpException):
    status_code = 404

    def __init__(self, message: str = "Not Found"):
        super().__init__(message)


class UnprocessableEntityException(HttpException):
    status_code = 422

    def __init__(self, errors: dict[str, list[str]]):
        super().__init__('Unprocessable Entity')
        self.errors = errors
