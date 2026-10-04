from django.test import SimpleTestCase, override_settings

from website_widgets.example.projects.store import Project, Store
from website_widgets.example.projects.widgets.project_list_tile.project_list_tile import ProjectListTile


@override_settings(ROOT_URLCONF='website_widgets.example.urls')
class ProjectListTileTestCase(SimpleTestCase):
    """Renders the widget on its own, with no page and no test client."""

    def setUp(self):
        super().setUp()
        Store.reset()

    def test_project_list_tile__shows_creator_name__when_rendered(self):
        html = ProjectListTile(project=Store.find_project(2)).render__test_sync()

        self.assertIn('By Jordan Avery', html)

    def test_project_list_tile__shows_placeholder__when_description_empty(self):
        project = Store.add_project(Project(name='Empty', created_by=1))

        html = ProjectListTile(project=project).render__test_sync()

        self.assertIn('No description.', html)
