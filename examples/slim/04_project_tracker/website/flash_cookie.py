from urllib.parse import unquote

from django.http import HttpRequest, HttpResponse


class FlashCookie:
    """
    A message that survives one navigation: the page's script writes it before leaving, and the
    next page renders it and deletes it. The viewer controls its content, so it is only ever
    rendered autoescaped.
    """

    NAME = 'project_tracker_flash'

    @classmethod
    def read(cls, request: HttpRequest) -> str:
        return unquote(request.COOKIES.get(cls.NAME, ''))[:200]

    @classmethod
    def clear(cls, request: HttpRequest, response: HttpResponse):
        if cls.NAME in request.COOKIES:
            response.delete_cookie(
                cls.NAME,
                path='/',
                samesite='Lax')
