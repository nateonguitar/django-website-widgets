# Copying the Framework into a Project

`python manage.py init_website_widgets` copies the framework's TypeScript and the package's docs
into the website app's `ts/website_widgets/` folder. Rerunning it after a package upgrade is how a
project takes the new version. Read this before upgrading the package, or when a file in that
folder changed and it isn't clear why.

Primary code:
- `website_widgets.management.commands.init_website_widgets` — the command
- `README.md` in `ts/website_widgets/` — the version it was copied from and the list of files init wrote

## What it writes

Into `<website app>/ts/website_widgets/`, the app being `WebsiteWidgetsConfig.website_app_name`
resolved through the app registry, so it works from any directory:

```
ts/website_widgets/
├── app.ts            App
├── controller.ts     Controller
├── completer.ts      Completer
├── AGENTS.md         the index of these docs
├── docs/             the package's docs, this one included
└── README.md         don't edit; the version and the list of files init wrote
```

The app has to be installed already; the command stops with an error naming the label when it
isn't.

## File by file, never the whole folder

**Each file the package ships is overwritten, and nothing else in the folder is touched.** The
README lists every file init wrote. On the next run, a file on that list that the new version no
longer ships, such as a renamed doc, is deleted. A file that was never on the list, such as one
a developer added, is left alone, and so is a listed path that would reach outside the folder.

Every file is reported as added, changed or removed (the unchanged ones as a count), and the
command suggests committing the folder. Committed, an upgrade shows up as a git diff of exactly
what changed, and a developer who edited a copy anyway sees what init replaced.

**Don't edit the copies.** A project changes behaviour by subclassing `Controller` or `App` in
its own files; see `docs/frontend_controllers.md`.

## The docs read from where they land

The copied docs are written for the project's tree, not the package repo's: a TypeScript file by
its name in this folder, a doc by its path beside `AGENTS.md`, and Python code by its dotted name
(`website_widgets.page.Page`), since the Python half is installed rather than copied. They're in
the project because an installed package may live only inside a container, and an AI assistant
or a person should be able to read them without starting one.

## The docs pointer

After copying, for each file AI coding assistants read instructions from, init asks whether to
append one line pointing them at the copied `AGENTS.md`. It looks for `CLAUDE.md`,
`.claude/CLAUDE.md` (both read by Claude Code) and `AGENTS.md` (read by Codex, Cursor and
others), all relative to the project root, and asks once per file it finds:

```
- `website/ts/website_widgets/AGENTS.md` — how django-website-widgets works; read before changing pages, widgets or controllers
```

The path in the line is relative to the project root in every one of them, `.claude/CLAUDE.md`
included, since that's how paths in these files are read. It doesn't ask when the file already
names that path. When none of the three exists, it offers to create `AGENTS.md` holding just
that line. The default answer is no. This is the only time init
writes outside the folder, and only on a yes.

The project root is `settings.BASE_DIR`, or the current directory without one; `--project-root`
names another.

## Options

- `--noinput` (or `--no-input`) asks nothing and adds no pointer, saying where one is missing.
  The files are still written, since they're the package's.
- `--project-root` is where to look for `CLAUDE.md`, `.claude/CLAUDE.md` and `AGENTS.md`.

Init takes no position on how a project runs its commands. Files it writes belong to whoever ran
it, so a container running as root writes root-owned files; that's the project's to handle.
