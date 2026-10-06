import importlib
import io
import os
import sys
import tempfile
import uuid
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.core.management import CommandError, call_command
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.test.utils import override_script_prefix
from django.urls import NoReverseMatch, include, path, re_path, reverse

from website_widgets import PageRoutes, register_url, reverse_template
from website_widgets.config import WebsiteWidgetsConfig
from website_widgets.page import Page
from website_widgets.widget import Widget


TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


class DefaultTemplateWidget(Widget):
    pass


class ClassLevelTemplateWidget(Widget):
    template_filename = 'tests.py'


class ContextChosenTemplateWidget(Widget):
    def set_context(self):
        self.template_filename = '__init__.py'


class BaseFolderWidget(Widget):
    pass


class SubfolderWidget(BaseFolderWidget):
    pass


class UnsetBasePage(Page):
    pass


class ClassLevelBasePage(Page):
    base_template_path = '../templates/base.html'


class SyncContextWidget(Widget):
    def set_context(self):
        self.context.data['word'] = 'sync'


class AsyncContextWidget(Widget):
    async def set_context(self):
        self.context.data['word'] = 'async'


class WordWidget(Widget):
    def __init__(self, word: str, template_filename: str):
        super().__init__()
        self.word = word
        self.template_filename = template_filename

    def set_context(self):
        self.context.data['word'] = self.word


class ParentWidget(Widget):
    def __init__(self, child_template_filename: str):
        super().__init__()
        self.child_template_filename = child_template_filename

    def set_context(self):
        self.context.children['single'] = WordWidget('one', self.child_template_filename)
        self.context.children['many'] = [
            WordWidget('two', self.child_template_filename),
            WordWidget('three', self.child_template_filename),
        ]
        self.context.children['absent'] = None


class WidgetTestCase(SimpleTestCase):
    def write_template(self, content: str) -> str:
        """Writes a template beside this module for one test and returns its bare file name."""
        with tempfile.NamedTemporaryFile('w', suffix='.html', dir=TESTS_DIR, delete=False) as template_file:
            template_file.write(content)
        self.addCleanup(os.remove, template_file.name)
        return os.path.basename(template_file.name)


