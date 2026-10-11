import importlib
import os
import re
from dataclasses import dataclass, field
from typing import NamedTuple

from django.apps import apps
from django.core import checks
from django.core.exceptions import ImproperlyConfigured
from django.urls import URLPattern, path
from django.urls.converters import get_converters

from website_widgets.config import get_config
from website_widgets.page import Page


PATH_PARAMETER_RE = re.compile(r'<(?:(?P<converter>[^>:]+):)?(?P<parameter>[^>]+)>')


@dataclass
class PageRoute:
    """One `@register_url` on a page: the arguments of the `path()` it becomes."""

    route: str
    name: str
    page_class: type[Page]
    kwargs: dict = field(default_factory=dict)

    # A converter missing here, such as a project's own, ranks with `str`.
    CONVERTER_RANKS = {
        'int': 1,
        'uuid': 2,
        'slug': 3,
        'str': 4,
        'path': 5,
    }
    # Ranks after every segment, so a longer route is tried before a shorter one it shares a
    # start with. That only matters when a `path` parameter could swallow the extra segments.
    END_OF_ROUTE_KEY = (6, 0)
    # Tried in order for each parameter; the first its converter's regex accepts is used.
    SAMPLE_PARAMETER_VALUES = ('a', '1', '00000000-0000-0000-0000-000000000000')

    def get_specificity_key(self) -> tuple:
        """Sorts the most specific route first, comparing segment by segment."""
        segment_keys = [self._get_segment_key(segment) for segment in self.route.split('/')]
        return (*segment_keys, self.END_OF_ROUTE_KEY)

    def can_match_same_url_as(
        self,
        other: 'PageRoute'
    ) -> bool:
        """For two equally specific routes, which have the same number of segments."""
        segment_pairs = zip(self.route.split('/'), other.route.split('/'))
        segments_match = [
            self._get_segment_regex(segment) == self._get_segment_regex(other_segment)
            for segment, other_segment in segment_pairs
        ]
        return all(segments_match)

    def get_segment_labels(self) -> list[str]:
        """What each segment matches: `fixed`, a converter name, or `fixed+<converter>` for both."""
        segment_labels = []
        for segment in self.route.split('/'):
            converter_names = [
                match.group('converter') or 'str'
                for match in PATH_PARAMETER_RE.finditer(segment)
            ]
            if not converter_names:
                segment_labels.append('fixed')
            elif PATH_PARAMETER_RE.sub('', segment):
                segment_labels.append('fixed+' + '+'.join(converter_names))
            else:
                segment_labels.append('+'.join(converter_names))
        return segment_labels

    def get_sample_kwargs(self) -> dict[str, str | None]:
        """
        A value per parameter that its converter accepts, for building a URL this route serves.
        None for a converter that accepts none of `SAMPLE_PARAMETER_VALUES`.
        """
        converters = get_converters()
        sample_kwargs = {}
        for match in PATH_PARAMETER_RE.finditer(self.route):
            converter_name = match.group('converter') or 'str'
            if converter_name not in converters:
                raise ImproperlyConfigured(
                    f"URL route '{self.route}' uses invalid converter '{converter_name}'.")
            converter_regex = converters[converter_name].regex
            sample_kwargs[match.group('parameter')] = next(
                (
                    sample_value
                    for sample_value in self.SAMPLE_PARAMETER_VALUES
                    if re.fullmatch(converter_regex, sample_value)
                ),
                None)
        return sample_kwargs

    def to_url_pattern(self) -> URLPattern:
        return path(
            self.route,
            self.page_class.as_view(),
            kwargs=self.kwargs,
            name=self.name)

    @classmethod
    def _get_segment_key(cls, segment: str) -> tuple[int, int]:
        converter_names = [
            match.group('converter') or 'str'
            for match in PATH_PARAMETER_RE.finditer(segment)
        ]
        if not converter_names:
            return (0, 0)
        rank = max(
            cls.CONVERTER_RANKS.get(converter_name, cls.CONVERTER_RANKS['str'])
            for converter_name in converter_names)
        literal_length = len(PATH_PARAMETER_RE.sub('', segment))
        # Literal text narrows a parameter, so `v-<str:x>` is tried before `<str:x>`.
        return (rank, -literal_length)

    def _get_segment_regex(self, segment: str) -> str:
        converters = get_converters()
        parts = []
        previous_end = 0
        for match in PATH_PARAMETER_RE.finditer(segment):
            converter_name = match.group('converter') or 'str'
            if converter_name not in converters:
                raise ImproperlyConfigured(
                    f"URL route '{self.route}' uses invalid converter '{converter_name}'.")
            parts.append(re.escape(segment[previous_end:match.start()]))
            parts.append(converters[converter_name].regex)
            previous_end = match.end()
        parts.append(re.escape(segment[previous_end:]))
        return ''.join(parts)


