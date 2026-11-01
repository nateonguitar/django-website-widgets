from website_widgets import SyncWidget

from website.widgets.emails.email_footer import EmailFooter


class EmailDocument(SyncWidget):
    """
    Every email's whole document, the way a document template is every page's: the <head>, one
    email's own part (its `content` widget), and the EmailFooter they all share. Rendered with
    render() and no request, since emails are sent from sync code.
    """

    def __init__(self, subject: str, site_url: str, content: SyncWidget):
        super().__init__()
        self.subject = subject
        self.site_url = site_url
        self.content = content

    def set_context(self):
        # Before its children run, so the content, the footer and anything inside them can link
        # back: an email has no request, so its links are the site's URL plus a path.
        self.context.page['site_url'] = self.site_url
        self.context.data['subject'] = self.subject
        self.context.children['content'] = self.content
        self.context.children['footer'] = EmailFooter()
