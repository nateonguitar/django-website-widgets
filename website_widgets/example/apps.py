from django.apps import AppConfig


class WebsiteWidgetsExampleConfig(AppConfig):
    """
    The example site. Install it only for development: its data lives in memory in each server
    process.
    """

    name = 'website_widgets.example'
    label = 'website_widgets_example'

    def ready(self):
        from website_widgets.example.projects.store import Store

        Store.reset()
