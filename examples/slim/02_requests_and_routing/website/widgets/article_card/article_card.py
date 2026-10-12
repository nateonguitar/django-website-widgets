from website_widgets import Widget

from website.models import Article


class ArticleCard(Widget):
    """
    One article in a list. The articles page renders the first few as children, and the "load
    more" endpoint renders the rest with `arender()`, so both produce the same markup.
    """

    def __init__(self, article: Article):
        super().__init__()
        self.article = article

    def set_context(self):
        self.context.data['article'] = self.article
