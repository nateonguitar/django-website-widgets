from website_widgets import Widget

from website.models import Project


class ProjectListTile(Widget):
    """One project in the projects page's list. Its project comes with `created_by` loaded."""

    def __init__(self, project: Project):
        super().__init__()
        self.project = project

    def set_context(self):
        self.context.data['project'] = self.project
