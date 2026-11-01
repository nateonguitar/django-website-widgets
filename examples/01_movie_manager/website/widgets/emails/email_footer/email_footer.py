from website_widgets import SyncWidget


class EmailFooter(SyncWidget):
    """
    The footer every email ends with, identical in each, the way a company's emails share one.
    EmailDocument places it, so an email's own widget never repeats it. Its links come from
    `page.site_url`, which EmailDocument sets before its children run.
    """
