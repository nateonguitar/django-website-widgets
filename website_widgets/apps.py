from django.apps import AppConfig


class WebsiteWidgetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'website_widgets'

    def ready(self):
        from django.core import checks
        from django.utils.autoreload import autoreload_started

        from website_widgets.management.framework_folder import FrameworkFolder
        from website_widgets.page_routes import PageRoutes

        autoreload_started.connect(PageRoutes.watch_pages_folder, dispatch_uid='website_widgets.watch_pages_folder')
        checks.register(PageRoutes.check_website_app_is_installed)
        checks.register(PageRoutes.check_pages_are_routed, checks.Tags.urls)
        checks.register(PageRoutes.check_for_ties, checks.Tags.urls)
        checks.register(FrameworkFolder.check_version_stamp)
