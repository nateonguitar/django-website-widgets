from website_widgets import PageRoutes, register_url
from website_widgets.page import Page
from website_widgets.tests.page_routes.page_routes_test_case import PageRoutesTestCase


class CheckForTiesTestCase(PageRoutesTestCase):
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

    def test_check_for_ties__succeeds__when_equally_specific_routes_differ_in_a_fixed_segment(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(Page):
            pass

        @register_url('tab-requests/<int:post_id>', name='tab_request')
        class TabRequestPage(Page):
            pass

        self.assertEqual(PageRoutes.check_for_ties(), [])
