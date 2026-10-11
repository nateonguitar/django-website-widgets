# website_widgets frontend framework

Copied from django-website-widgets {version} by `python manage.py init_website_widgets`.

**Don't edit the files init wrote here** (listed below). They belong to the
`django-website-widgets` package, and rerunning `init_website_widgets` after an upgrade overwrites
them. Commit this folder, so an upgrade shows up as a diff of exactly what changed.

To change how something here behaves, subclass it in your own code: extend `Controller` for a
controller, or subclass `App` and use your subclass. Keep project state, such as the logged-in
user or feature flags, in your own classes rather than on `App`.

| File | Holds |
| --- | --- |
| `app.ts` | `App`: `initializeController()` and the singleton registry |
| `controller.ts` | `Controller`, the base class every page and widget controller extends |
| `completer.ts` | `Completer`, a promise resolved from outside, used to signal readiness |
| `AGENTS.md` | The index of the package's docs, in `docs/`, and the rules every change follows |

Files init wrote, which a rerun overwrites, or deletes once the package stops shipping them:

<!-- website_widgets:files -->
{file_list}
<!-- /website_widgets:files -->
