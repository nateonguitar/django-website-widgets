from django.db import models


class AnimalType(models.TextChoices):
    DOG = 'dog', 'Dog'
    CAT = 'cat', 'Cat'


class Animal(models.Model):
    name = models.CharField(max_length=100)
    animal_type = models.CharField(max_length=3, choices=AnimalType.choices)
    age_years = models.PositiveSmallIntegerField()
    about = models.CharField(max_length=200)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
