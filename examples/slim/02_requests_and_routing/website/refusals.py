class PageRefusal(Exception):
    """
    Raised from a page's `set_context()` to refuse the request. `SitePage.handle_request()` turns
    it into the variant template `site_page__<variant>.html`, with the status code.
    """

    status_code: int
    variant: str
    title: str


class NotLoggedIn(PageRefusal):
    status_code = 401
    variant = 'unauthorized'
    title = 'Log in to see this page'


class NotAllowed(PageRefusal):
    status_code = 403
    variant = 'forbidden'
    title = "You're not allowed to see this page"


class NotFound(PageRefusal):
    status_code = 404
    variant = 'not_found'
    title = "There's nothing here"
