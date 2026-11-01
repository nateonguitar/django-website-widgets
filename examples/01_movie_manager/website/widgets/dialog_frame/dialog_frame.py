from website_widgets import AsyncWidget, SyncWidget


class DialogFrame(SyncWidget):
    """
    The <dialog> every dialog opens, and the only widget that renders one. It sits inside a
    <template>, which DialogController.openFrame() clones for each call, around the dialog's own
    content widget:

        DialogFrame(name='confirm-dialog', content=ConfirmDialog())

    `name` is the <dialog>'s class, and with `-template` the <template>'s id, which the content's
    controller passes to DialogController.openFrame(). A `title` adds a title row with a close button;
    without one, the content names the dialog itself (`data-dialog-label`) and closes it with
    buttons of its own.
    """

    def __init__(
            self,
            *,
            name: str,
            content: SyncWidget | AsyncWidget,
            title: str = ''):
        super().__init__()
        self.name = name
        self.content = content
        self.title = title

    def set_context(self):
        self.context.data['name'] = self.name
        self.context.data['title'] = self.title
        self.context.children['content'] = self.content
