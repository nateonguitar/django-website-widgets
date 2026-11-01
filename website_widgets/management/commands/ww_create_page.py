import os
from argparse import BooleanOptionalAction
from dataclasses import dataclass

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError
from django.urls import get_resolver
from django.utils.module_loading import import_string
from django.utils.regex_helper import normalize

from website_widgets.config import WebsiteWidgetsConfig, get_config
from website_widgets.management.component_files import ComponentFiles, ComponentName, WrittenFile
from website_widgets.management.framework_folder import FrameworkFolder, TypeScriptFolder
from website_widgets.page_routes import PageRoute, PageRoutes
from website_widgets.web_page import AsyncWebPage, _WebPage


@dataclass(frozen=True)
class PageBaseClass:
    """The class a generated page extends, as its import line will name it."""

    module_path: str
    class_name: str
    # An AsyncWebPage, so the page gets `async def set_context()`; otherwise a SyncWebPage.
    renders_async: bool

    def get_page_py_template(self) -> str:
        return 'page__async.py.tmpl' if self.renders_async else 'page__sync.py.tmpl'


class Command(BaseCommand):
    help = (
        "Creates a page in the website app's pages/: a subclass of the app's page base class, "
        "routed with @register_url, its template, and optionally a TypeScript controller and a "
        "stylesheet, registered in ts/main.ts.")

    def add_arguments(self, parser):
        parser.add_argument(
            'name',
            help='The page\'s folder and module name, such as "home_page" or "account/settings_page".')
        parser.add_argument(
            '--tscontroller',
            action=BooleanOptionalAction,
            dest='generate_ts',
            help='Generate a TypeScript controller, or not with --no-tscontroller. Asks when neither is given.')
        parser.add_argument(
            '--stylesheet',
            action=BooleanOptionalAction,
            dest='generate_styles',
            help='Generate a stylesheet, or not with --no-stylesheet. Asks when neither is given.')
        parser.add_argument(
            '--route',
            help=(
                'The route the page template\'s @register_url gets, such as "account/settings", '
                'or "" for the site root. Defaults to one made from the name.'))

    def handle(self, *args, **options):
        config = get_config()
        files = ComponentFiles(
            templates_dir=config.generate_component.templates_dir,
            stdout=self.stdout,
            stderr=self.stderr)
        app_folder = files.website_app_folder(config.website_app_name)
        files.require_framework_files(app_folder)
        # Checked before anything is written, so a missing base class leaves no half-made page.
        page_base_class = self._page_base_class(config)

        name = ComponentName.parse(options['name'])
        page_folder = os.path.join(app_folder, 'pages', name.path)
        if os.path.exists(page_folder):
            raise CommandError(f'{FrameworkFolder.display_path(page_folder)} already exists.')
        generate_ts = files.ask_yes_no(options['generate_ts'], 'Generate a TypeScript controller?')
        generate_styles = files.ask_yes_no(options['generate_styles'], 'Generate a stylesheet?')
        route = options['route'] if options['route'] is not None else name.get_default_route()
        page_py_template = page_base_class.get_page_py_template()
        # A project's page template without the placeholder writes pages it routes some other way.
        routed = files.template_has(page_py_template, '__route__')
        if routed:
            self._check_route_is_free(route, name)

        framework_folder = os.path.join(app_folder, TypeScriptFolder.RELATIVE_PATH)
        replacements = {
            '__ClassName__': name.class_name,
            '__module_name__': name.module_name,
            '__css_name__': name.css_name,
            '__framework_path__': files.relative_import_path(framework_folder, page_folder),
            '__app_page_module__': page_base_class.module_path,
            '__AppPageClass__': page_base_class.class_name,
            '__route__': route,
        }
        package_inits = files.make_component_folder(os.path.join(app_folder, 'pages'), name)
        written_files = []
        files.write_from_template(page_folder, '__init__.py', '__init__.py.tmpl', replacements)
        written_files.append(WrittenFile('__init__.py'))
        files.write_from_template(page_folder, f'{name.module_name}.py', page_py_template, replacements)
        page_py_note = f'class {name.class_name}({page_base_class.class_name})'
        if routed:
            page_py_note += f', {self._describe_route(route, name)}'
        else:
            page_py_note += f", not routed: the project's {page_py_template} has no @register_url('__route__')"
        written_files.append(WrittenFile(f'{name.module_name}.py', page_py_note))
        html_template = 'page__controller.html.tmpl' if generate_ts else 'page__nocontroller.html.tmpl'
        files.write_from_template(page_folder, f'{name.module_name}.html', html_template, replacements)
        written_files.append(WrittenFile(f'{name.module_name}.html', f'root #{name.css_name}'))

        # main.ts imports each stylesheet so webpack bundles it, and exports each controller so a
        # template can import it from the bundle.
        from_main_ts = files.relative_import_path(page_folder, os.path.join(app_folder, 'ts'))
        if generate_ts:
            files.write_from_template(page_folder, f'{name.module_name}.ts', 'controller.ts.tmpl', replacements)
            exported = files.add_to_main_ts(
                app_folder,
                '// {{ PAGE CONTROLLERS START }}',
                f"export {{ {name.class_name}Controller }} from '{from_main_ts}/{name.module_name}';")
            written_files.append(WrittenFile(
                f'{name.module_name}.ts',
                f'{name.class_name}Controller, exported from ts/main.ts' if exported else f'{name.class_name}Controller'))
        if generate_styles:
            files.write_from_template(page_folder, f'{name.module_name}.scss', 'component.scss.tmpl', replacements)
            imported = files.add_to_main_ts(
                app_folder,
                '// {{ PAGE STYLES START }}',
                f"import '{from_main_ts}/{name.module_name}.scss';")
            written_files.append(WrittenFile(f'{name.module_name}.scss', 'imported in ts/main.ts' if imported else ''))

        # A running runserver watches pages/ (PageRoutes.watch_pages_folder), but Django's
        # StatReloader skips a file the first time it sees one, so a page written in one go never
        # restarts it. pages/__init__.py has already been seen, so a new modification time on it,
        # with its content unchanged, does.
        pages_init = os.path.join(app_folder, 'pages', '__init__.py')
        if os.path.isfile(pages_init):
            os.utime(pages_init)

        self.stdout.write(self.style.SUCCESS(
            f'Created the page {name.class_name} in {FrameworkFolder.display_path(page_folder)}/:'))
        self.stdout.write(files.format_file_list(written_files))
        for init_path in package_inits:
            self.stdout.write(f'Also wrote {FrameworkFolder.display_path(init_path)}, so its folder imports as a package.')
        if not routed:
            page_module = '.'.join([files.website_app_module(config.website_app_name), 'pages', *name.path.split('/')])
            self.stdout.write(
                f"To serve it, add @register_url('{route}') above its class, or route it in urls.py:\n"
                f"  from {page_module} import {name.class_name}\n"
                f"  path('{route}', {name.class_name}.as_view(), name='{name.class_name}'),")
        if generate_ts or generate_styles:
            self.stdout.write('Run `npm run watch` (or `runserver`, with start_npm_watch()) to rebuild the bundle.')

    @staticmethod
    def _describe_route(
        route: str,
        name: ComponentName
    ) -> str:
        """
        The URL the route serves and the name it reverses by. The URLconf loaded before the page
        existed, so the URL is the prefix the website app's routes are included at, plus the route.
        """
        namespace = PageRoutes.get_namespace()
        view_name = f'{namespace}:{name.class_name}'
        included = get_resolver().namespace_dict.get(namespace)
        if included is None:
            return f"routed to '{route}' once urls.py includes PageRoutes.urls(), reversed as {view_name}"
        # The prefix is held as a regex, the way reverse() reads it.
        prefix_format, prefix_parameters = normalize(included[0])[0]
        if prefix_parameters:
            return f"routed to '{route}' after the website app's prefix, reversed as {view_name}"
        return f'routed to /{prefix_format}{route}, reversed as {view_name}'

    def _check_route_is_free(
        self,
        route: str,
        name: ComponentName
    ):
        """
        Stops on a name another page already registers, which would fail every import of the
        pages. Warns on a route that ties with another page's, which `check_for_ties()` reports,
        rather than stopping, since the developer may be about to change the other route.
        """
        PageRoutes.discover()
        new_route = PageRoute(
            route=route,
            name=name.class_name,
            page_class=_WebPage)
        try:
            # Raises on a converter Django doesn't have, which would otherwise fail on import.
            new_route.get_sample_kwargs()
        except ImproperlyConfigured as error:
            raise CommandError(str(error))
        new_route_key = new_route.get_specificity_key()
        for page_route in PageRoutes.get_ordered_routes():
            if page_route.name == new_route.name:
                raise CommandError(
                    f"A route is already named '{page_route.name}', on "
                    f"{page_route.page_class.__module__}.{page_route.page_class.__qualname__}, and "
                    f"@register_url names a route after its class. Choose another page name.")
            if page_route.get_specificity_key() == new_route_key and new_route.can_match_same_url_as(page_route):
                self.stdout.write(self.style.WARNING(
                    f"'{page_route.route}' ({page_route.page_class.__qualname__}) can match the "
                    f"same URLs as '{route}', and neither is more specific, so the "
                    f"website_widgets.E001 check fails until one of them changes."))

    @staticmethod
    def _page_base_class(config: WebsiteWidgetsConfig) -> PageBaseClass:
        """
        `app_page_class`, the class a generated page extends. Stops when nothing is there, or it
        is neither an `AsyncWebPage` nor a `SyncWebPage`.
        """
        dotted_path = config.generate_component.get_app_page_class(config.website_app_name)
        try:
            page_class = import_string(dotted_path)
        except ImportError:
            raise CommandError(
                f'There is no page base class at {dotted_path}. Create it, or set '
                f'WEBSITE_WIDGETS.generate_component.app_page_class to the dotted path of yours.')
        if not isinstance(page_class, type) or not issubclass(page_class, _WebPage):
            raise CommandError(
                f'{dotted_path} is neither a website_widgets.AsyncWebPage nor a '
                f'website_widgets.SyncWebPage.')
        module_path, class_name = dotted_path.rsplit('.', 1)
        return PageBaseClass(
            module_path=module_path,
            class_name=class_name,
            renders_async=issubclass(page_class, AsyncWebPage))
