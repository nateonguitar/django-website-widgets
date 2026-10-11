# Development Guide

## Setup

The library needs only Python 3.12+ and Poetry. From the repository root:

```bash
poetry install --no-root
```

This creates a virtualenv with Django, at the version pinned in `poetry.lock`. The lock file pins
the development environment only; a project installing the package gets any Django that
`pyproject.toml` allows.

## Tests

```bash
poetry run django-admin test website_widgets --settings=test_settings --pythonpath=.
```

`test_settings.py` sits at the repository root, outside the package, so it never ships. Every test
is a `SimpleTestCase`, so it configures no database. It does configure a `DjangoTemplates` backend,
because widget templates are compiled with `Template()`, which raises `ImproperlyConfigured`
without one. Any project using the library has one already.

GitHub Actions (`.github/workflows/tests.yml`) runs the same command on every push, for each
supported Python against each supported Django. **Supporting a new Django or Python version means
adding it to the matrix and the classifiers in `pyproject.toml` together**, and dropping one means
removing it from both, along with `requires-python` or the `django` requirement when the lowest
version changes.

## Releasing

A change reaches a project using the library only through a published version.

1. Bump `version` in `pyproject.toml`. The `0.x` series allows breaking changes in any release.
2. Run the tests, and check the GitHub Actions matrix is green.
3. Build and publish: `poetry build`, then `poetry publish`. Publishing needs a PyPI token, set
   once with `poetry config pypi-token.pypi <token>`.
4. Tag the release (`git tag v0.2.0`) and push the tag.
5. Bump the requirement in the project using it.

`poetry build` writes the wheel and source archive to `dist/`, which is git-ignored.

## Package structure

```
django-website-widgets/
├── pyproject.toml              # Package metadata and build config
├── poetry.lock                 # The development environment's pins
├── test_settings.py            # Settings for the tests, not shipped
├── .github/workflows/          # The test matrix
├── README.md                   # User documentation (shows on PyPI)
├── DEVELOPMENT.md              # This file
├── LICENSE
├── docs/                       # How the library works internally
└── website_widgets/            # The Python package, and the only thing shipped
    ├── __init__.py             # Exports Widget, Page, WidgetContext, PageRoutes, register_url,
    │                           # reverse_template, NpmWatch, start_npm_watch
    ├── apps.py
    ├── config.py               # WebsiteWidgetsConfig, get_config()
    ├── widget.py
    ├── page.py
    ├── page_routes.py          # @register_url, route discovery, the overlapping-route check
    ├── url_templates.py        # reverse_template()
    ├── npm_watch.py            # start_npm_watch(), for manage.py
    ├── widget_context.py
    ├── tests.py
    └── management/
        └── commands/           # test_website_widgets, show_page_resolve_order
```

## Gotchas

**The distribution and import names differ.** The package is installed as
`django-website-widgets` and imported as `website_widgets`, so `[tool.poetry]` names the package
to include explicitly; without it Poetry looks for a `django_website_widgets` folder and builds an
empty wheel.

**`test_website_widgets` is an installation check, not a test suite.** It confirms the app loads
and, with `--verbose`, prints the exported classes. It never renders a widget.
