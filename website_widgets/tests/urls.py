"""The URLs `reverse_template()` is tested against, each shaped to break a naive implementation."""

from django.urls import include, path, re_path

from website_widgets.tests.sample_widgets import UnsetDocumentPage


eleven_parameters_route = '/'.join(f'<int:p{i}>' for i in range(11))
stub_view = UnsetDocumentPage.as_view()
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
