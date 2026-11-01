# django-website-widgets (npm)

The frontend half of [django-website-widgets](https://github.com/nateonguitar/django-website-widgets):
the controllers that give server-rendered Django widgets their behaviour. The Python package,
`django-website-widgets` on PyPI, renders the pages and widgets; this package runs in the
browser beside them.

```bash
npm install django-website-widgets
```

A website app created by `python manage.py ww_create_app` depends on it already, at the version
range the installed Python package declares. `python manage.py ww_doctor` says when the two
disagree, and `python manage.py ww_upgrade` sets the range after a Python upgrade.

## What it holds

| Export | Is |
| --- | --- |
| `Controller` | The base class every page and widget controller extends |
| `App` | `App.initController()`, which starts a controller on its element, and the singleton registry |
| `Completer` | A promise resolved from outside, used to signal readiness |

## Use

A controller extends `Controller`:

```ts
import { Controller } from "django-website-widgets";

export class MovieCardController extends Controller {
    public async initState(): Promise<void> {
        // Look elements up inside this.rootElement.
    }

    public setState(): void {
        // Every DOM write.
    }
}
```

The project's `main.ts` re-exports `App` and its controllers, so a template's `<script>` imports
them from the bundle and starts its controller on the root it rendered:

```html
<script type="module">
    import { App, MovieCardController } from '{% static "main.js" %}';
    await App.initController(new MovieCardController(), '.movie-card[data-key="12"]');
</script>
```

A bundle must hold one copy of this package, since `App`'s singleton registry lives on the
class. Depend on it once, in the website app's `package.json`.

The full guide, from the controller lifecycle to the singleton registry, is in the Python
package's docs, which `ww_upgrade` copies into each website app as `website_widgets_docs/`.

## Versions

This package and the Python package are versioned separately: each releases when it changes.
The Python package declares the range of this package it works with. Changes are in
[CHANGELOG.md](CHANGELOG.md).
