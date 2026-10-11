# Routing Pages

How a page reaches a URL: declared on its class with `@register_url` and found by route
discovery, or listed by hand in `urls.py`. Read this before adding a page, renaming a route, or
when a URL goes to the wrong page.

Primary code:
- `website_widgets.page_routes` — `PageRoutes`: `register_url()`, `urls()`, discovery, the
  ordering key, `check_for_ties()`
- `website_widgets.management.commands.show_page_resolve_order` — the order and reachability
  report
- `website_widgets.page` — `Page.as_view()`, which both kinds of route call

## Two ways to route a page

**By hand**, like any Django view. The page can live anywhere, and its name is whatever
`urls.py` gives it:

```python
path('projects/', ProjectsPage.as_view(), name='projects')
```

**With `@register_url`**, which takes `path()`'s arguments and stacks one per route:

```python
from website_widgets import register_url

@register_url('')
class HomePage(AppPage): ...

@register_url('forum/<int:post_id>', name='forum_post')
@register_url('tab-requests/<int:post_id>', name='tab_request')
class ForumPostPage(AppPage): ...

@register_url('forum/create-post', name='forum_create_post', kwargs={'post_type': 'forum_post'})
class ForumCreatePostPage(AppPage): ...
```

`urls.py` then includes every decorated page in one line, the way the admin is included:

```python
from website_widgets import PageRoutes

urlpatterns = [
    path('', PageRoutes.urls()),
    ...
]
```

The two mix freely. A decorated route is an ordinary `path()`, so `reverse()`, `{% url %}`,
`resolve()` and URL tools such as django-extensions' `show_urls` all see it. A page without a
decorator is never routed automatically, which is what keeps base classes such as a project's
`AppPage` off the URL list.

The decorator checks when the class is defined: it raises `TypeError` on a class that isn't a
`Page`, and `ImproperlyConfigured` on a route name already registered. Its `kwargs` reach the
page's constructor alongside the URL's parameters, through `as_view()`, so one class can serve
variants of a route without wrapper functions.

## Discovery

**`PageRoutes.urls()` imports every module under the website app's `pages/` folder** before
building the URL patterns, the app being `WebsiteWidgetsConfig.website_app_name` (default
`'website'`), resolved through the app registry. A decorator only runs when its module is
imported, so this is the same trick as the admin importing each app's `admin` module. A
decorated page outside that folder is never found, and nothing reports it.

Discovery runs when `urls.py` loads. **A page module that calls `reverse()` at import time
fails**, since the URLs it would reverse are still being built. Reverse inside `set_context()`
or a method instead.

## Names and the namespace

Decorated routes live in a namespace named after the website app, like Django Ninja's
`api-1.0.0:`. `name` is optional and defaults to the class name, so `HomePage` reverses as
`reverse('website:HomePage')`, and `forum_post` as `reverse('website:forum_post')`. A
hand-routed page's name sits outside the namespace, so a project can tell the two apart by the
prefix. `resolve().url_name` drops the namespace; compare `view_name` when matching a resolved
page.

## Order

**Routes are tried most specific first, never in file or import order.** They are compared
segment by segment: a fixed segment comes before an `int` parameter, then `uuid`, `slug`, `str`
and `path`. A converter the package doesn't know, such as a project's own, ranks with `str`.
When one route continues past where another ends, the longer one is tried first, which only
matters when a `path` parameter could swallow the extra segments. Equally specific routes fall
back to alphabetical order by route string.

So `profile/settings` is always tried before `profile/<str:username>`, wherever either is
declared, which is the order most web routers use. Import order would make the winner depend on
file names.

**A system check fails on a true tie** (`website_widgets.E001`): two equally specific routes
that can match the same URL, such as `a/<str:x>` and `a/<str:y>`. It knows each converter's
pattern, so `forum/create-post` and `forum/<int:post_id>` don't count as overlapping.

## Checking the order

`show_page_resolve_order` lists the decorated routes in the order they are tried:

```
$ python manage.py show_page_resolve_order
#   URL                                              Segments  Page
1   /moderation/reports/<int:report_id>              f/f/i     ViewReportPage
...
15  /profile/<str:username>                          f/s       UserProfilePage
...
17  /                                                f         HomePage

Segments: f fixed, i int, s str, g slug, u uuid, p path, and a project converter by its name.
All 37 page routes reach their page.
```

For each route it reverses a sample URL (`/profile/a`) and resolves it through the whole
project, so it also catches a route that never reaches its page because something earlier in
`urls.py` takes its URLs, such as a hand-written route or a catch-all, or because
`PageRoutes.urls()` isn't included. A route that fails prints in red with the reason, and the
command exits non-zero, so it can run in CI.

- `--columns` picks the columns after `#`, in order, from `url,segments,name,page,reaches_page`
  (default `url,segments,page`). The reachability check runs either way.
- `--path-param-type` shows a path parameter as declared (`full`, the default:
  `<str:game_slug>`), as its converter (`type`: `<str>`) or as the sample value the check uses
  (`example`: `a`).

It only knows about decorated routes. For every route in the project, hand-routed pages and
plain views included, use django-extensions' `show_urls`.
