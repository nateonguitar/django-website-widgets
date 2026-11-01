from website_widgets import SyncWidget


class AccountMenu(SyncWidget):
    """
    The signed-in user's name in the appbar, and the dialog it opens: the theme and signing out.
    A child of `Appbar`, which builds it only when someone is signed in.

    It takes no user in its constructor. The user is page-wide: `AppPage` loads it once into
    `context.page`, which every widget in the tree shares by reference, so the template reads
    `page.user` directly instead of each widget on the way down passing it along. `context.data`
    is the other kind, this widget's alone, which a parent can't see and a child doesn't inherit;
    it's for what only this widget works out, and this one works out nothing, so it has no
    `set_context()`.
    """
