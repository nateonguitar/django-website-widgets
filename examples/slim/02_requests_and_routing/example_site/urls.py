from django.contrib.auth import views as auth_views
from django.urls import path

from website_widgets import PageRoutes

from website.endpoints.article_cards_endpoint import ArticleCardsEndpoint
from website.pages.about_page.about_page import AboutPage


urlpatterns = [
    # Every page under website/pages/ with @register_url, reversed as website:<name>.
    path('', PageRoutes.urls()),

    # A page routed by hand, like any Django view. It can live anywhere, and its name is plain.
    path('about/', AboutPage.as_view(), name='about'),

    # Plain Django views beside the pages.
    path('api/articles/', ArticleCardsEndpoint.as_view(), name='api_article_cards'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
