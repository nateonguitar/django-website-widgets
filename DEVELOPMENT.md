# Development Guide

## Local Development Setup

The host project installs this package as a path dependency in its own `pyproject.toml`:

```toml
django-website-widgets = {path = "django-website-widgets", develop = true}
```

The host project runs in Docker, with the repository bind-mounted at `/app`, so run Poetry and
`manage.py` through the container:

```bash
docker compose exec api python manage.py test_website_widgets --verbose
```

## Making Changes

Edit files in `django-website-widgets/website_widgets/`. Changes are immediately available because
the package is installed in develop mode from the bind-mounted source.

## Building

```bash
docker compose exec api sh -c "cd django-website-widgets && poetry build"
```

Creates distribution files in `dist/` (git-ignored):
- `django_website_widgets-X.Y.Z-py3-none-any.whl`
- `django_website_widgets-X.Y.Z.tar.gz`

## Publishing to PyPI

```bash
docker compose exec api sh -c "cd django-website-widgets && poetry publish"
```

Requires PyPI credentials configured in Poetry.

## Version Management

1. Edit `version` under `[project]` in `pyproject.toml`
2. Rebuild with `poetry build`
3. Publish with `poetry publish`
4. Tag the release in git, e.g. `v0.2.0`

## Package Structure

```
django-website-widgets/
├── pyproject.toml              # Package metadata and build config
├── MANIFEST.in
├── README.md                   # User documentation (shows on PyPI)
├── DEVELOPMENT.md              # This file
├── LICENSE
├── docs/                       # How the library works internally
└── website_widgets/            # Python package
    ├── __init__.py             # Exports Widget, Page, WidgetContext
    ├── apps.py
    ├── config.py               # WebsiteWidgetsConfig, get_config()
    ├── widget.py
    ├── page.py
    ├── widget_context.py
    ├── tests.py
    ├── management/
    │   └── commands/           # test_website_widgets
    └── example/                # Example pages and widgets
```

## Gotchas

**`pyproject.toml` declares the metadata twice.** Both `[project]` and `[tool.poetry]` set `name`,
`version`, `description`, `readme` and `authors`. Poetry uses `[project]` and ignores the
`[tool.poetry]` copies (`poetry check` warns about each one), so a version bumped only under
`[tool.poetry]` does not change the build.

**`test_website_widgets` is an installation check, not a test suite.** It confirms the app loads
and, with `--verbose`, prints the exported classes. It never renders a widget.
