from django.contrib import admin
from .models import WorkoutExercise, WorkoutPlan

# Register your models here.

admin.site.register(WorkoutExercise)
admin.site.register(WorkoutPlan)