from website_widgets import register_url

from website.pages.example_page import ExamplePage
from website.widgets.info_card.info_card import InfoCard
from website.widgets.page_title_note.page_title_note import PageTitleNote


@register_url('composition/')
class CompositionPage(ExamplePage):
    page_title = 'Composition'
    page_description = 'How widgets nest and how data reaches them.'

    def set_context(self):
        super().set_context()
        self.context.children['constructor_card'] = InfoCard(
            title='Constructor data',
            body="The page passed this title and text to the widget's constructor. Data flows down "
                 "this way; a parent never reads a child's context.")
        self.context.children['list_cards'] = [
            InfoCard(
                title=f'List child {number}',
                body='One of a list of widgets under a single key, looped over in the template.')
            for number in (1, 2, 3)
        ]
        self.context.children['skipped_card'] = None
        self.context.children['page_title_note'] = PageTitleNote()
