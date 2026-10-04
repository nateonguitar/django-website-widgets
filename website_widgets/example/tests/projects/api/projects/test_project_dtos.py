from django.test import SimpleTestCase, override_settings

from website_widgets.example.api.errors import UnprocessableEntityException
from website_widgets.example.projects.api.projects.by_id.project_update_dto import ProjectUpdateDto
from website_widgets.example.projects.api.projects.project_create_dto import ProjectCreateDto
from website_widgets.example.projects.api.projects.project_response_dto import ProjectResponseDto
from website_widgets.example.projects.store import Store


@override_settings(ROOT_URLCONF='website_widgets.example.urls')
class ProjectDtosTestCase(SimpleTestCase):
    def setUp(self):
        super().setUp()
        Store.reset()

    def test_create_dto__ignores_fields_a_client_may_not_set__when_sent(self):
        dto = ProjectCreateDto.from_dict({'name': 'Trip', 'id': 1, 'created_by': 2})

        self.assertEqual(dto, ProjectCreateDto(name='Trip'))

    def test_create_dto__fails_listing_every_field__when_both_break_rules(self):
        with self.assertRaises(UnprocessableEntityException) as caught:
            ProjectCreateDto.from_dict({'name': '', 'description': 7}).validate()

        self.assertEqual(list(caught.exception.errors), ['name', 'description'])

    def test_update_dto__succeeds__when_body_empty(self):
        ProjectUpdateDto.from_dict({}).validate()

    def test_update_dto__fails__when_name_given_blank(self):
        with self.assertRaises(UnprocessableEntityException) as caught:
            ProjectUpdateDto.from_dict({'name': ''}).validate()

        self.assertEqual(list(caught.exception.errors), ['name'])

    def test_response_dto__includes_derived_fields__when_from_project(self):
        project = Store.find_project(1)

        data = ProjectResponseDto.from_project(project).to_dict()

        self.assertEqual(data['created_by_name'], 'Riley Park')
        self.assertEqual(data['url'], project.url)
        self.assertEqual(data['created_at'], project.created_at.isoformat())
