import json

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.http import HttpRequest, HttpResponse, JsonResponse

from website.api.errors import BadRequestException, HttpException, UnprocessableEntityException


class Endpoint:
    """
    One JSON endpoint: one HTTP method on one URL, one class per file. Plain Django underneath;
    the package only renders pages and widgets, so these could equally be Django Ninja or Django
    REST Framework endpoints.

    Django routes by URL, not method, so `route()` builds the view a URL pattern points at from
    the endpoints sharing that URL.

    An error comes back as `{"error": "<message>"}`, except a validation error, which is a 422
    with `{"errors": {"<field>": ["<message>", ...]}}`.
    """

    method: str

    def __init__(self, request: HttpRequest):
        self.request = request

    async def handle(self, **kwargs) -> HttpResponse:
        raise NotImplementedError

    async def get_viewer(self) -> AbstractBaseUser | AnonymousUser:
        """The logged-in user, or `AnonymousUser`, fetched with the async API."""
        return await self.request.auser()

    def read_json(self, strip_strings: bool = True) -> dict:
        """
        The body as a JSON object. With `strip_strings`, each top-level text value has its
        surrounding whitespace removed.
        """
        body = self.request.body or b'{}'
        try:
            data = json.loads(body)
        except ValueError:
            raise BadRequestException(message='The request body must be JSON.')
        if not isinstance(data, dict):
            raise BadRequestException(message='The request body must be a JSON object.')
        if strip_strings:
            data = {
                key: value.strip() if isinstance(value, str) else value
                for key, value in data.items()
            }
        return data

    @staticmethod
    def error_response(message: str, status: int) -> JsonResponse:
        data = {'error': message}
        return JsonResponse(data, status=status)

    @staticmethod
    def route(*endpoint_classes: type['Endpoint']):
        """The view for one URL, handing each request to the endpoint for its method."""
        endpoints_by_method = {
            endpoint_class.method: endpoint_class
            for endpoint_class in endpoint_classes
        }

        async def view(request: HttpRequest, **kwargs) -> HttpResponse:
            endpoint_class = endpoints_by_method.get(request.method)
            if endpoint_class is None:
                response = Endpoint.error_response(message='Method Not Allowed', status=405)
                allowed_methods = ', '.join(endpoints_by_method)
                response['Allow'] = allowed_methods
                return response
            endpoint = endpoint_class(request)
            try:
                return await endpoint.handle(**kwargs)
            except UnprocessableEntityException as error:
                response_data = {'errors': error.errors}
                return JsonResponse(response_data, status=error.status_code or 422)
            except HttpException as error:
                return Endpoint.error_response(message=error.message, status=error.status_code or 400)

        return view
