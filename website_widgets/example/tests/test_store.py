from django.test import SimpleTestCase, override_settings

from website_widgets.example.projects.api.projects.by_id.project_update_dto import ProjectUpdateDto
from website_widgets.example.projects.api.projects.project_create_dto import ProjectCreateDto
from website_widgets.example.projects.store import Project, Store


@override_settings(ROOT_URLCONF='website_widgets.example.urls')
class StoreTestCase(SimpleTestCase):
    def setUp(self):
        super().setUp()
        Store.reset()
        self.user_1 = Store.find_user(1)
        self.user_2 = Store.find_user(2)
        self.admin = Store.find_user(3)
        self.project_1 = Store.find_project(1)

    def test_can_access__succeeds__when_viewer_created_the_project(self):
        self.assertTrue(self.project_1.can_access(self.user_1))

    def test_can_access__succeeds__when_viewer_is_admin(self):
        self.assertTrue(self.project_1.can_access(self.admin))

    def test_can_access__fails__when_viewer_is_another_user(self):
        self.assertFalse(self.project_1.can_access(self.user_2))

    def test_can_access__fails__when_anonymous(self):
        self.assertFalse(self.project_1.can_access(None))

    def test_projects_for__returns_own_projects__when_regular_user(self):
        self.assertEqual([project.id for project in Store.projects_for(self.user_1)], [1])

    def test_projects_for__returns_every_project__when_admin(self):
        self.assertEqual([project.id for project in Store.projects_for(self.admin)], [1, 2])

    def test_add_project__takes_next_id__when_added(self):
        project = Store.add_project(Project(name='New', created_by=self.user_2.id))

        self.assertEqual(project.id, 3)

    def test_update_project__replaces_stored_project__when_edited_copy_saved(self):
        edited = self.project_1.updated_with(ProjectUpdateDto(name='Vegetable garden'))

        Store.update_project(edited)

        self.assertIs(Store.find_project(1), edited)
        self.assertEqual(len(Store.projects), 2)

    def test_reset__restores_seed_data_and_ids__when_store_changed(self):
        Store.delete_project(self.project_1)
        Store.add_project(Project(name='New', created_by=self.user_1.id))

        Store.reset()

        self.assertEqual([project.id for project in Store.projects], [1, 2])
        self.assertEqual(
            Store.add_project(Project(name='Again', created_by=self.user_1.id)).id,
            3)

    def test_updated_with__keeps_fields_dto_leaves_out__when_partial(self):
        edited = self.project_1.updated_with(ProjectUpdateDto(name='Vegetable garden'))

        self.assertEqual(edited.description, self.project_1.description)
        self.assertEqual(self.project_1.name, 'Garden planner')

    def test_from_create_dto__sets_owner__when_created(self):
        project = Project.from_create_dto(ProjectCreateDto(name='Trip'), created_by=self.user_2)

        self.assertEqual(project.created_by, self.user_2.id)

    def test_name_errors__fails__when_blank(self):
        self.assertEqual(Project.name_errors(''), ['The name is required.'])

    def test_name_errors__fails__when_too_long(self):
        self.assertEqual(len(Project.name_errors('x' * (Project.NAME_MAX_LENGTH + 1))), 1)

    def test_description_errors__fails__when_too_long(self):
        self.assertEqual(
            len(Project.description_errors('x' * (Project.DESCRIPTION_MAX_LENGTH + 1))),
            1)

    def test_description_errors__succeeds__when_empty(self):
        self.assertEqual(Project.description_errors(''), [])
