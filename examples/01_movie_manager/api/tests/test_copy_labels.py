import re
from unittest.mock import patch

from django.test import TestCase

from api.models import Copy, CopyLabel, Movie


class CopyLabelsTestCase(TestCase):
    def test_copy_labels__are_four_letters_a_hyphen_and_four_digits__when_seeded(self):
        labels = list(Copy.objects.values_list('label', flat=True))

        self.assertTrue(all(re.fullmatch(r'[a-z]{4}-[0-9]{4}', label) for label in labels))
        self.assertEqual(len(labels), len(set(labels)))

    def test_create_copies__skips_a_label_already_taken__when_one_is_generated(self):
        movie = Movie.objects.get(title='Die Hard')
        taken = Copy.objects.first().label
        generated = iter([taken, 'aaaa-0001', 'aaaa-0002'])

        with patch.object(CopyLabel, 'generate', side_effect=lambda: next(generated)):
            copies = Copy.objects.create_copies(movie, 2)

        self.assertEqual(sorted(copy.label for copy in copies), ['aaaa-0001', 'aaaa-0002'])

    def test_create_copies__gives_each_copy_its_own_label__when_a_batch_repeats_one(self):
        movie = Movie.objects.get(title='Die Hard')
        generated = iter(['aaaa-0001', 'aaaa-0001', 'aaaa-0002'])

        with patch.object(CopyLabel, 'generate', side_effect=lambda: next(generated)):
            copies = Copy.objects.create_copies(movie, 2)

        self.assertEqual(sorted(copy.label for copy in copies), ['aaaa-0001', 'aaaa-0002'])
