from website_widgets import Widget


class EmailDocument(Widget):
    """
    The whole HTML document every email shares: the `<head>`, a header and a footer, around the
    one email's own part, passed in as `content`. A widget's template can be a whole document,
    so an email needs no `Page`, which answers a request.

    Sets `events_url` in `context.page` before its children run, so `content` and anything
    inside it can link back to the site.
    """

    def __init__(self, subject: str, events_url: str, content: Widget):
        super().__init__()
        self.subject = subject
        self.events_url = events_url
        self.content = content

    def set_context(self):
        self.context.page['events_url'] = self.events_url
        self.context.data['subject'] = self.subject
        self.context.children['content'] = self.content
