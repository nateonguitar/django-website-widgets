# Testing widgets

A test of one widget renders that widget into a small HTML document the test controls, instead
of the whole page that would hold it. The test gets the widget, the chrome it asks for and
nothing else, and can put the widget in states no page happens to produce. Read this before
writing a widget test; a page is still tested through Django's test client, with its real
document.

Primary code:
- `website_widgets.testing` — `WidgetDocumentTestMixin`: `document_template`, `document_children()`,
  `page_context()`, `render_document()`, `arender_document()`

## The mixin

**`WidgetDocumentTestMixin` is a mixin, combined with the Django test class a test already uses,**
so the package never decides whether a test has a database:

```python
from django.test import TestCase
from website_widgets.testing import WidgetDocumentTestMixin


class MovieCardTests(WidgetDocumentTestMixin, TestCase):
    async def test_card__links_to_sign_in__when_signed_out(self):
        html = await self.arender_document(MovieCard(movie=movie, key=movie.id))
        ...
```

It is imported from `website_widgets.testing`, not the package's top level, so production code
never loads it. It builds on `render__test()` / `arender__test()` (`rendering_a_widget_alone.md`)
and imports nothing from `django.test`.

## The document

**The document is itself a widget.** Its template is the class attribute `document_template`,
and its children are `document_children()` plus the widget under test under the key `widget`,
so the template places `{{ children.widget }}` and any other child, such as
`{{ children.appbar }}`, in one widget tree with one mock request. The default document is bare:
`<!DOCTYPE html>`, a `<head>` with charset and viewport, and a `<body>` holding only the widget.
The package can't know a project's stylesheet or script names, so a project's CSS bundle, fonts
or a CDN script go in its own `document_template`, in `<head>` with `{% static %}`
(`{% load static %}` first); there is no special slot.

| Call | Does |
|---|---|
| `self.render_document(widget, user=None, document_children=None, page_context=None)` | the document as HTML, rendered with `render__test()`; every widget in it, document children included, must be a `SyncWidget` |
| `await self.arender_document(...)` | the same through `arender__test()`, for a tree holding any `AsyncWidget` |

**`document_children` and `page_context` merge over the hooks of the same name,** the call's
keys winning, and default to `None`. A document child named `widget` raises `ValueError`. A
child set to `None` renders nothing, as anywhere in a tree.

**`page_context(user)` is the document's `context.page`.** The document is the root, so its
`context.page` is the dict shared down the tree, replacing any set on the widget under test:
writing `widget.context.page[...]` before the render raises `RuntimeError`, as it would for any
child. The hook receives the render's `user` (or `None`), so a project whose page base puts the
user in `context.page` does the same there, and every widget reading `page.user` sees what it
would on a page.

**A document with async chrome means `arender_document()` throughout.** `render()` refuses an
`async def set_context()` anywhere in the tree, so once a project's document holds an
`AsyncWidget` (an appbar loading the user's notifications, say), a test of even a `SyncWidget`
awaits `arender_document()`. Data the widget takes through its constructor is then queried with
the async ORM before the call.

## A project's own document

A project subclasses the mixin once, with its document and the values its page base supplies,
and its widget tests inherit that class. The movie manager's
`website/tests/app_widget_test_case.py` is the worked example:

- `AppWidgetTestCase(WidgetDocumentTestMixin, TestCase)`, the combined class every widget test uses;
- `document_template` with the site's stylesheet and the `AppState` script from its real
  document template, but no `<title>` or favicon, which only a page has;
- `document_children()` returning `AppPage.document_widgets()`, a static method the page base
  also calls, so a widget test holds the same appbar, `AppUrls` and dialog `<template>`s as a page
  and the two can't drift;
- `page_context(user)` with what `AppPage.handle_request()` puts in `context.page`: the user,
  site name, CSRF token and theme.

## Where a test lives

**Anywhere.** Django's runner discovers `test*.py` in any package, a widget's folder included, so
the package requires no placement. The movie manager shows both: a test of one widget sits beside
it (`widgets/movie_card/test_movie_card.py`), and page tests, and tests of several widgets
together, stay in `website/tests/`.
