from website_widgets import Widget

from api.models import MovieRating


class RatingPicker(Widget):
    """
    A rating <select> that says what the chosen rating means. Used by the add-to-inventory page,
    and by the Movie admin through RatingSelect, with the same controller in both: its template's
    <script> imports it from the site's bundle, in the admin as on the site.
    """

    def __init__(self, name: str, value: str = '', select_id: str | None = None):
        """`select_id` is the <select>'s id, for a <label for>, as a Django form passes it."""
        super().__init__()
        self.name = name
        self.value = value
        self.select_id = select_id

    def set_context(self):
        chosen = MovieRating(self.value) if self.value in MovieRating.values else None
        self.context.data['name'] = self.name
        self.context.data['value'] = self.value
        self.context.data['select_id'] = self.select_id
        # One root per field, so two pickers on a page each start their own controller.
        self.context.data['root_id'] = f'rating-picker-{self.select_id or self.name}'
        self.context.data['ratings'] = list(MovieRating)
        # Rendered with the page, so the chosen rating's description shows before any script
        # runs, and stays right where the bundle isn't loaded.
        self.context.data['description'] = chosen.description if chosen else ''
