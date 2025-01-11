from django.db import models
from users.models import FitnessGoal
from workout_management.models import WorkoutPlan

# Create your models here.

class GoalWorkoutMapping(models.Model):
    goal_type = models.CharField(max_length=35, choices=FitnessGoal.GOAL_CHOICES)
    workout_plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE)