import random
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.utils import timezone


# Every seeded user's password. Not `password` or another common one, which browsers flag as
# breached on every sign-in.
PASSWORD = 'try-the-widgets'

FAMILY = ['alex', 'jordan', 'sam']
# Runs the shelf from /admin/ too. The site and the admin share Django's session, so signing in
# on either signs in on both.
SUPERUSER = 'sam'

# Title, year, genre, rating, copies on the shelf.
MOVIES = [
    # A third arrives with NEW_COPIES.
    ('Die Hard', 1988, 'action', 'R', 2),
    ('Gladiator', 2000, 'action', 'R', 1),
    ('John Wick', 2014, 'action', 'R', 1),
    ('Lethal Weapon', 1987, 'action', 'R', 1),
    ('Mad Max: Fury Road', 2015, 'action', 'R', 1),
    ('Mission: Impossible', 1996, 'action', 'PG13', 2),
    ('Raiders of the Lost Ark', 1981, 'action', 'PG', 2),
    ('Speed', 1994, 'action', 'R', 1),
    ('The Dark Knight', 2008, 'action', 'PG13', 2),
    ('Top Gun', 1986, 'action', 'PG', 1),
    ('Coco', 2017, 'animation', 'PG', 2),
    ('Finding Nemo', 2003, 'animation', 'G', 3),
    ('Inside Out', 2015, 'animation', 'PG', 2),
    ('My Neighbor Totoro', 1988, 'animation', 'G', 1),
    ('Ratatouille', 2007, 'animation', 'G', 1),
    ('Shrek', 2001, 'animation', 'PG', 2),
    ('Spirited Away', 2001, 'animation', 'PG', 1),
    ('The Incredibles', 2004, 'animation', 'PG', 2),
    ('The Lion King', 1994, 'animation', 'G', 2),
    ('Up', 2009, 'animation', 'PG', 1),
    ('WALL-E', 2008, 'animation', 'G', 1),
    ('Airplane!', 1980, 'comedy', 'PG', 1),
    ('Clueless', 1995, 'comedy', 'PG13', 1),
    ("Ferris Bueller's Day Off", 1986, 'comedy', 'PG13', 1),
    ('Ghostbusters', 1984, 'comedy', 'PG', 2),
    ('Groundhog Day', 1993, 'comedy', 'PG', 1),
    ('Hot Fuzz', 2007, 'comedy', 'R', 1),
    ('Mean Girls', 2004, 'comedy', 'PG13', 1),
    ('Office Space', 1999, 'comedy', 'R', 1),
    ('The Big Lebowski', 1998, 'comedy', 'R', 1),
    ('The Grand Budapest Hotel', 2014, 'comedy', 'R', 1),
    ('Apollo 13', 1995, 'drama', 'PG', 1),
    ('Dead Poets Society', 1989, 'drama', 'PG', 1),
    ('Forrest Gump', 1994, 'drama', 'PG13', 2),
    ('Good Will Hunting', 1997, 'drama', 'R', 1),
    ('Jaws', 1975, 'drama', 'PG', 1),
    ('Rocky', 1976, 'drama', 'PG', 1),
    ('The Godfather', 1972, 'drama', 'R', 1),
    ('The Shawshank Redemption', 1994, 'drama', 'R', 1),
    ('Titanic', 1997, 'drama', 'PG13', 2),
    ('Babe', 1995, 'family', 'G', 1),
    ('E.T. the Extra-Terrestrial', 1982, 'family', 'PG', 2),
    ('Home Alone', 1990, 'family', 'PG', 2),
    ('Hook', 1991, 'family', 'PG', 1),
    ('Mary Poppins', 1964, 'family', 'G', 1),
    ('Matilda', 1996, 'family', 'PG', 1),
    ('Paddington 2', 2017, 'family', 'PG', 2),
    ('The Princess Bride', 1987, 'family', 'PG', 1),
    ('The Sound of Music', 1965, 'family', 'G', 1),
    ('A Quiet Place', 2018, 'horror', 'PG13', 1),
    ('Alien', 1979, 'horror', 'R', 1),
    ('Get Out', 2017, 'horror', 'R', 1),
    ('Gremlins', 1984, 'horror', 'PG', 1),
    ('Halloween', 1978, 'horror', 'R', 1),
    ('Poltergeist', 1982, 'horror', 'PG', 1),
    ('Scream', 1996, 'horror', 'R', 1),
    ('The Shining', 1980, 'horror', 'R', 1),
    ('The Sixth Sense', 1999, 'horror', 'PG13', 1),
    ('Arrival', 2016, 'science_fiction', 'PG13', 1),
    ('Back to the Future', 1985, 'science_fiction', 'PG', 2),
    ('Blade Runner', 1982, 'science_fiction', 'R', 1),
    ('Close Encounters of the Third Kind', 1977, 'science_fiction', 'PG', 1),
    ('Inception', 2010, 'science_fiction', 'PG13', 2),
    ('Interstellar', 2014, 'science_fiction', 'PG13', 1),
    ('Jurassic Park', 1993, 'science_fiction', 'PG13', 2),
    ('Star Wars', 1977, 'science_fiction', 'PG', 2),
    ('The Matrix', 1999, 'science_fiction', 'R', 1),
    ('The Terminator', 1984, 'science_fiction', 'R', 1),
]
# The movies above went on the shelf this many days before the seed, before any of the history.
STOCKED_DAYS_AGO = 400