class PageRoutesUrls(NamedTuple):
    """
    What `PageRoutes.urls()` returns. A tuple, because `path()` only accepts an include as a list
    or a tuple, as with `admin.site.urls`; the field names are for reading it.
    """

    url_patterns: list[URLPattern]
    app_name: str
    namespace: str


class PageRoutes:
    """The pages routed with `@register_url`."""

    _routes: dict[str, PageRoute] = {}

    @classmethod
    def register_url(
        cls,
        route: str,
        *,
        name: str | None = None,
        kwargs: dict | None = None
    ):
        """
        Adds the decorated page to the project's URLs, with `path()`'s arguments. The name
        defaults to the class name, and is reversed inside the website app's namespace:

            @register_url('')
            class HomePage(AppPage):  # reverse('website:HomePage')

        Stack one per route, naming all but one, since names must be unique:

            @register_url('forum/<int:post_id>')
            @register_url('tab-requests/<int:post_id>', name='TabRequestPage')
            class ForumPostPage(AppPage):

        `kwargs` reach the page's constructor alongside the URL's parameters. Only pages in modules
        under the website app's `pages/` folder are found.
        """
        def decorator(page_class):
            if not (isinstance(page_class, type) and issubclass(page_class, Page)):
                raise TypeError(
                    f"@register_url('{route}') decorates {page_class!r}, which is not a Page "
                    f"subclass.")
            route_name = name if name is not None else page_class.__name__
            existing = cls._routes.get(route_name)
            if existing is not None:
                raise ImproperlyConfigured(
                    f"@register_url name '{route_name}' on {page_class.__qualname__} is already "
                    f"used by {existing.page_class.__qualname__} at '{existing.route}'.")
            cls._routes[route_name] = PageRoute(
                route=route,
                name=route_name,
                page_class=page_class,
                kwargs=dict(kwargs or {}))
            return page_class

        return decorator

    @classmethod
    def urls(cls) -> PageRoutesUrls:
        """
        Every registered page's URL pattern, most specific route first, in a namespace named after
        the website app. Included in `urls.py` the way the admin is:

            path('', PageRoutes.urls()),
        """
        cls.discover()
        url_patterns = [route.to_url_pattern() for route in cls.get_ordered_routes()]
        namespace = cls.get_namespace()
        return PageRoutesUrls(
            url_patterns=url_patterns,
            app_name=namespace,
            namespace=namespace)

    @staticmethod
    def get_namespace() -> str:
        """The namespace every decorated route is reversed in, named after the website app."""
        return get_config().website_app_name

    @classmethod
    def discover(cls):
        """Imports every module under the website app's `pages/` folder, registering its pages."""
        app_config = apps.get_app_config(get_config().website_app_name)
        pages_folder = os.path.join(app_config.path, 'pages')
        for folder, subfolders, filenames in os.walk(pages_folder):
            subfolders[:] = sorted(subfolder for subfolder in subfolders if subfolder != '__pycache__')
            relative_folder = os.path.relpath(folder, pages_folder)
            package_parts = [] if relative_folder == '.' else relative_folder.split(os.sep)
            for filename in sorted(filenames):
                if not filename.endswith('.py'):
                    continue
                module_parts = [app_config.name, 'pages', *package_parts]
                if filename != '__init__.py':
                    module_parts.append(filename.removesuffix('.py'))
                importlib.import_module('.'.join(module_parts))

    @classmethod
    def get_ordered_routes(cls) -> list[PageRoute]:
        """Most specific first. Equally specific routes fall back to alphabetical order."""
        return sorted(
            cls._routes.values(),
            key=lambda page_route: (page_route.get_specificity_key(), page_route.route))

    @staticmethod
    def check_for_ties(
        app_configs=None,
        **kwargs
    ) -> list[checks.Error]:
        """
        Fails on two equally specific routes that can match the same URL, since only their
        alphabetical order would decide which page serves it.
        """
        try:
            apps.get_app_config(get_config().website_app_name)
        except LookupError:
            return []
        PageRoutes.discover()

        errors = []
        ordered_routes = PageRoutes.get_ordered_routes()
        for index, page_route in enumerate(ordered_routes):
            for later_route in ordered_routes[index + 1:]:
                if later_route.get_specificity_key() != page_route.get_specificity_key():
                    break
                if page_route.can_match_same_url_as(later_route):
                    errors.append(checks.Error(
                        f"'{page_route.route}' ({page_route.name}) and '{later_route.route}' "
                        f"({later_route.name}) can match the same URL, and neither route is more "
                        f"specific.",
                        hint="Add a fixed segment to one route, or give it a narrower converter.",
                        obj=later_route.page_class,
                        id='website_widgets.E001'))
        return errors
