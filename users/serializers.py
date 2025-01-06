from rest_framework import serializers
from .models import User
from datetime import date
from rest_framework.exceptions import ValidationError
from rest_framework import status
from django.contrib.auth import authenticate

class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        required=True,
        error_messages={
            "min_length": "Password must be at least 8 characters long.",
        }
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'gender', 'date_of_birth', 'height', 'weight', 'is_trainer')

    def validate_date_of_birth(self, date_of_birth):
        today = date.today()
        if date_of_birth > today:
            raise ValidationError(
                detail={"date_of_birth": "Date of birth shouldn't be in the future."},
                code=status.HTTP_400_BAD_REQUEST
            )
        return date_of_birth

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            gender=validated_data.get('gender'),
            date_of_birth=validated_data.get('date_of_birth'),
            height=validated_data.get('height'),
            weight=validated_data.get('weight'),
        )

        return user

class LoginUserSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError(
                {"detail": "Invalid email or password."}
            )
        attrs['user'] = user  # Pass the authenticated user to the view
        return attrs
    
class UpdateUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'gender', 'date_of_birth', 
            'avatar', 'height', 'weight'
        ]

    def validate_date_of_birth(self, value):
        # Ensure date_of_birth is not in the future
        if value and value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'gender', 'date_of_birth', 
            'avatar', 'height', 'weight', 'unique_id'
        ]