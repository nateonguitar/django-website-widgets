from django.urls import reverse

from website_widgets import register_url

from website.models import Article
from website.pages.site_page import SitePage


@register_url('')
class IndexPage(SitePage):
    async def set_context(self):
        await super().set_context()
        members_only_article = await Article.objects.filter(members_only=True).afirst()
        self.context.data['demos'] = [
            {
                'name': 'Articles, with "load more"',
                'url': reverse('website:articles'),
                'description': 'The first cards render with the page; the button asks an endpoint for more, rendered on the server with arender().',
            },
            {
                'name': 'The latest article',
                'url': reverse('website:latest_article'),
                'description': 'A redirect from handle_request(). Its fixed route, articles/latest/, is tried before articles/<slug:slug>/.',
            },
            {
                'name': 'A members-only article',
                'url': reverse('website:article', kwargs={'slug': members_only_article.slug}) if members_only_article else '',
                'description': 'Logged out, the 401 variant; logged in, the article.',
            },
            {
                'name': 'An article that doesn\'t exist',
                'url': reverse('website:article', kwargs={'slug': 'no-such-article'}),
                'description': 'The 404 variant.',
            },
            {
                'name': 'The editor',
                'url': reverse('website:editor'),
                'description': 'Staff only: logged out, 401; logged in but not staff, 403.',
            },
            {
                'name': 'The changelog',
                'url': reverse('website:changelog'),
                'description': 'An ETag from the newest article, and a 304 Not Modified when nothing changed.',
            },
            {
                'name': 'About',
                'url': reverse('about'),
                'description': 'A page routed by hand in urls.py, with a plain name instead of website:<name>.',
            },
        ]
