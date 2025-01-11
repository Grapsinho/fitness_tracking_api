from rest_framework import serializers
from .models import WorkoutPlan, WorkoutExercise
from django.db.models import Q
from exercises.serializers import ListExerciseSerializer
from rest_framework.exceptions import ValidationError
from plan_recommendations.models import GoalWorkoutMapping

class CreateWorkoutPlanSerializer(serializers.ModelSerializer):

    WORKOUT_TAG_CHOICES = [
        ('Weight Loss', 'Weight Loss'),
        ('Strength Building', 'Strength Building'),
        ('Cardiovascular Fitness', 'Cardiovascular Fitness'),
        ('Flexibility', 'Flexibility'),
        ('BodyBuilding', 'BodyBuilding'),
    ]
    
    tags = serializers.ListField(
        child=serializers.ChoiceField(choices=WORKOUT_TAG_CHOICES),
        required=True,
    )

    class Meta:
        model = WorkoutPlan
        fields = ('title', 'difficulty_level', 'description', 'workout_banner', "tags")
    
    def validate_tags(self, tags):
        print(tags)
        if not tags:
            raise serializers.ValidationError("At least one tag must be provided.")
    
        if not isinstance(tags, list):
            raise ValidationError("Tags required must be a list.")
        if not all(isinstance(item, str) for item in tags):
            raise ValidationError("All items in the tags list must be strings.")
        
        return tags

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
                tags=validated_data['tags']
            )
        else:
            workout_plan = WorkoutPlan.objects.create(
                title=validated_data['title'],
                created_by=user,
                difficulty_level=validated_data['difficulty_level'],
                description=validated_data['description'],
                tags=validated_data['tags']
            )
        
        for tag in validated_data['tags']:
            GoalWorkoutMapping.objects.get_or_create(
                goal_type=tag,
                workout_plan=workout_plan
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
                "detail": f"The order ({order}) or exercise ({exercise.name}) already exists in the workout plan."
            })

        return attrs

class UpdateWorkoutExerciseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = WorkoutExercise
        fields = ("id", 'order', 'repetitions', 'sets', 'rest_time', 'exercise')
    
    def validate(self, attrs):
        """
        Validate the order and uniqueness of the exercise within the workout plan.
        """

        pk = self.instance.workout_plan_id
        exercise = attrs.get('exercise')
        order = attrs.get('order')

        if WorkoutExercise.objects.filter(
            Q(workout_plan_id=pk, order=order) | 
            Q(workout_plan_id=pk, exercise=exercise)
        ).exists():
            raise serializers.ValidationError({
                "detail": f"The order ({order}) or exercise already exists in the workout plan."
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