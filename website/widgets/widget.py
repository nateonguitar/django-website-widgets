from django.http import HttpRequest
from django.utils.safestring import SafeText

class Widget:
    request: HttpRequest
    context: dict

    def __init__(self, request: HttpRequest, context: dict = {}):
        self.request = request
        self.context = context

    def styles(self) -> SafeText:
        return SafeText('')
    
    def html(self, request: HttpRequest) -> SafeText:
        return SafeText('')