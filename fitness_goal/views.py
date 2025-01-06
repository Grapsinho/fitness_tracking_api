from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from users.models import FitnessGoal
from .serializers import CreateFitnessGoalSerializer, ListFitnessGoalSerializer, UpdateFitnessGoalSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from django_filters.rest_framework import DjangoFilterBackend


class FitnessGoalViewSet(ModelViewSet):
    """
    ViewSet for managing Fitness Goals.
    """
    queryset = FitnessGoal.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "unique_id"
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']

    def get_serializer_class(self):
        """
        Return different serializers for different actions.
        """
        if self.action == 'list_goal':
            return ListFitnessGoalSerializer
        return CreateFitnessGoalSerializer
    
    def get_queryset(self):
        """
        Get queryset for current user
        """

        FitnessGoal.objects.deactivate_expired(self.request.user)
        return FitnessGoal.objects.filter(user=self.request.user)
    
    def get_object(self):
        try:
            obj = FitnessGoal.objects.get(unique_id=self.kwargs.get(self.lookup_field), user=self.request.user)
        except FitnessGoal.DoesNotExist:
            raise NotFound({"detail": "The requested fitness goal does not exist or you do not have permission to access it."})
        return obj
    
    @action(detail=False, methods=['get'], url_path='list', url_name='list')
    def list_goal(self, request, *args, **kwargs):
        """
        List goals with additional metadata.
        """
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        total_goals = queryset.count()
        active_goals = queryset.filter(is_active=True).count()
        inactive_goals = total_goals - active_goals
        metadata = {
            "total_goals": total_goals,
            "active_goals": active_goals,
            "inactive_goals": inactive_goals,
        }
        return Response({
            "metadata": metadata,
            "data": serializer.data
        })

    @action(detail=False, methods=['post'], url_path='create', url_name='create')
    def create_goal(self, request, *args, **kwargs):
        """
        Handle the creation of a fitness goal.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], url_path='update', url_name='update')
    def update_goal(self, request, unique_id=None, *args, **kwargs):
        """
        Custom route for updating a specific fitness goal.
        """
        instance = self.get_object()
        serializer = UpdateFitnessGoalSerializer(instance, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], url_path='delete', url_name='delete')
    def delete_goal(self, request, unique_id=None, *args, **kwargs):
        """
        Custom route for deleting a specific fitness goal.
        """
        instance = self.get_object()
        instance.delete()
        return Response({"detail": "Fitness goal deleted successfully."}, status=status.HTTP_200_OK)