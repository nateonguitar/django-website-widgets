from datetime import timedelta

from django.db import migrations
from django.db.models import Exists, OuterRef
from django.utils import timezone


# Movie title, which of its shelf copies (0 for the first by id), reporter, kind, notes,
# unrecoverable, days ago. Only copies on the shelf, so no one's open rental is touched.
REPORTS = [
    ('Die Hard', 0, 'alex', 'scratched', 'Freezes for a second during the vent scene.', False, 40),
    ('Finding Nemo', 0, 'jordan', 'other', 'The menu plays in French. The film itself is fine.', False, 75),
    ('Finding Nemo', 0, 'sam', 'broken_case', 'The hinge snapped; the disc is fine. Taped it.', False, 20),
    # Retires the copy, so one copy shows as out of rotation. The seeded history last returns
    # this copy 45 days ago, so nothing rents it after it was lost.
    ('Finding Nemo', 1, 'alex', 'lost', 'Lent it to a neighbour who moved away.', True, 30),
]


def seed_reports(apps, schema_editor):
    User = apps.get_model('api', 'User')
    Copy = apps.get_model('api', 'Copy')
    CopyReport = apps.get_model('api', 'CopyReport')
    Rental = apps.get_model('api', 'Rental')

    now = timezone.now()
    is_out = Exists(Rental.objects.filter(copy=OuterRef('pk'), returned_at__isnull=True))
    for title, index, username, kind, notes, unrecoverable, days_ago in REPORTS:
        copy = Copy.objects.filter(~is_out, movie__title=title).order_by('id')[index]
        report = CopyReport.objects.create(
            copy=copy,
            user=User.objects.get(username=username),
            kind=kind,
            notes=notes,
            unrecoverable=unrecoverable)
        reported_at = now - timedelta(days=days_ago)
        # reported_at is auto_now_add, so the insert set it to now; it goes back after.
        CopyReport.objects.filter(id=report.id).update(reported_at=reported_at)
        if unrecoverable:
            Copy.objects.filter(id=copy.id).update(retired_at=reported_at)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_copy_label_retired_at_copy_report'),
    ]

    operations = [
        migrations.RunPython(seed_reports, migrations.RunPython.noop),
    ]
