from website_widgets import Widget
from website_widgets.example.projects.store import Project


class ProjectListTile(Widget):
    """One project in the projects page's list."""

    def __init__(self, project: Project):
        super().__init__()
        self.project = project

    def set_context(self):
        self.context.data['project'] = self.project
