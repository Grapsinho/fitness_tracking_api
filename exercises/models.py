from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
from users.models import User

class Exercise(models.Model):

    EXERCISE_CATEGORIES = [
        ('Strength', 'Strength'),
        ('Cardio', 'Cardio'),
        ('Yoga', 'Yoga'),
        ('Flexibility', 'Flexibility'),
        ('Calisthenics', 'Calisthenics'),
        ('Aerobic', 'Aerobic')
    ]

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_exercises')

    name = models.CharField(max_length=50)
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    description = models.TextField(help_text="Additional details about the exercise")
    category = models.CharField(max_length=50, choices=EXERCISE_CATEGORIES, help_text="Type of exercise")
    equipment = models.JSONField(default=list)
    repetitions = models.PositiveIntegerField(default=0)
    sets = models.PositiveIntegerField(default=0)
    muscle_group = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = _("Exercises")
        unique_together = ('name', 'created_by')

    def __str__(self):
        return f"exercise name: {self.name}"