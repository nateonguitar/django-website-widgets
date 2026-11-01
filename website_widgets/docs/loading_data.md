# Loading data in a page

A lesson: getting data into a page's widgets with the async ORM, without slow pages or
`SynchronousOnlyOperation`. Read this before writing a widget that queries. The rule that a sync
query fails inside a page is in `rendering_pipeline.md`'s gotchas; this is how to write the
widgets so it never comes up.

## Query in `async def set_context()`

A widget in a page or behind `arender()` loads its data with the async ORM, and hands its
template evaluated data, never a lazy queryset:

```python
class MovieList(AsyncWidget):
    async def set_context(self):
        movies = [movie async for movie in Movie.objects.order_by('title')]
        self.context.children['cards'] = [MovieCard(movie=movie) for movie in movies]
```

`aget()`, `afirst()`, `acount()`, `aexists()`, `aaggregate()` and `async for` cover most reads;
`acreate()`, `asave()` and `adelete()` most writes. Anything without an async form (a
`transaction.atomic()` block, a third-party sync API) goes in a `sync_to_async` function.

**A template following a foreign key queries too.** `{{ data.rental.user.username }}` on a
rental loaded without its user makes a sync query while the template renders, inside the page's
async pipeline, and raises. Load what the template reads in the same query:
`Rental.objects.select_related('user', 'copy__movie')`, or `prefetch_related()` for a
many-side. The same goes for a model property that queries.

## One after another, or gathered

**The package runs each widget's `set_context()` to the end before starting the next**, depth
first, parent before child. Three widgets that each await a slow call take three times as long
as one.

When the slow part is outside the database, such as an HTTP call to another service, the parent
gathers the calls in its own `set_context()` and passes each result down through a constructor:

```python
import asyncio

class DashboardPage(AppPage):
    async def set_context(self):
        weather, stock, news = await asyncio.gather(
            WeatherApi.today(),
            StockApi.prices(),
            NewsApi.headlines())
        self.context.children['weather'] = WeatherCard(weather=weather)
        self.context.children['stock'] = StockCard(stock=stock)
        self.context.children['news'] = NewsCard(news=news)
```

The children are then plain widgets that only display what they were given. **Gathering database
queries gains nothing:** Django's async ORM runs every query on one shared thread, so gathered
queries still run one at a time. For the database, fewer queries is the fix (`select_related`,
one query for a list instead of one per row), not concurrency.

A widget that loads its own data is still the simplest choice for one query; gather only when
the page is measurably waiting on several slow calls.
