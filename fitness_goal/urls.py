from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FitnessGoalViewSet

# Create a router and register the FitnessGoalViewSet
router = DefaultRouter()
router.register(r'', FitnessGoalViewSet, basename='fitness-goal')

urlpatterns = [
    path('', include(router.urls)),
]