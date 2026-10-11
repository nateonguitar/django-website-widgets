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

**One test class per file, named for what it tests.** A class's tests sit in a folder named for
the module (`tests/widget/test_render.py` for `Widget.render()`,
`tests/page_routes/test_register_url.py`); a module with one test class keeps a flat
`tests/test_<module>.py`. Test names follow `test_<feature>__<succeeds/fails>__when_<condition>`.
The shared pieces sit beside the tests:

- `tests/sample_widgets.py`: the widgets and pages the tests render.
- `tests/widget_test_case.py`: `WidgetTestCase.write_template()`, which writes a test's template
  beside `sample_widgets.py`, since a widget's template is looked up beside its class's module.
- `tests/urls.py`: the URLconf `reverse_template()` is tested against, also `ROOT_URLCONF`.
- `tests/page_routes/page_routes_test_case.py`: an empty route registry and a throwaway website
  app for each test.

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
├── README.md                   # The introduction (shows on PyPI), linking to the docs
├── DEVELOPMENT.md              # This file
├── LICENSE
└── website_widgets/            # The Python package, and the only thing shipped
    ├── AGENTS.md               # The index of docs/ and the rules every change follows
    ├── docs/                   # How each part works, and why
    ├── frontend/               # The framework TypeScript and its README, which
    │                           # init_website_widgets copies into a project
    ├── generator_templates/    # generate_component's default templates (*.tmpl)
    ├── __init__.py             # Exports Widget, Page, WidgetContext, PageRoutes, register_url,
    │                           # reverse_template, NpmWatch, start_npm_watch
    ├── apps.py
    ├── config.py               # WebsiteWidgetsConfig, GenerateComponentConfig, get_config()
    ├── widget.py
    ├── page.py
    ├── page_routes.py          # @register_url, route discovery, the overlapping-route check
    ├── url_templates.py        # reverse_template()
    ├── npm_watch.py            # start_npm_watch(), for manage.py
    ├── widget_context.py
    ├── tests/                  # One test class per file; see "Tests" above
    └── management/
        └── commands/           # test_website_widgets, show_page_resolve_order,
                                # init_website_widgets, generate_component
```

## Docs

**The docs live inside the Python package,** in `website_widgets/docs/`, so they ship in the wheel
and a project's installed copy carries the docs for its version. `website_widgets/AGENTS.md`
indexes them, one line per doc, and `tests/test_agents_md.py` fails when a doc has no index line
or an index line names a doc that doesn't exist. A new doc gets its line in the same change, and
a README section that grows past an introduction moves into a doc with a link left behind. The
README's links are absolute GitHub URLs, since PyPI shows the README but not the files beside it.

**`init_website_widgets` copies `AGENTS.md` and `docs/` into projects as they are,** so they're
written for where they land: a TypeScript file by its name, a doc by its path beside
`AGENTS.md`, and Python by its dotted name (`website_widgets.page`), never a repo path like
`website_widgets/page.py`. `frontend/README.md` is the one template: init fills in its
`{version}` and `{file_list}`.

**`generator_templates/` holds no project opinions**: no logging, no nonce, no HTTP client.
`tests/commands/test_generate_component.py` fails when one creeps in. They're named `*.tmpl`
and kept out of a `templates/` folder, so neither Python tooling nor Django's template loader
mistakes them for real files.

**The framework TypeScript in `frontend/` is the source of truth.** Gametabs and every other
project get it by running init; a change is made here and reaches them in a release.

## Gotchas

**The distribution and import names differ.** The package is installed as
`django-website-widgets` and imported as `website_widgets`, so `[tool.poetry]` names the package
to include explicitly; without it Poetry looks for a `django_website_widgets` folder and builds an
empty wheel.

**`test_website_widgets` is an installation check, not a test suite.** It confirms the app loads
and, with `--verbose`, prints the exported classes. It never renders a widget.
