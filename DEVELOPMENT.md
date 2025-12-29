# Development Guide

## Local Development Setup

This package is installed in the main project via Poetry:

```bash
cd /app
poetry add --editable ./django-website-widgets
```

## Making Changes

Edit files in `/app/django-website-widgets/website_widgets/`. Changes are immediately available since it's installed in editable mode.

## Reinstalling After Structural Changes

If changes don't appear:

```bash
cd /app
poetry remove django-website-widgets
poetry add --editable ./django-website-widgets
```

## Building

```bash
cd /app/django-website-widgets
poetry build
```

Creates distribution files in `dist/`:
- `django_website_widgets-X.Y.Z-py3-none-any.whl`
- `django-website-widgets-X.Y.Z.tar.gz`

## Publishing to PyPI

```bash
cd /app/django-website-widgets
poetry publish
```

Requires PyPI credentials configured in Poetry.

## Version Management

1. Edit version in `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

2. Rebuild:
   ```bash
   poetry build
   ```

3. Publish:
   ```bash
   poetry publish
   ```

4. Tag in git:
   ```bash
   git tag -a v0.2.0 -m "Release 0.2.0"
   git push origin v0.2.0
   ```

## Package Structure

```
django-website-widgets/
├── pyproject.toml              # Poetry config
├── README.md                   # User documentation (shows on PyPI)
├── DEVELOPMENT.md              # This file
├── LICENSE
└── website_widgets/            # Python package
    ├── __init__.py
    ├── apps.py
    ├── widget.py
    ├── page.py
    ├── widget_context.py
    ├── management/
    │   └── commands/
    └── example/
```
