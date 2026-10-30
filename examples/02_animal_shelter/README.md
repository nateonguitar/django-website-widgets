# Animal shelter

**The no-build alternative.** [`01_movie_manager`](../01_movie_manager) is how django-website-widgets
means a site to be built, with TypeScript, SCSS and webpack, and nearly everything there works
the same here. This shows only what a site without npm does differently: a static CSS file and
an inline `<script>`.

```bash
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver
```

Then open http://localhost:8000/. Tests: `poetry run python manage.py test`.

- **One page, three widgets.** `ShelterPage` (`website/pages/shelter_page/`) loads the animals
  and hands them down through constructors: `AnimalFilter` gets the dog and cat choices,
  `AnimalList` gets the animals and builds an `AnimalCard` for each.
- **Styles** are `website/static/website/styles.css`, linked from the document template with
  `{% static %}`.
- **The filter** is an inline `<script>` in `animal_filter.html`, beside the buttons it drives,
  showing and hiding cards by their `data-animal-type`.
