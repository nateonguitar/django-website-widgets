# Templates

What a widget's or page's template can see, how its file is found, and how a variant render is
chosen. The package renders templates itself rather than through Django's loader, so a few
things a Django developer expects are absent. Read this before writing a template, or when a
widget renders but its content is missing.

Primary code:
- `website_widgets.widget` — `get_template_path()`, `_context_dict()`, `_render_template()`

## The context is four keys

`_render_template()` opens the template file with `open()`, builds a `Template` from the string
and renders it against a bare `Context`, so **no template context processors run.** The context
is exactly:

| Key | Value |
|---|---|
| `request` | the request, or `None` when `render()`/`arender()` was given none |
| `page` | `self.context.page`, shared by reference down the whole tree |
| `data` | `self.context.data`, this widget only |
| `children` | `self.context.children`, this widget only, each rendered to HTML |

Anything a project expects from a context processor (`user`, `csrf_token`, `MEDIA_URL`, `debug`,
settings) **is not there** and resolves to empty with no error; `rendering_pipeline.md` says
how a page provides the user. `{% load %}`, custom tags and filters, `{% url %}` and
`{% static %}` all work normally. A page's document template also receives `page_content_html`.

**A missing namespace prefix fails silently.** `{{ title }}` is not `{{ data.title }}`; it is
undefined, so a `{% if %}` guarding a block is false and the block never renders, with nothing
logged. This is the most common cause of "my widget renders but its content is missing".

**`data` and `children` are per-widget, `page` is shared.** A child cannot see its parent's
`data`. Anything every widget must reach goes in `context.page`. A child in `children` may be a
widget, a list of widgets (iterated with `{% for item in children.items %}`) or `None`.

## Which file

**The template file is named after the class's module** unless `template_filename` says
otherwise: a class in `info_card/info_card.py` renders `info_card/info_card.html`. **A file
called `template.html` is never found**; it fails with `FileNotFoundError` at render time.

**A variant render is another file beside it, `<module>__<variant>.html`,** chosen by assigning
`template_filename` a bare file name (a `/`, `\` or `..` raises `ValueError`). It is read after
every `set_context()` has run, so a widget can choose in `set_context()`: a page with a
not-found state keeps `project_page__not_found.html` beside `project_page.html` and switches to
it there.

**The lookup walks the class hierarchy, the concrete class first.** `get_template_path()` checks
the folder of each class in the MRO, skipping the library's own classes, and returns the first
folder holding the file. A base class's variant, kept beside the base class's module, works for
every subclass; a subclass with a file of the same name shadows it. A name found nowhere raises
`FileNotFoundError` listing the folders searched. The module-named default is always beside the
concrete class.

**`{% include %}` of another component's template is not part of the model,** since files are
opened directly rather than resolved through `TEMPLATES` dirs. Compose with child widgets.
