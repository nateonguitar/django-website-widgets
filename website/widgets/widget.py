from django.conf import settings
from django.http import HttpRequest
from django.template import Template, Context
from django.utils.safestring import mark_safe, SafeText
import os


class Widget:
    request: HttpRequest

    @classmethod
    def get_styles(cls, folder_path: str) -> list[str]:
        filepath = os.path.join(settings.BASE_DIR, folder_path, 'styles.css')
        if os.path.exists(filepath):
            with open(filepath, 'r') as file:
                return [file.read()]
        return []

    def html(self) -> SafeText:
        return mark_safe('')

    def render_html(self, template_path: str, context: dict = None) -> SafeText:
            context = context or {}
            filepath = os.path.join(settings.BASE_DIR, template_path)
            with open(filepath, 'r') as file:
                template = Template(file.read())
            return template.render(Context(context))
