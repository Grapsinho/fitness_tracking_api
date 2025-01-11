from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from .models import WorkoutPlan, WorkoutExercise
from .serializers import CreateWorkoutExerciseSerializer, CreateWorkoutPlanSerializer, WorkoutPlanDetailSerializer, UpdateWorkoutExerciseSerializer
from rest_framework.permissions import IsAuthenticated
from exercises.permissions import IsTrainer
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from django.utils.translation import gettext_lazy as _
from uuid import UUID
from django.db import transaction, IntegrityError

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

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

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
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
        serializer = UpdateWorkoutExerciseSerializer(instance, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Workout exercise updated successfully.", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=["patch"], url_path="bulk-update", url_name="bulk_update")
    def bulk_update(self, request, *args, **kwargs):
        """
        Handle bulk updates for workout exercises using batch updates.
        """

        with transaction.atomic():
            data = request.data.get("workout_exercises", [])
            if not data:
                return Response({"detail": "No data provided for bulk update."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Validate data and prepare instance map
                instance_map, workout_plan_id = self._validate_bulk_update_data(data)

                # Batch update: Nullify orders
                self._nullify_orders_batch(instance_map)

                # Batch update: Apply updates
                self._save_updates_batch(instance_map)

                return Response({"message": "Update successful."}, status=status.HTTP_200_OK)

            except (WorkoutExercise.DoesNotExist, ValidationError) as e:
                return Response({"detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)
            except IntegrityError as e:
                return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                return Response({"detail": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    # util methods to update multiple instances
    def _validate_bulk_update_data(self, data):
        """
        Validate the bulk update payload and prepare instance mapping efficiently.
        """
        if not data:
            raise ValidationError("No data provided for validation.")

        # Extract IDs from the payload
        instance_ids = [item.get("id") for item in data if "id" in item]
        if not instance_ids:
            raise ValidationError("Each item in the payload must include an 'id' field.")

        # Batch fetch all instances
        instances = WorkoutExercise.objects.filter(id__in=instance_ids).select_related("exercise")
        instance_map = {instance.id: instance for instance in instances}

        # Validate all provided IDs exist in the database
        missing_ids = set(instance_ids) - set(instance_map.keys())
        if missing_ids:
            raise ValidationError(f"The following IDs were not found: {', '.join(map(str, missing_ids))}")

        # Initialize variables for validation
        workout_plan_id = None
        new_orders = set()
        new_exercises = set()
        validated_instance_map = {}

        # Validate each item in the payload
        for item in data:
            instance_id = item.get("id")
            new_order = item.get("order")
            new_exercise_id = item.get("exercise")
            repetitions = item.get("repetitions")
            sets = item.get("sets")
            rest_time = item.get("rest_time")

            # Fetch the instance
            instance = instance_map[instance_id]

            # Ensure all instances belong to the same workout plan
            if workout_plan_id is None:
                workout_plan_id = instance.workout_plan_id
            elif workout_plan_id != instance.workout_plan_id:
                raise ValidationError(f"All exercises must belong to the same workout plan. Mismatch found for ID: {instance_id}")

            # Check for duplicate orders in the payload
            if new_order is not None:
                if new_order in new_orders:
                    raise ValidationError(f"Duplicate order '{new_order}' found in the payload.")
                if new_order < 1:
                    raise ValidationError(f"Invalid order '{new_order}' for ID: {instance_id}. Order must be a greater than 0.")
                new_orders.add(new_order)

            # Check for duplicate exercise IDs in the payload
            if new_exercise_id is not None:
                if new_exercise_id in new_exercises:
                    raise ValidationError(f"Duplicate exercise ID '{new_exercise_id}' found in the payload.")
                new_exercises.add(new_exercise_id)

            # Prepare the validated instance map
            validated_instance_map[instance_id] = {
                "instance": instance,
                "new_order": new_order,
                "new_exercise_id": new_exercise_id,
                "repetitions": repetitions,
                "sets": sets,
                "rest_time": rest_time,
            }

        return validated_instance_map, workout_plan_id

    def _nullify_orders_batch(self, instance_map):
        """
        Batch nullify orders for instances being updated.
        """
        instances_to_nullify = [item["instance"] for item in instance_map.values() if item["new_order"] is not None]
        for instance in instances_to_nullify:
            instance.order = 0
        WorkoutExercise.objects.bulk_update(instances_to_nullify, ["order"])
    
    def _save_updates_batch(self, instance_map):
        """
        Batch save updated fields for all instances.
        """
        instances_to_update = []
        for item in instance_map.values():
            instance = item["instance"]
            if item["new_order"] is not None:
                instance.order = item["new_order"]
            if item["new_exercise_id"] is not None:
                instance.exercise_id = item["new_exercise_id"]
            if item["repetitions"] is not None:
                instance.repetitions = item["repetitions"]
            if item["sets"] is not None:
                instance.sets = item["sets"]
            if item["rest_time"] is not None:
                instance.rest_time = item["rest_time"]
            instances_to_update.append(instance)
        WorkoutExercise.objects.bulk_update(instances_to_update, ["order", "exercise_id", "repetitions", "sets", "rest_time"])


    @action(detail=True, methods=['delete'], url_path='delete', url_name='delete')
    def delete_workout_exercise(self, request, pk=None, *args, **kwargs):
        """
        Custom route for deleting a specific workout exercise.
        """
        instance = self.get_object()
        instance.delete()
        return Response({"detail": "Workout exercise deleted successfully."}, status=status.HTTP_200_OK)
    