# Movies new to the shelf, the home page's "brand new": title, year, genre, rating, copies, and
# days before the seed they arrived.
NEW_MOVIES = [
    ('Toy Story', 1995, 'animation', 'G', 2, 5),
    ('The Iron Giant', 1999, 'animation', 'PG', 1, 9),
    ('Paddington', 2014, 'family', 'PG', 1, 20),
]

# Another copy of a movie already on the shelf: title, and days before the seed it arrived. The
# last is older than the home page's month, so it isn't shown.
NEW_COPIES = [
    ('Die Hard', 12),
    ('Jurassic Park', 18),
    ('Home Alone', 25),
    ('Inception', 45),
]

# Who has what right now, and for how many days: one of the three Die Hards, and the only
# Spirited Away, so it shows as none available.
OUT_ALREADY = [
    ('jordan', 'Die Hard', 4),
    ('sam', 'Spirited Away', 23),
]

# A year of returned rentals, so My history and its chart have something to show.
HISTORY_DAYS = 365
# Each person's chance, on a given day, of taking something from the shelf.
CHANCE_OF_A_VISIT = {'alex': 0.45, 'jordan': 0.3, 'sam': 0.55}
# How many movies one visit takes, picked from this list.
MOVIES_PER_VISIT = [1, 1, 1, 2, 2, 3]
# A fixed seed, so every migrate and every test run gets the same history.
RANDOM_SEED = 2026


def seed(apps, schema_editor):
    User = apps.get_model('api', 'User')
    Movie = apps.get_model('api', 'Movie')
    Copy = apps.get_model('api', 'Copy')
    Rental = apps.get_model('api', 'Rental')

    hashed_password = make_password(PASSWORD)
    users = {}
    for username in FAMILY:
        is_superuser = username == SUPERUSER
        users[username] = User.objects.create(
            username=username,
            # example.com is reserved for examples, so nothing is ever delivered there.
            email=f'{username}@example.com',
            password=hashed_password,
            is_staff=is_superuser,
            is_superuser=is_superuser)

    now = timezone.now()
    # added_at is auto_now_add, so each insert sets it to now; the past dates go in after.
    for title, year, genre, rating, copies in MOVIES:
        movie = Movie.objects.create(title=title, year=year, genre=genre, rating=rating)
        for _ in range(copies):
            Copy.objects.create(movie=movie)
    Copy.objects.update(added_at=now - timedelta(days=STOCKED_DAYS_AGO))
    for title, year, genre, rating, copies, days_ago in NEW_MOVIES:
        movie = Movie.objects.create(title=title, year=year, genre=genre, rating=rating)
        new_copy_ids = [Copy.objects.create(movie=movie).id for _ in range(copies)]
        Copy.objects.filter(id__in=new_copy_ids).update(added_at=now - timedelta(days=days_ago))
    for title, days_ago in NEW_COPIES:
        copy = Copy.objects.create(movie=Movie.objects.get(title=title))
        Copy.objects.filter(id=copy.id).update(added_at=now - timedelta(days=days_ago))

    # When each disc that's out now left the shelf: the history must have it back by then.
    out_since = {}
    for username, title, days_out in OUT_ALREADY:
        copy = Copy.objects.filter(movie__title=title).first()
        rental = Rental.objects.create(copy=copy, user=users[username])
        taken_at = now - timedelta(days=days_out)
        # taken_at is auto_now_add, so the insert set it to now; it goes back after.
        Rental.objects.filter(id=rental.id).update(taken_at=taken_at)
        out_since[copy.id] = taken_at

    rng = random.Random(RANDOM_SEED)
    movie_of_copy = dict(Copy.objects.values_list('id', 'movie_id'))
    # When each disc is next on the shelf, starting from the day it arrived, so no copy is taken
    # before it was bought or is with two people at once.
    back_at = dict(Copy.objects.values_list('id', 'added_at'))
    rentals = []
    taken_ats = []
    for days_ago in range(HISTORY_DAYS, 0, -1):
        for username in FAMILY:
            if rng.random() >= CHANCE_OF_A_VISIT[username]:
                continue
            taken_at = now - timedelta(days=days_ago, hours=rng.randint(0, 12))
            movies_this_visit = set()
            for _ in range(rng.choice(MOVIES_PER_VISIT)):
                # Up to nine days, but never past the day before the seed, so the history is
                # all back and nothing piles up as returned today.
                kept_days = min(rng.randint(1, 9), days_ago - 1)
                kept = timedelta(days=kept_days, hours=rng.randint(2, 12))
                returned_at = min(taken_at + kept, now - timedelta(hours=1))
                on_the_shelf = [
                    copy_id for copy_id, back in back_at.items()
                    if back <= taken_at
                    and returned_at <= out_since.get(copy_id, now)
                    and movie_of_copy[copy_id] not in movies_this_visit
                ]
                copy_id = rng.choice(on_the_shelf)
                back_at[copy_id] = returned_at
                movies_this_visit.add(movie_of_copy[copy_id])
                rentals.append(Rental(copy_id=copy_id, user=users[username], returned_at=returned_at))
                taken_ats.append(taken_at)

    created = Rental.objects.bulk_create(rentals)
    # taken_at is auto_now_add, so the insert set it to now; the history's dates go back after.
    for rental, taken_at in zip(created, taken_ats):
        rental.taken_at = taken_at
    Rental.objects.bulk_update(created, ['taken_at'], batch_size=500)


class Migration(migrations.Migration):
    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
