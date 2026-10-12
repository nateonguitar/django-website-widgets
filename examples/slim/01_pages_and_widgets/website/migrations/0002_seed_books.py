from django.db import migrations


BOOKS = [
    ('The Hobbit', 'J. R. R. Tolkien', 1937),
    ('Nineteen Eighty-Four', 'George Orwell', 1949),
    ('To Kill a Mockingbird', 'Harper Lee', 1960),
    ('Dune', 'Frank Herbert', 1965),
    ('The Left Hand of Darkness', 'Ursula K. Le Guin', 1969),
]


class SeedBooks:
    """The shelf every page and test starts from, so `migrate` alone gives a working site."""

    @staticmethod
    def add(apps, schema_editor):
        book_model = apps.get_model('website', 'Book')
        book_model.objects.bulk_create([
            book_model(title=title, author=author, year=year)
            for title, author, year in BOOKS
        ])

    @staticmethod
    def remove(apps, schema_editor):
        book_model = apps.get_model('website', 'Book')
        book_model.objects.filter(title__in=[title for title, _author, _year in BOOKS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(SeedBooks.add, SeedBooks.remove),
    ]
