from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from website_widgets.testing import WidgetDocumentTestMixin

from website.pages.app_page import AppPage


class AppWidgetTestCase(WidgetDocumentTestMixin, TestCase):
    """
    Renders one widget the way a page of this site would hold it, without the page: the
    stylesheet, `AppUrls` and `AppState` that every controller relies on, the appbar a card's
    controller tells about the cart, and the confirm dialog's `<template>`. What's left out is
    what only a page has: its `<title>`, its favicon, its own content.

    `render_document()` / `arender_document()` take the widget and the user, and `page_context()`
    puts that user in `context.page` as `AppPage.handle_request()` does, so a widget reading
    `page.user` sees the same thing it would on a page.
    """

    document_template = """{% load static %}
<!DOCTYPE html>
<html lang="en"
      data-theme="{{ page.theme }}">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet"
          href="{% static 'bundled-styles.css' %}">
  </head>
  <body>
    {{ children.app_urls }}
    <script type="module">
      import { AppState } from '{% static "main.js" %}';
      AppState.siteName = '{{ page.site_name|escapejs }}';
      AppState.csrfToken = '{{ page.csrf_token|escapejs }}';
      {% if page.user.is_authenticated %}
      AppState.user = {
        id: {{ page.user.id }},
        username: '{{ page.user.username|escapejs }}',
      };
      {% endif %}
    </script>
    {{ children.appbar }}
    {{ children.widget }}
    {{ children.confirm_dialog }}
  </body>
</html>
"""

    # Any non-empty value: the test client and the browser tier's routed requests skip CSRF checks.
    CSRF_TOKEN = 'test-csrf-token'

    def document_children(self) -> dict:
        return AppPage.document_widgets()

    def page_context(self, user) -> dict:
        return {
            'user': user if user is not None else AnonymousUser(),
            'site_name': AppPage.SITE_NAME,
            'csrf_token': self.CSRF_TOKEN,
            'theme': 'system',
        }
