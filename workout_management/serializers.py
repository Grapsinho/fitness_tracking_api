from rest_framework import serializers
from .models import WorkoutPlan, WorkoutExercise
from django.db.models import Q
from exercises.serializers import ListExerciseSerializer

class CreateWorkoutPlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkoutPlan
        fields = ('title', 'difficulty_level', 'description', 'workout_banner')

    def create(self, validated_data):

        user = self.context['request'].user

        workout_banner = validated_data.get('workout_banner')

        if workout_banner:

            workout_plan = WorkoutPlan.objects.create(
                title=validated_data['title'],
                created_by=user,
                difficulty_level=validated_data['difficulty_level'],
                description=validated_data['description'],
                workout_banner=workout_banner,
            )
        else:
            workout_plan = WorkoutPlan.objects.create(
                title=validated_data['title'],
                created_by=user,
                difficulty_level=validated_data['difficulty_level'],
                description=validated_data['description'],
            )

        return workout_plan

class CreateWorkoutExerciseSerializer(serializers.ModelSerializer):

    exercise_details = ListExerciseSerializer(source='exercise', read_only=True)

    class Meta:
        model = WorkoutExercise
        fields = [
            "id",
            'workout_plan',
            'exercise',
            'exercise_details',
            'order',
            'repetitions',
            'sets',
            'rest_time',
        ]
    
    def validate(self, attrs):
        """
        Validate the order and uniqueness of the exercise within the workout plan.
        """
        workout_plan = attrs.get('workout_plan')
        exercise = attrs.get('exercise')
        order = attrs.get('order')

        if WorkoutExercise.objects.filter(
            Q(workout_plan=workout_plan, order=order) | 
            Q(workout_plan=workout_plan, exercise=exercise)
        ).exists():
            raise serializers.ValidationError({
                "detail": "The order or exercise already exists in the workout plan."
            })


        return attrs

class WorkoutPlanDetailSerializer(serializers.ModelSerializer):
    workout_exercises = CreateWorkoutExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = WorkoutPlan
        fields = [
            "id",
            'unique_id',
            'created_by',
            'title',
            'description',
            'difficulty_level',
            'workout_banner',
            'created_at',
            'updated_at',
            'workout_exercises',
        ]
        read_only_fields = ['unique_id', 'created_at', 'updated_at']