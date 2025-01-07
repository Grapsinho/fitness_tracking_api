from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExerciseViewSet

# Create a router and register the ExerciseViewSet
router = DefaultRouter()
router.register(r'', ExerciseViewSet, basename='exercises')

urlpatterns = [
    path('', include(router.urls)),
]