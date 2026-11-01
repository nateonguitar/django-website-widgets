import os

from website_widgets import AsyncWebPage, register_url

from website.models import Animal, AnimalType
from website.widgets.animal_filter.animal_filter import AnimalFilter
from website.widgets.animal_list.animal_list import AnimalList


@register_url('')
class ShelterPage(AsyncWebPage):
    """
    The site's only page. It loads the animals and hands them down: the list gets every animal,
    and builds a card for each.
    """

    # Absolute, since a relative path would resolve beside a subclass's module.
    document_template_path = os.path.join(os.path.dirname(__file__), 'document_template.html')

    async def set_context(self):
        # Evaluated here with the async ORM: a page renders inside an async pipeline, where a
        # queryset left for the template would run a sync query and raise.
        animals = [animal async for animal in Animal.objects.all()]
        self.context.page['title'] = 'Animal shelter'
        self.context.children['filter'] = AnimalFilter(animal_types=AnimalType.choices)
        self.context.children['list'] = AnimalList(animals=animals)