class TemplateFilenameTestCase(WidgetTestCase):
    """Existing files beside this module stand in for templates, since only the lookup is tested."""

    def test_get_template_path__returns_module_named_html__when_template_filename_unset(self):
        self.assertEqual(
            DefaultTemplateWidget().get_template_path(),
            os.path.join(TESTS_DIR, 'tests.html'))

    def test_get_template_path__returns_sibling_file__when_template_filename_set_on_class(self):
        self.assertEqual(
            ClassLevelTemplateWidget().get_template_path(),
            os.path.join(TESTS_DIR, 'tests.py'))

    def test_get_template_path__returns_sibling_file__when_template_filename_set_in_set_context(self):
        widget = ContextChosenTemplateWidget()
        widget.set_context()

        self.assertEqual(widget.get_template_path(), os.path.join(TESTS_DIR, '__init__.py'))

    def test_get_template_path__fails__when_template_filename_is_a_path(self):
        for filename in ('/srv/templates/absolute.html', 'sub/child.html', '../up.html', 'a\\b.html', '..'):
            with self.subTest(filename=filename):
                widget = DefaultTemplateWidget()
                widget.template_filename = filename
                with self.assertRaises(ValueError):
                    widget.get_template_path()

    def test_get_template_path__fails_naming_the_searched_folders__when_file_is_missing(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = 'missing.html'

        with self.assertRaises(FileNotFoundError) as caught:
            widget.get_template_path()
        self.assertIn(TESTS_DIR, str(caught.exception))

    def test_get_template_path__returns_base_class_file__when_only_the_base_folder_has_it(self):
        with tempfile.TemporaryDirectory() as root:
            base_dir = os.path.join(root, 'base')
            sub_dir = os.path.join(root, 'base', 'sub')
            os.makedirs(sub_dir)
            with open(os.path.join(base_dir, 'base__variant.html'), 'w') as template_file:
                template_file.write('')
            fake_files = {
                SubfolderWidget: os.path.join(sub_dir, 'sub.py'),
                BaseFolderWidget: os.path.join(base_dir, 'base.py'),
            }
            widget = SubfolderWidget()
            widget.template_filename = 'base__variant.html'

            with patch('website_widgets.widget.inspect.getfile', side_effect=fake_files.__getitem__):
                path = widget.get_template_path()

        self.assertEqual(path, os.path.join(base_dir, 'base__variant.html'))

    def test_get_template_path__prefers_own_folder__when_class_and_base_both_have_the_file(self):
        with tempfile.TemporaryDirectory() as root:
            base_dir = os.path.join(root, 'base')
            sub_dir = os.path.join(root, 'base', 'sub')
            os.makedirs(sub_dir)
            for folder in (base_dir, sub_dir):
                with open(os.path.join(folder, 'shared.html'), 'w') as template_file:
                    template_file.write('')
            fake_files = {
                SubfolderWidget: os.path.join(sub_dir, 'sub.py'),
                BaseFolderWidget: os.path.join(base_dir, 'base.py'),
            }
            widget = SubfolderWidget()
            widget.template_filename = 'shared.html'

            with patch('website_widgets.widget.inspect.getfile', side_effect=fake_files.__getitem__):
                path = widget.get_template_path()

        self.assertEqual(path, os.path.join(sub_dir, 'shared.html'))

    def test_render__test_sync__renders_chosen_template__when_template_filename_set(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('chosen {{ data.word }}')
        widget.context.data['word'] = 'template'

        self.assertEqual(widget.render__test_sync(), 'chosen template')


class RenderInPlaceTestCase(WidgetTestCase):
    async def test_render__test__runs_set_context__when_set_context_is_sync(self):
        widget = SyncContextWidget()
        widget.template_filename = self.write_template('{{ data.word }}')

        self.assertEqual(await widget.render__test(), 'sync')

    async def test_render__test__runs_set_context__when_set_context_is_async(self):
        widget = AsyncContextWidget()
        widget.template_filename = self.write_template('{{ data.word }}')

        self.assertEqual(await widget.render__test(), 'async')

    async def test_render__test__renders_children__when_nested_and_listed(self):
        widget = ParentWidget(self.write_template('{{ data.word }}'))
        widget.template_filename = self.write_template(
            '{{ children.single }}|{% for child in children.many %}{{ child }},{% endfor %}|'
            '{{ children.absent|default_if_none:"none" }}')

        self.assertEqual(await widget.render__test(), 'one|two,three,|none')

    async def test_render__test__shares_page_context_with_children__when_set_before_rendering(self):
        widget = ParentWidget(self.write_template('{{ page.nonce }}'))
        widget.template_filename = self.write_template('{{ children.single }}')
        widget.context.page['nonce'] = 'abc'

        self.assertEqual(await widget.render__test(), 'abc')

    async def test_render__test__renders_as_anonymous__when_no_user_given(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ user.is_authenticated }}')

        self.assertEqual(await widget.render__test(), 'False')

    async def test_render__test__renders_as_user__when_user_given(self):
        user = SimpleNamespace(is_authenticated=True, username='riley')
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ user.username }}')

        self.assertEqual(await widget.render__test(user=user), 'riley')

    async def test_render__standalone__renders_with_given_request__when_called(self):
        request = RequestFactory().get('/somewhere/')
        request.user = AnonymousUser()
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('{{ request.path }}')

        self.assertEqual(await widget.render__standalone(request), '/somewhere/')

    async def test_render__test__fails__when_already_rendered(self):
        widget = DefaultTemplateWidget()
        widget.template_filename = self.write_template('once')
        await widget.render__test()

        with self.assertRaises(RuntimeError):
            await widget.render__test()


eleven_parameters_route = '/'.join(f'<int:p{i}>' for i in range(11))
stub_view = UnsetBasePage.as_view()
inner_patterns = (
    [path('items/<int:item_id>', stub_view, name='item')],
    'inner_app')
outer_patterns = (
    [
        path('posts/<int:post_id>', stub_view, name='post'),
        path('nested/', include(inner_patterns, namespace='inner')),
    ],
    'outer_app')
urlpatterns = [
    path('plain', stub_view, name='plain'),
    path('posts/<int:post_id>/comments/<int:comment_id>', stub_view, name='comment'),
    path('files/file-<int:file_id>', stub_view, name='file'),
    path('v1/1/<int:item_id>', stub_view, name='literal_one'),
    path(eleven_parameters_route, stub_view, name='eleven'),
    path('things/<uuid:thing_id>/<slug:thing_slug>/<path:rest>', stub_view, name='converters'),
    path('section/', include([path('pages/<int:page_id>', stub_view, name='section_page')])),
    path('outer/', include(outer_patterns, namespace='outer')),
    path('app-default/', include(outer_patterns)),
    re_path(r'^legacy/(\d+)/$', stub_view, name='unnamed_group'),
    re_path(r'^optional/(?:(?P<page>\d+)/)?$', stub_view, name='optional_group'),
]


