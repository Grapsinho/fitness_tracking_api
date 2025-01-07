from rest_framework import serializers
from .models import Exercise
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.db import IntegrityError

class CreateExerciseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Exercise
        fields = ('name', 'category', 'description', 'equipment', 'repetitions', 'sets', 'muscle_group')

    def validate_equipment(self, equipment):
        if not isinstance(equipment, list):
            raise ValidationError("Equipment required must be a list.")
        if not all(isinstance(item, str) for item in equipment):
            raise ValidationError("All items in the equipment list must be strings.")
        
        return equipment

    def create(self, validated_data):

        user = self.context['request'].user

        try:
            exercise = Exercise.objects.create(
                name=validated_data['name'],
                created_by=user,
                category=validated_data['category'],
                description=validated_data['description'],
                equipment=validated_data['equipment'],
                repetitions=validated_data['repetitions'],
                sets=validated_data['sets'],
                muscle_group=validated_data['muscle_group'],
            )
        except IntegrityError as e:
            if 'duplicate key value violates unique constraint' in str(e):
                raise ValidationError(
                    {"detail": f'An exercise with this name "{validated_data['name']}" already exists for you. Please choose a different name.'}
                )
            raise e

        return exercise

class BulkCreateExerciseSerializer(serializers.Serializer):
    exercises = CreateExerciseSerializer(many=True)

    def validate(self, data):
        """
        Validate the entire list of exercises.
        """
        if not data.get('exercises', []):
            raise ValidationError("No exercises provided for creation.")
        
        # Additional custom validations can go here (e.g., duplicate names).
        return data

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        exercises_data = validated_data['exercises']

        # Create multiple exercises in one transaction
        exercises = [
            Exercise(
                name=exercise_data['name'],
                created_by=user,
                category=exercise_data['category'],
                description=exercise_data['description'],
                equipment=exercise_data['equipment'],
                repetitions=exercise_data['repetitions'],
                sets=exercise_data['sets'],
                muscle_group=exercise_data['muscle_group'],
            )
            for exercise_data in exercises_data
        ]

        try:
            Exercise.objects.bulk_create(exercises)
        except IntegrityError as e:
            if 'duplicate key value violates unique constraint' in str(e):
                raise ValidationError(
                    {"detail": "One of your exercises name already exists for you. Please choose a different name."}
                )
            raise e
        return exercises
    
class ListExerciseSerializer(serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(read_only=True, slug_field='unique_id')

    class Meta:
        model = Exercise
        fields = ('name', 'category', 'description', 'equipment', 'repetitions', 'sets', 'muscle_group', "created_by", "unique_id", 'created_by')