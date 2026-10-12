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

## Examples

`examples/` holds small Django projects that show the library in use, grouped by what they need
to run and numbered in reading order. `slim/` needs only Poetry: static CSS and JavaScript files,
and each widget's behaviour inline. `examples/README.md` is the reader's index; keep it in step
when one is added.

- **Each is its own project:** its own `manage.py`, settings and `pyproject.toml`, so one folder
  copies out as the start of someone's site. Each depends on the package by relative path,
  `django-website-widgets = {path = "../../..", develop = true}`, so it runs the code in this
  checkout, and a package change shows up in every example at once.
- **They run on models and SQLite**, seeded by a data migration, so `migrate` alone gives a
  working site and every test starts from the same rows. `db.sqlite3` is git-ignored.
- **Run one:** `cd examples/slim/01_pages_and_widgets`, `poetry install`,
  `poetry run python manage.py migrate`, then `runserver` or `test`.
- **CI runs every example's tests**, finding each folder with a `manage.py`, so a new example needs
  no workflow edit. An example that a package change breaks fails the build like a package test.
- **They never ship.** `exclude` in `[tool.poetry]` keeps `examples/` out of the wheel and the
  source archive.

## Releasing

A change reaches a project using the library only through a published version.

1. Bump `version` in `pyproject.toml`. The `0.x` series allows breaking changes in any release.
2. Run the tests, and check the GitHub Actions matrix is green.
3. Build with `poetry build`, then check that nothing but the package ships: both commands must
   print nothing.
   ```bash
   unzip -Z1 dist/*.whl | grep -vE '^website_widgets/|\.dist-info/' ; unzip -Z1 dist/*.whl | grep '/tests/'
   tar tzf dist/*.tar.gz | sed 's|^[^/]*/||' | grep -vE '^(website_widgets/|$|README.md|LICENSE|pyproject.toml|PKG-INFO)' ; tar tzf dist/*.tar.gz | grep -E '/tests/|/examples/'
   ```
   `exclude` in `[tool.poetry]` keeps `website_widgets/tests/` and `examples/` out.
4. Publish with `poetry publish`. Publishing needs a PyPI token, set once with
   `poetry config pypi-token.pypi <token>`.
5. Tag the release (`git tag v0.2.0`) and push the tag.
6. Bump the requirement in the project using it.

`poetry build` writes the wheel and source archive to `dist/`, which is git-ignored.

## Package structure

```
django-website-widgets/
├── pyproject.toml              # Package metadata and build config
├── poetry.lock                 # The development environment's pins
├── test_settings.py            # Settings for the tests, not shipped
├── .github/workflows/          # The test matrix and the examples' tests
├── examples/                   # Runnable example projects, not shipped; see "Examples"
├── README.md                   # The introduction (shows on PyPI), linking to the docs
├── DEVELOPMENT.md              # This file
├── LICENSE
└── website_widgets/            # The Python package, the only thing shipped (minus tests/)
    ├── AGENTS.md               # The index of docs/ and the rules every change follows
    ├── docs/                   # How each part works, and why
    ├── frontend/               # The framework TypeScript and its README, which
    │                           # ww_create_app and ww_upgrade copy into a project
    ├── generator_templates/    # ww_create_page's and ww_create_widget's default templates (*.tmpl)
    ├── __init__.py             # Exports Widget, WebPage, WidgetContext, PageRoutes, register_url,
    │                           # reverse_template, NpmWatch, start_npm_watch
    ├── apps.py
    ├── config.py               # WebsiteWidgetsConfig, GenerateComponentConfig, get_config()
    ├── widget.py
    ├── web_page.py
    ├── page_routes.py          # @register_url, route discovery, the overlapping-route check
    ├── url_templates.py        # reverse_template()
    ├── npm_watch.py            # start_npm_watch(), for manage.py
    ├── widget_context.py
    ├── tests/                  # One test class per file, not shipped; see "Tests" above
    └── management/
        ├── framework_folder.py # FrameworkFolder: the copied ts/website_widgets/, and its
        │                       # out-of-date system check
        ├── component_files.py  # ComponentFiles: the file work ww_create_page and ww_create_widget
        │                       # both call; each command's own handle() reads top to bottom
        └── commands/           # ww_create_app, ww_upgrade, ww_create_page, ww_create_widget,
                                # ww_show_routes
```

## Docs

**The docs live inside the Python package,** in `website_widgets/docs/`, so they ship in the wheel
and a project's installed copy carries the docs for its version. `website_widgets/AGENTS.md`
indexes them, one line per doc, and `tests/test_agents_md.py` fails when a doc has no index line
or an index line names a doc that doesn't exist. A new doc gets its line in the same change, and
a README section that grows past an introduction moves into a doc with a link left behind. The
README's links are absolute GitHub URLs, since PyPI shows the README but not the files beside it.

**`ww_create_app` and `ww_upgrade` copy `AGENTS.md` and `docs/` into projects as they are,** so
they're written for where they land: a TypeScript file by its name, a doc by its path beside
`AGENTS.md`, and Python by its dotted name (`website_widgets.web_page`), never a repo path like
`website_widgets/web_page.py`. `frontend/README.md` is the one template: `FrameworkFolder` fills
in its `{version}` and `{file_list}`, and the out-of-date check reads the version back, so keep
its "Copied from django-website-widgets {version} by" line.

**`generator_templates/` holds no project opinions**: no logging, no nonce, no HTTP client.
`tests/test_generator_templates.py` fails when one creeps in. They're named `*.tmpl`
and kept out of a `templates/` folder, so neither Python tooling nor Django's template loader
mistakes them for real files.

**The framework TypeScript in `frontend/` is the source of truth.** Gametabs and every other
project get it through `ww_create_app` and then `ww_upgrade`; a change is made here and reaches
them in a release.

**Every command is `ww_`-prefixed, and `ww_create_*` is the one verb for writing new files.**
A new command follows both, so `manage.py help`'s list and a project's shell history say where a
command comes from.

## Gotchas

**The distribution and import names differ.** The package is installed as
`django-website-widgets` and imported as `website_widgets`, so `[tool.poetry]` names the package
to include explicitly; without it Poetry looks for a `django_website_widgets` folder and builds an
empty wheel.
