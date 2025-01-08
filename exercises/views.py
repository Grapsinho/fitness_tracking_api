from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from .models import Exercise
from .serializers import CreateExerciseSerializer, ListExerciseSerializer, BulkCreateExerciseSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from django.utils.translation import gettext_lazy as _
from uuid import UUID
from .permissions import IsTrainer

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from rest_framework.pagination import PageNumberPagination

class ExercisePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ExerciseViewSet(ModelViewSet):
    """
    ViewSet for managing Exercises.
    """
    queryset = Exercise.objects.all().select_related("created_by")
    permission_classes = [IsAuthenticated]
    lookup_field = "unique_id"
    serializer_class = CreateExerciseSerializer

    pagination_class = ExercisePagination

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category', 'muscle_group', 'created_by']  # Exact match filters
    search_fields = ['name', 'description']  # Partial match for name
    ordering_fields = ['name', 'category', 'sets']

    def get_permissions(self):
        """
        Dynamically assign permissions based on request method.
        """
        if self.request.method in ['GET', "RETRIEVE", 'HEAD', 'OPTIONS']:
            return [permission() for permission in [IsAuthenticated]]
        return [permission() for permission in [IsAuthenticated, IsTrainer]]
        
    def get_serializer_class(self):
        """
        Return different serializers for different actions.
        """
        if self.action in ['list', 'retrieve']:
            return ListExerciseSerializer
        return CreateExerciseSerializer
    
    def get_object(self):

        """
        Retrieve an object based on the unique_id. 
        - For GET requests: Allow any authenticated user to access.
        - For non-GET requests: Restrict access to the trainer who created the exercise.
        """

        unique_id = self.kwargs.get(self.lookup_field)
        
        # Validate UUID format
        try:
            UUID(unique_id, version=4)
        except ValueError:
            raise NotFound({"detail": _("The provided unique ID is not in a valid format. Please check and try again.")})
        
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            try:
                obj = self.get_queryset().get(unique_id=unique_id)
            except Exercise.DoesNotExist:
                raise NotFound({"detail": "The requested exercise does not exist."})
            return obj

        try:
            obj = self.get_queryset().get(unique_id=self.kwargs.get(self.lookup_field), created_by=self.request.user)
        except Exercise.DoesNotExist:
            raise NotFound({"detail": "The requested exercise does not exist or you do not have permission to access it."})
        return obj
        
    @action(detail=False, methods=['post'], url_path='create', url_name='create')
    def create_exercise(self, request, *args, **kwargs):
        """
        Handle the creation of a exercise.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            detail = {
                "message": "Exercise created successfully",
                "data": serializer.data
            }
            return Response(detail, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='bulk-create', url_name='bulk_create')
    def bulk_create_exercises(self, request, *args, **kwargs):
        """
        Handle the creation of multiple exercises at once.
        """
        serializer = BulkCreateExerciseSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            exercises = serializer.save()
            return Response({
                "message": f"{len(exercises)} exercises created successfully.",
                "created_exercises": [exercise.name for exercise in exercises],
            }, status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    
    @action(detail=True, methods=['patch'], url_path='update', url_name='update')
    def update_exercise(self, request, unique_id=None, *args, **kwargs):
        """
        Custom route for updating a specific exercise.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], url_path='delete', url_name='delete')
    def delete_exercise(self, request, unique_id=None, *args, **kwargs):
        """
        Custom route for deleting a specific exercise.
        """
        instance = self.get_object()
        instance.delete()
        return Response({"detail": "Exercise deleted successfully."}, status=status.HTTP_200_OK)