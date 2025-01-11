from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from users.models import FitnessGoal
from .models import GoalWorkoutMapping
from workout_management.models import WorkoutPlan
from workout_management.serializers import WorkoutPlanDetailSerializer
from django.db.models import Prefetch

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

        # Prefetch related mappings to reduce query count
        goal_mappings = GoalWorkoutMapping.objects.filter(goal_type__in=active_goals).select_related('workout_plan')
        prefetch_mapping = Prefetch('goalworkoutmapping_set', queryset=goal_mappings)

        # Fetch distinct workout plans related to active goals with prefetch
        recommended_plans = WorkoutPlan.objects.filter(
            goalworkoutmapping__goal_type__in=active_goals
        ).distinct().select_related('created_by').prefetch_related(prefetch_mapping, "workout_exercises__exercise")

        # Manually instantiate the paginator
        paginator = self.pagination_class()

        # Apply pagination manually
        page = paginator.paginate_queryset(recommended_plans, request)
        if page is not None:
            serializer = WorkoutPlanDetailSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = WorkoutPlanDetailSerializer(recommended_plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)