from website_widgets import Widget


class InfoCard(Widget):
    def __init__(self, title: str, body: str):
        super().__init__()
        self.title = title
        self.body = body

    def set_context(self):
        self.context.data['title'] = self.title
        self.context.data['body'] = self.body
