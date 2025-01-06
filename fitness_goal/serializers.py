from rest_framework import serializers
from users.models import FitnessGoal
from datetime import date
from rest_framework.exceptions import ValidationError
from rest_framework import status

class CreateFitnessGoalSerializer(serializers.ModelSerializer):

    class Meta:
        model = FitnessGoal
        fields = ('goal_type', 'end_date', 'description')

    def validate_end_date(self, end_date):
        start_date = date.today()

        if end_date and end_date <= start_date:
            raise ValidationError({
                "end_date": "End date must be greater than the start date."
            })

        return end_date

    def create(self, validated_data):

        user = self.context['request'].user

        fitness_goal = FitnessGoal.objects.create(
            user=user,
            goal_type=validated_data['goal_type'],
            end_date=validated_data['end_date'],
            description=validated_data['description'],
        )

        return fitness_goal
    
class UpdateFitnessGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FitnessGoal
        fields = ('goal_type', 'end_date', 'description', 'start_date', "is_active")
    
    def validate(self, data):
        """
        Validate start_date and end_date.
        """
        start_date = data.get('start_date', self.instance.start_date if self.instance else None)
        end_date = data.get('end_date', self.instance.end_date if self.instance else None)

        # Ensure start_date is not in the future
        if start_date and start_date > date.today():
            raise ValidationError({
                "start_date": "Start date cannot be in the future."
            })

        # Ensure end_date is not earlier than or equal to start_date
        if end_date and start_date and end_date <= start_date:
            raise ValidationError({
                "end_date": "End date must be greater than the start date."
            })

        return data
    
class ListFitnessGoalSerializer(serializers.ModelSerializer):

    class Meta:
        model = FitnessGoal
        fields = ('goal_type', 'end_date', 'description', 'start_date', "is_active", "unique_id")