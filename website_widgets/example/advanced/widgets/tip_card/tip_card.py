from website_widgets import Widget


class TipCard(Widget):
    """
    One numbered tip about the library. The widget-from-endpoint page renders tip 0 as a child,
    and the tip endpoint renders the following ones on their own with `render__standalone()`, so
    both produce the same markup. Numbers past the last tip wrap around.
    """

    TIPS = [
        "A widget takes its data through its constructor; a parent never reads a child's context.",
        'Anything every widget in the tree needs goes in context.page, shared by reference.',
        'A page picks a variant template by setting template_filename in set_context().',
        "A variant kept beside a base class's module works for every subclass.",
        'A child set to None renders nothing, so optional children need no if in Python.',
        'set_context() can be sync or async; the library awaits whichever it finds.',
        'Templates get no context processors: request, user, page, data and children only.',
        'An endpoint renders a widget with render__standalone(request); a test uses render__test().',
    ]

    def __init__(self, number: int):
        super().__init__()
        self.number = number

    def set_context(self):
        self.context.data['number'] = self.number
        self.context.data['text'] = self.TIPS[self.number % len(self.TIPS)]
