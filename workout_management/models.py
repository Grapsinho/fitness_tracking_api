from django.db import models
import uuid
from users.models import User
from exercises.models import Exercise
from django.utils.translation import gettext_lazy as _
from django.db.models import F
from django.core.exceptions import ValidationError

class WorkoutPlan(models.Model):
    """
    Represents a workout plan created by a trainer.
    """

    WORKOUT_DIFFICULTY_LEVEL = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    WORKOUT_TAG_CHOICES = [
        ('Weight Loss', 'Weight Loss'),
        ('Strength Building', 'Strength Building'),
        ('Cardiovascular Fitness', 'Cardiovascular Fitness'),
        ('Flexibility', 'Flexibility'),
        ('BodyBuilding', 'BodyBuilding'),
    ]


    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_plans')
    title = models.CharField(max_length=100, help_text="Title of the workout plan")
    description = models.TextField(blank=True, help_text="Details about the workout plan")
    difficulty_level = models.CharField(max_length=20, choices=WORKOUT_DIFFICULTY_LEVEL)
    workout_banner = models.ImageField(upload_to='workout_banners/', default='workout_banners/no-img-banner.jpg',blank=True, null=True)
    tags = models.JSONField(
        default=list,
        help_text="Tags describing the plan, e.g., ['strength', 'weight_loss']",
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Check if all tags in the list are valid
        if self.tags:
            invalid_tags = [tag for tag in self.tags if tag not in dict(self.WORKOUT_TAG_CHOICES)]
            if invalid_tags:
                raise ValidationError(f"Invalid tags: {', '.join(invalid_tags)}")
        super().clean()

    def delete(self, *args, **kwargs):
        # Delete the workout banner file
        if self.workout_banner and self.workout_banner.name != 'workout_banners/no-img-banner.jpg':
            self.workout_banner.delete(save=False)
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name_plural = _("Workout Plans")
    
    def __str__(self):
        return f"Workout Plan: {self.title} by {self.created_by}"


class WorkoutExercise(models.Model):
    """
    Represents the linking table between WorkoutPlan and Exercise.
    """

    workout_plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='workout_exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='workout_exercises')
    order = models.PositiveIntegerField(default=1, help_text="Order of the exercise in the workout plan")
    repetitions = models.PositiveIntegerField(default=0, help_text="Number of repetitions for this exercise")
    sets = models.PositiveIntegerField(default=0, help_text="Number of sets for this exercise")
    rest_time = models.DurationField(blank=True, null=True, help_text="Rest time after completing this exercise")

    class Meta:
        verbose_name_plural = _("Workout Exercises")
        unique_together = ('workout_plan', 'exercise', 'order')
        ordering = ['order']

    def delete(self, *args, **kwargs):
        """
        Override the delete method to adjust the order of other exercises in the workout plan.
        """
        # Cache the workout_plan ID and the order of the exercise being deleted
        workout_plan_id = self.workout_plan_id
        deleted_order = self.order

        # Call the default delete behavior
        super().delete(*args, **kwargs)

        # Adjust the order of remaining exercises
        WorkoutExercise.objects.filter(
            workout_plan_id=workout_plan_id,
            order__gt=deleted_order
        ).update(order=F("order") - 1)

    def __str__(self):
        return f"Workout: {self.workout_plan.title}, Exercise: {self.exercise.name}, Order: {self.order}"