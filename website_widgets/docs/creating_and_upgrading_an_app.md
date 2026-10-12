# Creating and Upgrading a Website App

`python manage.py ww_create_app` creates a new website app. `python manage.py ww_upgrade` brings an
existing one's framework files up to the installed package, and is how a project takes a new
version. Both write the app's `ts/website_widgets/` folder the same way. Read this before
creating an app, before upgrading the package, or when a file in that folder changed and it
isn't clear why.

Primary code:
- `website_widgets.management.commands.ww_create_app` and `website_widgets.management.commands.ww_upgrade` — the commands
- `website_widgets.management.framework_folder.FrameworkFolder` — the folder both write, and the system check on it
- `README.md` in `ts/website_widgets/` — the version it was copied from and the list of files the package wrote

## The app's name

**The app is `WebsiteWidgetsConfig.website_app_name`, `website` by default, and `ww_create_app`
takes no name.** The running site reads that setting too: route discovery imports
`<app>/pages/`, decorated pages reverse as `<app>:<name>`, and `start_npm_watch()` runs in the
app's folder. The package supports one website app per project, so an app created under any
other name would never be routed. To use another name, set it in `settings.py` first:

```python
from website_widgets.config import WebsiteWidgetsConfig

WEBSITE_WIDGETS = WebsiteWidgetsConfig(website_app_name='storefront')
```

Without a `WEBSITE_WIDGETS`, `ww_create_app` says it is using the default name, and how to set
another, before it lists anything.

## `ww_create_app`

It lists every file it is about to write, then asks `Create these files? [y/N]`; `--noinput`
writes them without asking. It refuses when the app's folder exists or an app with that label is
installed, pointing at `ww_upgrade` instead. It writes, in the project root:

```
<app>/
├── __init__.py
├── apps.py               the AppConfig, named for the app (WebsiteConfig)
├── pages/__init__.py     where ww_create_page puts pages, and route discovery looks
├── widgets/__init__.py   where ww_create_widget puts widgets
└── ts/website_widgets/   the framework folder, below
```

Then it offers the docs pointer (below) and prints the next steps: the app in `INSTALLED_APPS`,
`path('', PageRoutes.urls())` in `urls.py`, and a page base class at
`<app>.pages.app_page.AppPage` before the first `ww_create_page`.

## `ww_upgrade`

Run it after every upgrade of the package, and once on an app that never ran `ww_create_app`,
such as one a site already had. The app has to be installed; the command stops with an error
naming the label when it isn't. It rewrites the framework folder, reports what changed, and
offers the docs pointer.

**A system check warns when the folder is from another version than the installed package**
(`website_widgets.W001`), read from the README's version stamp, so a project that upgrades the
package and forgets `ww_upgrade` hears about it at the next `runserver`. It's silent when the
app or the folder doesn't exist, since a site may use only the Python half.

## The framework folder

```
ts/website_widgets/
├── app.ts            App
├── controller.ts     Controller
├── completer.ts      Completer
├── AGENTS.md         the index of these docs
├── docs/             the package's docs, this one included
└── README.md         don't edit; the version and the list of files the package wrote
```

**Each file the package ships is overwritten, and nothing else in the folder is touched.** The
README lists every file the package wrote. On the next run, a file on that list that the new
version no longer ships, such as a renamed doc, is deleted. A file that was never on the list,
such as one a developer added, is left alone, and so is a listed path that would reach outside
the folder.

`ww_upgrade` reports every file as added, changed or removed (the unchanged ones as a count),
and suggests committing the folder. Committed, an upgrade shows up as a git diff of exactly what
changed, and a developer who edited a copy anyway sees what was replaced.

**Don't edit the copies.** A project changes behaviour by subclassing `Controller` or `App` in
its own files; see `docs/frontend_controllers.md`.

## The docs read from where they land

The copied docs are written for the project's tree, not the package repo's: a TypeScript file by
its name in this folder, a doc by its path beside `AGENTS.md`, and Python code by its dotted name
(`website_widgets.web_page.WebPage`), since the Python half is installed rather than copied.
They're in the project because an installed package may live only inside a container, and an AI
assistant or a person should be able to read them without starting one.

## The docs pointer

After writing the folder, for each file AI coding assistants read instructions from, both
commands ask whether to append one line pointing them at the copied `AGENTS.md`. They look for
`CLAUDE.md`, `.claude/CLAUDE.md` (both read by Claude Code) and `AGENTS.md` (read by Codex, Cursor
and others), all relative to the project root, and ask once per file found:

```
- `website/ts/website_widgets/AGENTS.md` — how django-website-widgets works; read before changing pages, widgets or controllers
```

The path in the line is relative to the project root in every one of them, `.claude/CLAUDE.md`
included, since that's how paths in these files are read. Neither asks when the file already
names that path. When none of the three exists, they offer to create `AGENTS.md` holding just
that line. The default answer is no. This is the only time either writes outside the app, and
only on a yes.

The project root is `settings.BASE_DIR`, or the current directory without one; `--project-root`
names another.

## Options

- `--noinput` (or `--no-input`): `ww_create_app` writes without asking; neither adds a docs
  pointer, saying where one is missing. `ww_upgrade` still writes the folder, since its files
  are the package's.
- `--project-root`: where `ww_create_app` creates the app, and where both look for `CLAUDE.md`,
  `.claude/CLAUDE.md` and `AGENTS.md`.

The package takes no position on how a project runs its commands. Files they write belong to
whoever ran them, so a container running as root writes root-owned files; that's the project's
to handle.
