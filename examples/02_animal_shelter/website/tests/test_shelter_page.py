from django.test import TestCase


class ShelterPageTestCase(TestCase):
    def test_shelter_page__lists_every_animal_with_its_type__when_opened(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        for name in ('Biscuit', 'Juniper', 'Rocket', 'Mochi', 'Pepper', 'Tofu'):
            self.assertContains(response, name)
        html = response.content.decode()
        self.assertEqual(html.count('class="animal-card"\n    data-animal-type="dog"'), 3)
        self.assertEqual(html.count('class="animal-card"\n    data-animal-type="cat"'), 3)

    def test_shelter_page__offers_all_dogs_and_cats__when_opened(self):
        response = self.client.get('/')

        self.assertContains(response, '>All</button>')
        self.assertContains(response, '>Dogs</button>')
        self.assertContains(response, '>Cats</button>')
