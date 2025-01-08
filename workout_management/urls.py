from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkoutPlanViewSet, WorkoutExerciseViewSet

# Create a router and register the WorkoutPlanViewSet
router = DefaultRouter()
router.register(r'workout_plan', WorkoutPlanViewSet, basename='workout_plan')
router.register(r'workout_exercises', WorkoutExerciseViewSet, basename='workout-exercise')


urlpatterns = [
    path('', include(router.urls)),
]