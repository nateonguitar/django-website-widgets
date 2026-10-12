from django.apps import AppConfig


class WebsiteWidgetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'website_widgets'

    def ready(self):
        from django.core import checks

        from website_widgets.management.framework_folder import FrameworkFolder
        from website_widgets.page_routes import PageRoutes

        checks.register(PageRoutes.check_for_ties, checks.Tags.urls)
        checks.register(FrameworkFolder.check_version_stamp)
