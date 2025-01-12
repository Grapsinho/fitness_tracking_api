from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from users.models import FitnessGoal
from workout_management.models import WorkoutPlan
from workout_management.serializers import WorkoutPlanDetailSerializer
from django.core.cache import cache

from rest_framework.pagination import PageNumberPagination

class RecommendationPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class RecommendationView(APIView):
    """
    Optimized API endpoint to retrieve recommended workout plans for the current user.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = RecommendationPagination

    def get(self, request):
        user = request.user

        # Cache key and version
        cache_key = f"recommendations_user_{user.id}"
        version = cache.get(f"recommendation_version_{user.id}", 1)  # Default version is 1

        # Try to fetch recommendations from the cache
        cached_data = cache.get(cache_key, version=version)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        # Use values_list to fetch only relevant data for active goals
        active_goals = list(
            FitnessGoal.objects.filter(user=user, is_active=True)
            .values_list('goal_type', flat=True)
        )

        if not active_goals:
            return Response(
                {"detail": "You don't have any active fitness goals."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Fetch distinct workout plans related to active goals with prefetch
        recommended_plans = WorkoutPlan.objects.filter(
            goalworkoutmapping__goal_type__in=active_goals
        ).distinct().select_related('created_by').prefetch_related("workout_exercises__exercise")

        # Manually instantiate the paginator
        paginator = self.pagination_class()

        # Apply pagination manually
        page = paginator.paginate_queryset(recommended_plans, request)
        if page is not None:
            serializer = WorkoutPlanDetailSerializer(page, many=True)
            paginated_data = paginator.get_paginated_response(serializer.data).data
            # Cache the paginated response
            cache.set(cache_key, paginated_data, timeout=3600, version=version)
            return Response(paginated_data, status=status.HTTP_200_OK)

        serializer = WorkoutPlanDetailSerializer(recommended_plans, many=True)
        response_data = serializer.data

        # Cache the full response
        cache.set(cache_key, response_data, timeout=3600, version=version)

        return Response(response_data, status=status.HTTP_200_OK)