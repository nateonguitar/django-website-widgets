from django.db import migrations


# Name, type, age in years, about.
ANIMALS = [
    ('Biscuit', 'dog', 3, 'A beagle who has never met a sandwich he didn\'t like.'),
    ('Juniper', 'dog', 7, 'Calm, gray in the muzzle, and very good at naps.'),
    ('Rocket', 'dog', 1, 'Fast, loud, and still learning what "sit" means.'),
    ('Mochi', 'cat', 2, 'Sits on whatever you are reading.'),
    ('Pepper', 'cat', 9, 'Prefers a quiet house and a sunny windowsill.'),
    ('Tofu', 'cat', 4, 'Will fetch hair ties, but only on his terms.'),
]


def seed(apps, schema_editor):
    Animal = apps.get_model('website', 'Animal')
    for name, animal_type, age_years, about in ANIMALS:
        Animal.objects.create(name=name, animal_type=animal_type, age_years=age_years, about=about)


class Migration(migrations.Migration):
    dependencies = [
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