@override_settings(ROOT_URLCONF='website_widgets.tests')
class ReverseTemplateTestCase(SimpleTestCase):
    def test_reverse_template__returns_reverse_result__when_route_has_no_parameters(self):
        self.assertEqual(reverse_template('plain'), reverse('plain'))

    def test_reverse_template__returns_route_parameter_names__when_paramnames_omitted(self):
        self.assertEqual(reverse_template('comment'), '/posts/{post_id}/comments/{comment_id}')

    def test_reverse_template__returns_template__when_parameter_not_after_slash(self):
        self.assertEqual(reverse_template('file'), '/files/file-{file_id}')

    def test_reverse_template__keeps_literal_segment__when_route_contains_slash_one(self):
        self.assertEqual(reverse_template('literal_one'), '/v1/1/{item_id}')

    def test_reverse_template__returns_every_placeholder__when_route_has_eleven_parameters(self):
        expected = '/' + '/'.join('{p' + str(i) + '}' for i in range(11))

        self.assertEqual(reverse_template('eleven'), expected)

    def test_reverse_template__returns_template__when_converters_reject_digits(self):
        self.assertEqual(reverse_template('converters'), '/things/{thing_id}/{thing_slug}/{rest}')

    def test_reverse_template__includes_prefix__when_route_is_included(self):
        self.assertEqual(reverse_template('section_page'), '/section/pages/{page_id}')

    def test_reverse_template__includes_prefix__when_name_is_namespaced(self):
        self.assertEqual(reverse_template('outer:post'), '/outer/posts/{post_id}')

    def test_reverse_template__includes_every_prefix__when_namespaces_are_nested(self):
        self.assertEqual(reverse_template('outer:inner:item'), '/outer/nested/items/{item_id}')

    def test_reverse_template__uses_default_instance__when_name_uses_app_namespace(self):
        self.assertEqual(reverse('outer_app:post', args=[1]), '/app-default/posts/1')
        self.assertEqual(reverse_template('outer_app:post'), '/app-default/posts/{post_id}')

    def test_reverse_template__includes_script_prefix__when_one_is_set(self):
        with override_script_prefix('/mounted/'):
            self.assertEqual(reverse_template('outer:post'), '/mounted/outer/posts/{post_id}')

    def test_reverse_template__renames_placeholders_in_order__when_paramnames_given(self):
        self.assertEqual(
            reverse_template('comment', ['a', 'b']),
            '/posts/{a}/comments/{b}')

    def test_reverse_template__names_unnamed_group__when_paramnames_given(self):
        self.assertEqual(reverse_template('unnamed_group', ['legacy_id']), '/legacy/{legacy_id}/')

    def test_reverse_template__chooses_route_by_parameter_count__when_paramnames_given(self):
        self.assertEqual(reverse_template('optional_group', ['page']), '/optional/{page}/')

    def test_reverse_template__fails__when_routes_for_name_differ_in_parameters(self):
        with self.assertRaises(ValueError):
            reverse_template('optional_group')

    def test_reverse_template__fails__when_paramnames_count_differs_from_route(self):
        with self.assertRaises(NoReverseMatch):
            reverse_template('comment', ['post_id'])

    def test_reverse_template__fails__when_name_is_unknown(self):
        with self.assertRaises(NoReverseMatch):
            reverse_template('missing')

    def test_reverse_template__fails__when_namespace_is_unknown(self):
        with self.assertRaises(NoReverseMatch):
            reverse_template('missing:post')


class BaseTemplatePathTestCase(SimpleTestCase):
    def test_get_base_template_path__fails__when_base_template_path_unset(self):
        with self.assertRaises(NotImplementedError):
            UnsetBasePage().get_base_template_path()

    def test_get_base_template_path__returns_path_beside_class__when_base_template_path_relative(self):
        self.assertEqual(
            ClassLevelBasePage().get_base_template_path(),
            os.path.join(TESTS_DIR, '../templates/base.html'))

    def test_get_base_template_path__returns_path_unchanged__when_base_template_path_absolute(self):
        page = UnsetBasePage()
        page.base_template_path = '/srv/templates/base.html'

        self.assertEqual(page.get_base_template_path(), '/srv/templates/base.html')


class WebsiteWidgetsConfigTestCase(SimpleTestCase):
    def test_website_app_name__returns_website__when_not_given(self):
        self.assertEqual(WebsiteWidgetsConfig().website_app_name, 'website')

    def test_website_app_name__returns_given_label__when_given(self):
        config = WebsiteWidgetsConfig(website_app_name='storefront')

        self.assertEqual(config.website_app_name, 'storefront')


