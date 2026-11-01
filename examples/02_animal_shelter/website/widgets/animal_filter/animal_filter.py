from website_widgets import SyncWidget


class AnimalFilter(SyncWidget):
    """The All, Dogs and Cats buttons. Filtering happens in the browser, in its template's script."""

    def __init__(self, animal_types: list[tuple[str, str]]):
        super().__init__()
        self.animal_types = animal_types

    def set_context(self):
        self.context.data['animal_types'] = self.animal_types
