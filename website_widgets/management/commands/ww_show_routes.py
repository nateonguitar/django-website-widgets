import argparse
from dataclasses import dataclass

from django.core.management.base import BaseCommand, CommandError
from django.urls import NoReverseMatch, Resolver404, resolve, reverse

from website_widgets.page_routes import PATH_PARAMETER_RE, PageRoute, PageRoutes
from website_widgets.url_templates import reverse_template


@dataclass(frozen=True)
class ReachabilityCheck:
    """Whether a route's sample URL reaches its own page, and what the table says about it."""

    reaches_page: bool
    description: str


@dataclass(frozen=True)
class TableRow:
    """One route's cells, in column order, and whether to print them as a failure."""

    cells: list[str]
    reaches_page: bool


class Command(BaseCommand):
    help = (
        'Lists every @register_url page route in the order incoming URLs are matched against '
        'them, then checks that a sample URL for each route reaches its own page through the '
        'whole project, not a route listed earlier in ROOT_URLCONF.')

    # A converter missing here, such as a project's own, is shown by its full name.
    SEGMENT_ABBREVIATIONS = {
        'fixed': 'f',
        'int': 'i',
        'str': 's',
        'slug': 'g',
        'uuid': 'u',
        'path': 'p',
    }
    COLUMN_HEADERS = {
        'url': 'URL',
        'segments': 'Segments',
        'name': 'Name',
        'page': 'Page',
        'reaches_page': 'Reaches page',
    }
    DEFAULT_COLUMNS = 'url,segments,page'

    def add_arguments(self, parser):
        parser.add_argument(
            '--columns',
            type=self._parse_columns,
            default=self._parse_columns(self.DEFAULT_COLUMNS),
            help=(
                f"Comma-separated columns to show after '#', in order, from "
                f"{','.join(self.COLUMN_HEADERS)}. Default: {self.DEFAULT_COLUMNS}. The "
                f"reachability check runs either way."))
        parser.add_argument(
            '--path-param-type',
            choices=['full', 'type', 'example'],
            default='full',
            help=(
                "How the URL column shows a path parameter: 'full' as declared "
                "(<str:game_slug>), 'type' as its converter (<str>), or 'example' as the sample "
                "value the reachability check uses (a)."))

    def handle(self, *args, **options):
        columns = options['columns']
        path_param_type = options['path_param_type']
        PageRoutes.discover()
        namespace = PageRoutes.get_namespace()
        ordered_routes = PageRoutes.get_ordered_routes()

        rows = []
        unreachable_lines = []
        for position, page_route in enumerate(ordered_routes, start=1):
            view_name = f'{namespace}:{page_route.name}'
            url = self._describe_url(page_route, view_name, path_param_type)
            reachability = self._check_reachable(page_route, view_name)
            if not reachability.reaches_page:
                unreachable_lines.append(f'#{position} {url}: {reachability.description}')
            cells_by_column = {
                'url': url,
                'segments': self._abbreviate_segments(page_route),
                'name': view_name,
                'page': self._describe_page(page_route),
                'reaches_page': reachability.description,
            }
            rows.append(TableRow(
                cells=[str(position), *(cells_by_column[column] for column in columns)],
                reaches_page=reachability.reaches_page))

        self._write_table(
            ['#', *(self.COLUMN_HEADERS[column] for column in columns)],
            rows)
        if 'segments' in columns:
            self.stdout.write('')
            self.stdout.write(
                'Segments: f fixed, i int, s str, g slug, u uuid, p path, '
                'and a project converter by its name.')
        if unreachable_lines:
            if 'reaches_page' not in columns:
                self.stdout.write('')
                for unreachable_line in unreachable_lines:
                    self.stdout.write(self.style.ERROR(unreachable_line))
            raise CommandError(
                f'{len(unreachable_lines)} of {len(ordered_routes)} page routes do not reach '
                f'their page.')
        self.stdout.write(self.style.SUCCESS(
            f'All {len(ordered_routes)} page routes reach their page.'))

    @classmethod
    def _parse_columns(
        cls,
        value: str
    ) -> list[str]:
        columns = [column.strip() for column in value.split(',') if column.strip()]
        unknown_columns = [column for column in columns if column not in cls.COLUMN_HEADERS]
        if unknown_columns or not columns:
            raise argparse.ArgumentTypeError(
                f"unknown or missing columns {unknown_columns}; choose from "
                f"{','.join(cls.COLUMN_HEADERS)}")
        return columns

    def _check_reachable(
        self,
        page_route: PageRoute,
        view_name: str
    ) -> ReachabilityCheck:
        sample_kwargs = page_route.get_sample_kwargs()
        if None in sample_kwargs.values():
            return ReachabilityCheck(reaches_page=False, description='no sample value fits a converter')
        try:
            sample_url = reverse(view_name, kwargs=sample_kwargs)
        except NoReverseMatch:
            return ReachabilityCheck(
                reaches_page=False,
                description='not in ROOT_URLCONF, is PageRoutes.urls() included?')
        try:
            match = resolve(sample_url)
        except Resolver404:
            return ReachabilityCheck(reaches_page=False, description=f'{sample_url} matches nothing')
        if match.view_name != view_name:
            return ReachabilityCheck(
                reaches_page=False,
                description=f'{sample_url} goes to {match.view_name} instead')
        return ReachabilityCheck(reaches_page=True, description='yes')

    @staticmethod
    def _describe_url(
        page_route: PageRoute,
        view_name: str,
        path_param_type: str
    ) -> str:
        """The full path, prefix included, with each parameter shown as `path_param_type` asks."""
        try:
            url = reverse_template(view_name)
        except NoReverseMatch:
            return page_route.route or '(root)'
        sample_kwargs = page_route.get_sample_kwargs()
        for match in PATH_PARAMETER_RE.finditer(page_route.route):
            parameter = match.group('parameter')
            declared = match.group(0)
            if path_param_type == 'type':
                shown = f"<{match.group('converter') or 'str'}>"
            elif path_param_type == 'example':
                shown = sample_kwargs[parameter] or declared
            else:
                shown = declared
            url = url.replace('{' + parameter + '}', shown)
        return url

    @classmethod
    def _abbreviate_segments(
        cls,
        page_route: PageRoute
    ) -> str:
        return '/'.join(
            '+'.join(
                cls.SEGMENT_ABBREVIATIONS.get(part, part)
                for part in segment_label.split('+'))
            for segment_label in page_route.get_segment_labels())

    @staticmethod
    def _describe_page(page_route: PageRoute) -> str:
        if not page_route.kwargs:
            return page_route.page_class.__qualname__
        kwargs_text = ', '.join(f'{key}={value!r}' for key, value in page_route.kwargs.items())
        return f'{page_route.page_class.__qualname__}({kwargs_text})'

    def _write_table(
        self,
        headers: list[str],
        rows: list[TableRow]
    ):
        column_widths = [
            max(len(cells[column]) for cells in [headers, *(row.cells for row in rows)])
            for column in range(len(headers))
        ]
        self.stdout.write(self.style.MIGRATE_HEADING(self._format_row(headers, column_widths)))
        for row in rows:
            line = self._format_row(row.cells, column_widths)
            self.stdout.write(line if row.reaches_page else self.style.ERROR(line))

    @staticmethod
    def _format_row(
        cells: list[str],
        column_widths: list[int]
    ) -> str:
        return '  '.join(
            cell.ljust(width)
            for cell, width in zip(cells, column_widths)
        ).rstrip()
