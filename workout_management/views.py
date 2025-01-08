from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from .models import WorkoutPlan, WorkoutExercise
from .serializers import CreateWorkoutExerciseSerializer, CreateWorkoutPlanSerializer, WorkoutPlanDetailSerializer
from rest_framework.permissions import IsAuthenticated
from exercises.permissions import IsTrainer
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from django.utils.translation import gettext_lazy as _
from uuid import UUID

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from rest_framework.pagination import PageNumberPagination

class WorkoutPlanPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class WorkoutPlanViewSet(ModelViewSet):
    """
    ViewSet for managing Workout Plan.
    """
    queryset = WorkoutPlan.objects.all().select_related("created_by").prefetch_related("workout_exercises__exercise")

    permission_classes = [IsAuthenticated]
    lookup_field = "unique_id"
    serializer_class = CreateWorkoutPlanSerializer

    pagination_class = WorkoutPlanPagination

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['difficulty_level', 'created_by']
    search_fields = ['title', 'description'] 
    ordering_fields = ['created_at', 'difficulty_level']

    def get_object(self):
        """
        Retrieve an object based on the unique_id. 
        - For GET requests: Allow any authenticated user to access.
        - For non-GET requests: Restrict access to the trainer who created the workout plan.
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
            except WorkoutPlan.DoesNotExist:
                raise NotFound({"detail": "The requested workout plan does not exist."})
            return obj

        try:
            obj = self.get_queryset().get(unique_id=self.kwargs.get(self.lookup_field), created_by=self.request.user)
        except WorkoutPlan.DoesNotExist:
            raise NotFound({"detail": "The requested workout plan does not exist or you do not have permission to access it."})
        return obj

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
            return WorkoutPlanDetailSerializer
        return CreateWorkoutPlanSerializer
        
    @action(detail=False, methods=['post'], url_path='create', url_name='create')
    def create_workout_plan(self, request, *args, **kwargs):
        """
        Handle the creation of a workout plan.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            detail = {
                "message": "Workout Plan created successfully",
                "data": serializer.data
            }
            return Response(detail, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    @action(detail=True, methods=['patch'], url_path='update', url_name='update')
    def update_workout_plan(self, request, unique_id=None, *args, **kwargs):
        """
        Custom route for updating a specific workout plan.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], url_path='delete', url_name='delete')
    def delete_workout_plan(self, request, unique_id=None, *args, **kwargs):
        """
        Custom route for deleting a specific workout plan.
        """
        instance = self.get_object()
        instance.delete()
        return Response({"detail": "Workout Plan deleted successfully."}, status=status.HTTP_200_OK)
    

class WorkoutExerciseViewSet(ModelViewSet):
    """
    ViewSet for managing Workout Exercises.
    """
    queryset = WorkoutExercise.objects.all().select_related("workout_plan", "exercise")
    permission_classes = [IsAuthenticated, IsTrainer]
    serializer_class = CreateWorkoutExerciseSerializer

    def get_object(self):
        """
        Filter the queryset to show only exercises related to workout plans created by the current user.
        """
        try:
            obj = self.queryset.get(
                pk=self.kwargs['pk'],
                workout_plan__created_by=self.request.user
            )
            return obj
        except WorkoutExercise.DoesNotExist:
            raise NotFound({"detail": "The requested workout exercise does not exist or you do not have permission to access it."})

    @action(detail=False, methods=['post'], url_path='create', url_name='create')
    def create_workout_exercise(self, request, *args, **kwargs):
        """
        Handle the creation of a workout exercise.
        """
        serializer = self.get_serializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Workout exercise created successfully.", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='update', url_name='update')
    def update_workout_exercise(self, request, *args, **kwargs):
        """
        Handle the update of a workout exercise.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Workout exercise updated successfully.", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='delete', url_name='delete')
    def delete_workout_exercise(self, request, pk=None, *args, **kwargs):
        """
        Custom route for deleting a specific workout exercise.
        """
        instance = self.get_object()
        instance.delete()
        return Response({"detail": "Workout exercise deleted successfully."}, status=status.HTTP_200_OK)
    
