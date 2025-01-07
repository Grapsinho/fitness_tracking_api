from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from users.models import FitnessGoal
from .serializers import CreateFitnessGoalSerializer,  UpdateFitnessGoalSerializer, ListFitnessGoalSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from django.utils.translation import gettext_lazy as _
from uuid import UUID


class FitnessGoalViewSet(ModelViewSet):
    """
    ViewSet for managing Fitness Goals.
    """
    queryset = FitnessGoal.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "unique_id"
    serializer_class = CreateFitnessGoalSerializer
    
    def get_queryset(self):
        """
        Get goals for the current user, but this view is not used for listing all goals.
        """

        return FitnessGoal.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """
        Return different serializers for different actions.
        """
        if self.action == 'retrieve':
            return ListFitnessGoalSerializer
        return CreateFitnessGoalSerializer
    
    def get_object(self):
        unique_id = self.kwargs.get(self.lookup_field)
        
        # Validate UUID format
        try:
            UUID(unique_id, version=4)
        except ValueError:
            raise NotFound({"detail": _("The provided unique ID is not in a valid format. Please check and try again.")})

        try:
            obj = FitnessGoal.objects.get(unique_id=self.kwargs.get(self.lookup_field), user=self.request.user)
        except FitnessGoal.DoesNotExist:
            raise NotFound({"detail": "The requested fitness goal does not exist or you do not have permission to access it."})
        return obj

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