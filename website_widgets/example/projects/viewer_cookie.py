from django.http import HttpRequest, HttpResponse

from website_widgets.example.projects.store import Store, User


class ViewerCookie:
    """
    The fake login: a plain cookie holding a user id, which anyone can edit in their browser. It
    stands in for whatever authentication a real site uses and is not authentication.
    """

    NAME = 'website_widgets_example_user'

    @classmethod
    def viewer(cls, request: HttpRequest) -> User | None:
        raw_id = request.COOKIES.get(cls.NAME, '')
        if not raw_id.isdigit():
            return None
        return Store.find_user(int(raw_id))

    @classmethod
    def set(cls, response: HttpResponse, user: User):
        response.set_cookie(
            cls.NAME,
            str(user.id),
            path='/',
            httponly=True,
            samesite='Lax')

    @classmethod
    def clear(cls, response: HttpResponse):
        response.delete_cookie(
            cls.NAME,
            path='/',
            samesite='Lax')
