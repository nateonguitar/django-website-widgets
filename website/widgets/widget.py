from django.http import HttpRequest
from django.utils.safestring import mark_safe, SafeText

class Widget:
    request: HttpRequest
    context: dict

    def __init__(self, request: HttpRequest, context: dict = {}):
        self.request = request
        self.context = context

    def html(self, request: HttpRequest) -> SafeText:
        return mark_safe('')
