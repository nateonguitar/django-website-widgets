from website_widgets import Widget

from website.models import Animal
from website.widgets.animal_card.animal_card import AnimalCard


class AnimalList(Widget):
    """Every animal, one `AnimalCard` each: a list of children, rendered in order."""

    def __init__(self, animals: list[Animal]):
        super().__init__()
        self.animals = animals

    def set_context(self):
        self.context.children['cards'] = [AnimalCard(animal=animal) for animal in self.animals]
