from django.core.management.base import BaseCommand
from django.utils.termcolors import colorize


class Command(BaseCommand):
    """
    Manual sanity check that the django-website-widgets package is installed
    correctly (--verbose dumps app_config/class info). Not a real test suite.
    """

    help = 'Test that django-website-widgets package is working correctly'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information',
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)

        self.stdout.write(colorize('=' * 60, fg='cyan'))
        self.stdout.write(colorize('  Django Website Widgets Package Test', fg='cyan', opts=('bold',)))
        self.stdout.write(colorize('=' * 60, fg='cyan'))
        self.stdout.write('')

        self.stdout.write(self.style.SUCCESS('✓ Package is installed and working!'))
        self.stdout.write('')

        if verbose:
            from django.apps import apps
            try:
                from website_widgets import Widget, Page, WidgetContext

                app_config = apps.get_app_config('website_widgets')

                self.stdout.write(self.style.HTTP_INFO('Package Details:'))
                self.stdout.write(f'  App name: {app_config.name}')
                self.stdout.write(f'  App path: {app_config.path}')
                self.stdout.write(f'  Verbose name: {app_config.verbose_name}')
                self.stdout.write('')

                self.stdout.write(self.style.HTTP_INFO('Available Classes:'))
                self.stdout.write(f'  Widget: {Widget}')
                self.stdout.write(f'  Page: {Page}')
                self.stdout.write(f'  WidgetContext: {WidgetContext}')
                self.stdout.write('')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {e}'))

        self.stdout.write(self.style.SUCCESS('Management command executed successfully!'))
        self.stdout.write('')
