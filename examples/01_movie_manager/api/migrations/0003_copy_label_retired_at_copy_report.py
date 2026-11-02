import random

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import api.models


# A fixed seed, so every migrate and every test run gives the seeded copies the same labels.
LABEL_SEED = 1234


def label_existing_copies(apps, schema_editor):
    Copy = apps.get_model('api', 'Copy')
    rng = random.Random(LABEL_SEED)
    used = set()
    for copy in Copy.objects.order_by('id'):
        label = api.models.CopyLabel.generate(rng)
        while label in used:
            label = api.models.CopyLabel.generate(rng)
        used.add(label)
        copy.label = label
        copy.save(update_fields=['label'])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_seed_family_and_movies'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Nullable first: a callable default is computed once for every existing row, which the
        # unique constraint would refuse.
        migrations.AddField(
            model_name='copy',
            name='label',
            field=models.SlugField(db_index=False, editable=False, max_length=9, null=True),
        ),
        migrations.RunPython(label_existing_copies, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='copy',
            name='label',
            field=models.SlugField(default=api.models.CopyLabel.generate, editable=False, max_length=9, unique=True),
        ),
        migrations.AddField(
            model_name='copy',
            name='retired_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='CopyReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('scratched', 'Scratched or skips'), ('broken_case', 'Broken case'), ('lost', 'Lost'), ('other', 'Something else')], max_length=20)),
                ('notes', models.TextField(max_length=1000)),
                ('unrecoverable', models.BooleanField(default=False)),
                ('reported_at', models.DateTimeField(auto_now_add=True)),
                ('copy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='api.copy')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='copy_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-reported_at'],
            },
        ),
    ]
