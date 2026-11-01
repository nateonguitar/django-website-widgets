from website_widgets import SyncWidget

from website.models import Animal


class AnimalCard(SyncWidget):
    """One animal, given to it by the list that built it."""

    def __init__(self, animal: Animal):
        super().__init__()
        self.animal = animal

    def set_context(self):
        self.context.data['animal'] = self.animal
