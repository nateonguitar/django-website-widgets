from django.conf import settings
from django.template import Template, Context
from django.utils.safestring import mark_safe, SafeText
import os

class Widget:
    request = None

    def html(self) -> SafeText:
        return mark_safe('')

    def render_html(
            self,
            template_path: str,
            page_context: dict = None) -> SafeText:
        page_context = page_context or {}
        filepath = os.path.join(settings.BASE_DIR, template_path)
        with open(filepath, 'r') as file:
            template = Template(file.read())
        return template.render(Context(page_context))
