from datetime import timedelta

from django.db.models import Count, Max
from django.utils import timezone
from django.utils.timesince import timesince
from website_widgets import register_url

from api.models import Copy, Movie
from website.pages.app_page import AppPage
from website.widgets.movie_card import MovieCard


@register_url('')
class HomePage(AppPage):
    """What's new on the shelf: every movie that gained a copy in the last month, newest first."""

    page_title = 'New on the shelf'
    NEW_FOR_DAYS = 30

    async def set_context(self):
        since = timezone.now() - timedelta(days=self.NEW_FOR_DAYS)
        arrivals = (
            Copy.objects
            .filter(added_at__gte=since)
            .values('movie_id')
            .annotate(new_copies=Count('id'), arrived_at=Max('added_at'))
            .order_by('-arrived_at')
        )
        arrivals = [arrival async for arrival in arrivals]
        movies = Movie.objects.with_availability().filter(id__in=[arrival['movie_id'] for arrival in arrivals])
        movies_by_id = {movie.id: movie async for movie in movies}

        cards = []
        for arrival in arrivals:
            movie = movies_by_id[arrival['movie_id']]
            if arrival['new_copies'] == movie.total_copies:
                what = 'New to the shelf'
            elif arrival['new_copies'] == 1:
                what = '1 new copy'
            else:
                what = f"{arrival['new_copies']} new copies"
            # depth=1: "2 weeks ago", not "2 weeks, 4 days ago". timesince counts whole minutes,
            # so under one it says "0 minutes".
            if timezone.now() - arrival['arrived_at'] < timedelta(minutes=1):
                when = 'just now'
            else:
                when = f"{timesince(arrival['arrived_at'], depth=1)} ago"
            note = f'{what}, {when}'
            cards.append(MovieCard(movie=movie, note=note))
        self.context.data['new_for_days'] = self.NEW_FOR_DAYS
        self.context.children['cards'] = cards
