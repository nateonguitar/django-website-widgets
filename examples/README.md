# Examples

Django projects you can run, showing django-website-widgets in use. They're not part of the
package: clone the repository to use them. Each runs the package from this repository, so it
always shows the current code, and each has its own README with how to run it and where to look.

```bash
git clone https://github.com/nateonguitar/django-website-widgets.git
cd django-website-widgets/examples/01_movie_manager
```

| Project | Shows |
| --- | --- |
| [`01_movie_manager`](01_movie_manager) | **The main example**, a whole site built the way the package means one to be: created by `ww_create_app`, every page and widget started by `ww_create_page` and `ww_create_widget`, TypeScript controllers, SCSS and webpack. A family's shared movie shelf with sign-in, search answered with widget HTML from `arender()`, a cart in `localStorage`, all-or-nothing checkout, and a Django Ninja API. Needs Node and `npm install` as well as Poetry. |
| [`02_animal_shelter`](02_animal_shelter) | The no-build alternative, kept tiny: one page of composed widgets, a static CSS file and an inline `<script>`. Needs only Poetry. |

Techniques too narrow for either, such as widgets in a plain Django view, HTML emails, or a 304
from a page, are lessons in the package's docs, indexed by
[`website_widgets/docs/AGENTS.md`](../website_widgets/docs/AGENTS.md).

For a real project built on the package, see [Gametabs](https://gametabs.net).