class PageRoutesTestCase(SimpleTestCase):
    """
    Each test gets an empty registry and a throwaway website app on `sys.path`, so neither the
    project's pages nor another test's leak in.
    """

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.package_name = f'page_routes_fixture_{uuid.uuid4().hex}'
        package_folder = os.path.join(temp_dir.name, self.package_name)
        self.pages_folder = os.path.join(package_folder, 'pages')
        os.makedirs(self.pages_folder)
        sys.path.insert(0, temp_dir.name)
        self.addCleanup(sys.path.remove, temp_dir.name)
        self.addCleanup(self.forget_fixture_modules)

        app_config = SimpleNamespace(
            name=self.package_name,
            path=package_folder)
        mock_apps = self.enterContext(patch('website_widgets.page_routes.apps'))
        mock_apps.get_app_config.return_value = app_config
        self.enterContext(patch.object(PageRoutes, '_routes', {}))

    def forget_fixture_modules(self):
        for module_name in list(sys.modules):
            if module_name.startswith(self.package_name):
                del sys.modules[module_name]

    def write_page_module(self, relative_path: str, content: str):
        module_path = os.path.join(self.pages_folder, relative_path)
        os.makedirs(os.path.dirname(module_path), exist_ok=True)
        with open(module_path, 'w') as module_file:
            module_file.write(content)
        importlib.invalidate_caches()

    def get_routes_in_url_order(self) -> list[str]:
        url_patterns, _app_name, _namespace = PageRoutes.urls()
        return [str(url_pattern.pattern) for url_pattern in url_patterns]

    def test_register_url__routes_page_at_each_route__when_stacked(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        @register_url('tab-requests/<int:post_id>', name='tab_request')
        class ForumPostPage(Page):
            pass

        url_patterns, _app_name, _namespace = PageRoutes.urls()

        self.assertEqual(
            {url_pattern.name: url_pattern.callback.view_class for url_pattern in url_patterns},
            {
                'forum_post': ForumPostPage,
                'tab_request': ForumPostPage,
            })

    def test_register_url__names_route_after_class__when_name_omitted(self):
        @register_url('')
        class HomePage(Page):
            pass

        url_patterns, _app_name, _namespace = PageRoutes.urls()

        self.assertEqual([url_pattern.name for url_pattern in url_patterns], ['HomePage'])

    def test_urls__namespaces_routes_by_website_app_name__when_included(self):
        config = WebsiteWidgetsConfig(website_app_name='storefront')
        self.enterContext(patch('website_widgets.page_routes.get_config', return_value=config))

        _url_patterns, app_name, namespace = PageRoutes.urls()

        self.assertEqual((app_name, namespace), ('storefront', 'storefront'))

    def test_register_url__passes_kwargs_to_route__when_kwargs_given(self):
        @register_url('tab-requests/create', name='tab_request_create', kwargs={'post_type': 'tab_request'})
        class CreatePostPage(Page):
            pass

        url_patterns, _app_name, _namespace = PageRoutes.urls()

        self.assertEqual(url_patterns[0].default_args, {'post_type': 'tab_request'})

    def test_register_url__fails__when_name_already_registered(self):
        @register_url('forum', name='forum')
        class ForumPage(Page):
            pass

        with self.assertRaises(ImproperlyConfigured):
            @register_url('other-forum', name='forum')
            class OtherForumPage(Page):
                pass

    def test_register_url__fails__when_class_is_not_a_page(self):
        with self.assertRaises(TypeError):
            @register_url('plain', name='plain')
            class PlainWidget(Widget):
                pass

    def test_urls__routes_page__when_only_discovery_imports_its_module(self):
        self.write_page_module('nested_page/__init__.py', '')
        self.write_page_module(
            'nested_page/nested_page.py',
            'from website_widgets import Page, register_url\n'
            '\n'
            '\n'
            "@register_url('nested', name='nested')\n"
            'class NestedPage(Page):\n'
            '    pass\n')

        self.assertEqual(self.get_routes_in_url_order(), ['nested'])

    def test_urls__orders_fixed_segment_first__when_parameter_could_match_it(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(Page):
            pass

        @register_url('profile/settings', name='profile_settings')
        class SettingsPage(Page):
            pass

        self.assertEqual(self.get_routes_in_url_order(), ['profile/settings', 'profile/<str:username>'])

    def test_urls__orders_longer_route_first__when_path_parameter_could_match_it(self):
        @register_url('files/<path:file_path>', name='file')
        class FilePage(Page):
            pass

        @register_url('files/<path:file_path>/history', name='file_history')
        class FileHistoryPage(Page):
            pass

        self.assertEqual(
            self.get_routes_in_url_order(),
            ['files/<path:file_path>/history', 'files/<path:file_path>'])

    def test_urls__orders_alphabetically__when_routes_are_equally_specific(self):
        @register_url('tabs/<int:tab_id>', name='tab')
        class TabPage(Page):
            pass

        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(Page):
            pass

        self.assertEqual(self.get_routes_in_url_order(), ['forum/<int:post_id>', 'tabs/<int:tab_id>'])

    def test_check_for_ties__fails__when_equally_specific_routes_match_same_url(self):
        @register_url('a/<str:x>', name='a_x')
        class XPage(Page):
            pass

        @register_url('a/<str:y>', name='a_y')
        class YPage(Page):
            pass

        errors = PageRoutes.check_for_ties()

        self.assertEqual([error.id for error in errors], ['website_widgets.E001'])

    def test_check_for_ties__succeeds__when_fixed_segment_and_int_parameter_share_position(self):
        @register_url('forum/create-post', name='forum_create_post')
        class CreatePostPage(Page):
            pass

        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(Page):
            pass

        self.assertEqual(PageRoutes.check_for_ties(), [])

    def use_urlconf(self, urlpatterns: list):
        urlconf = ModuleType('page_routes_test_urlconf')
        urlconf.urlpatterns = urlpatterns
        self.enterContext(override_settings(ROOT_URLCONF=urlconf))

    def run_show_page_resolve_order(self, *args, output: io.StringIO | None = None, **options) -> str:
        output = output or io.StringIO()
        call_command('show_page_resolve_order', *args, stdout=output, no_color=True, **options)
        return output.getvalue()

    def test_show_page_resolve_order__shows_only_given_columns__when_columns_given(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(Page):
            pass

        self.use_urlconf([path('', PageRoutes.urls())])

        output = self.run_show_page_resolve_order('--columns=url,name')

        self.assertIn('website:forum_post', output)
        self.assertNotIn('ForumPostPage', output)

    def test_show_page_resolve_order__lists_unreachable_route__when_reaches_page_column_hidden(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(Page):
            pass

        self.use_urlconf([
            path('profile/<str:username>', UnsetBasePage.as_view(), name='hand_routed_profile'),
            path('', PageRoutes.urls()),
        ])
        output = io.StringIO()

        with self.assertRaises(CommandError):
            self.run_show_page_resolve_order('--columns=url', output=output)

        self.assertIn('/profile/a goes to hand_routed_profile instead', output.getvalue())

    def test_show_page_resolve_order__shows_converter_only__when_path_param_type_is_type(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(Page):
            pass

        self.use_urlconf([path('', PageRoutes.urls())])

        output = self.run_show_page_resolve_order(path_param_type='type')

        self.assertIn('/forum/<int>', output)

    def test_show_page_resolve_order__shows_sample_value__when_path_param_type_is_example(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(Page):
            pass

        self.use_urlconf([path('', PageRoutes.urls())])

        output = self.run_show_page_resolve_order(path_param_type='example')

        self.assertIn('/forum/1 ', output)

    def test_show_page_resolve_order__lists_fixed_segment_first__when_parameter_could_match_it(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(Page):
            pass

        @register_url('profile/settings', name='profile_settings')
        class SettingsPage(Page):
            pass

        self.use_urlconf([path('', PageRoutes.urls())])

        output = self.run_show_page_resolve_order()

        self.assertLess(output.index('profile/settings'), output.index('profile/<str:username>'))

    def test_show_page_resolve_order__fails__when_earlier_urlconf_route_takes_its_url(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(Page):
            pass

        self.use_urlconf([
            path('profile/<str:username>', UnsetBasePage.as_view(), name='hand_routed_profile'),
            path('', PageRoutes.urls()),
        ])

        with self.assertRaises(CommandError):
            self.run_show_page_resolve_order()

    def test_show_page_resolve_order__fails__when_page_routes_not_included(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(Page):
            pass

        self.use_urlconf([])

        with self.assertRaises(CommandError):
            self.run_show_page_resolve_order()

    def test_check_for_ties__succeeds__when_equally_specific_routes_differ_in_a_fixed_segment(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(Page):
            pass

        @register_url('tab-requests/<int:post_id>', name='tab_request')
        class TabRequestPage(Page):
            pass

        self.assertEqual(PageRoutes.check_for_ties(), [])
