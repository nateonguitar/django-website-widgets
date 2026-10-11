# URL Templates for the Frontend

`reverse_template()` stands in for `reverse()` when the frontend fills in a URL's parameters:
it turns a URL name into a template such as `/posts/{post_id}`. Read this before handing a URL
to TypeScript, or when a placeholder comes out wrong.

Primary code:
- `website_widgets/url_templates.py` — `reverse_template()`

## What it returns

```python
from website_widgets import reverse_template

# path('projects/<int:project_id>/tasks/<slug:task_slug>', ..., name='project_task')
reverse_template('project_task')   # '/projects/{project_id}/tasks/{task_slug}'
reverse_template('project_list')   # '/projects', as reverse() returns it
```

A placeholder per route parameter, named after the parameter. Namespaces, `include()` prefixes
and the script prefix apply as they do in `reverse()`, and a URL with no parameters comes back
exactly as `reverse()` returns it, so one call covers every route a page hands the frontend.
Converters don't run, so a placeholder is accepted wherever a parameter goes.

The frontend fills a placeholder itself, with plain string replacement:
`url.replace('{post_id}', String(postId))`. The package has no TypeScript helper for it.

## Why it reads the route instead of taking parameter names

The names come from the resolver's `reverse_dict`, the parsed routes Django itself reverses
with, reached by walking namespaces the way `reverse()` does. Both are Django internals, so the
tests pin them against `include()` prefixes, nested and app namespaces and the script prefix,
which is where a Django upgrade would show a change. An earlier version reversed with stand-in values (`0`, `1`, ...) and replaced
them in the result, which broke on a parameter not after a `/` (`file-<int:file_id>`), a
literal `/1` in the route, eleven or more parameters (`/1` matching inside `/10`), and
converters that reject digits. Reading the route costs about what `reverse()` does, 7 to 15 µs
a URL.

`paramnames` is still accepted, to rename the placeholders in route order. A `re_path()` with
unnamed groups needs it, having no names to read: `reverse_template('legacy', ['legacy_id'])`.
When the routes for one name take different parameters, which a `re_path()` with an optional
group does, it raises `ValueError` unless `paramnames` picks one by count.

## Why it isn't called `reverse`

A template like `/posts/{post_id}` is not a URL. Used where a real one belongs, a redirect or an
email link, it fails silently, so it gets a name that can't be mistaken for Django's. It is a
module-level function, as `reverse()` is.
