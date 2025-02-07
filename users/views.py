from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterUserSerializer, LoginUserSerializer, UpdateUserProfileSerializer, UserProfileSerializer
from utils.store_token import set_jwt_cookie
from .permissions import IsNotAuthenticated
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from .throttling import LoginRateThrottle
from rest_framework.exceptions import Throttled
from .models import User, FitnessGoal
from fitness_goal.serializers import ListFitnessGoalSerializer
from django.db.models import Count, Q
from django.core.cache import cache


class RegisterUser(generics.CreateAPIView):
    serializer_class = RegisterUserSerializer
    permission_classes = [IsNotAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Create the response
            response = Response({
                'message': 'User registered successfully',
                'user': {
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_trainer': user.is_trainer,
                    'refresh_token': refresh_token,
                    'access_token': access_token
                }
            }, status=status.HTTP_201_CREATED)

            # store jwt token in a secure way
            set_jwt_cookie(response, access_token, refresh_token)

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginUser(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginUserSerializer
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Create the response
            response = Response({
                'message': 'Login successful',
                'user': {
                    'refresh_token': refresh_token,
                    'access_token': access_token
                }
            }, status=status.HTTP_200_OK)

            # Store JWT tokens securely
            set_jwt_cookie(response, access_token, refresh_token)

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def handle_exception(self, exc):
        # Custom handling for Throttled exception
        if isinstance(exc, Throttled):
            custom_response_data = {
                "message": "You have made too many login attempts. Please try again later.",
                "available_in": f"{exc.wait} seconds"
            }
            return Response(custom_response_data, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Handle other exceptions as usual
        return super().handle_exception(exc)

class LogoutUser(APIView):
    serializer_class = None

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()  # Blacklist the token
        except Exception as e:
            return Response(
                {"error": "Token could not be blacklisted, login again please", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Clear the cookies
        response = Response(
            {"message": "Logout successful"},
            status=status.HTTP_200_OK,
        )
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        return response


class CurrentUserDetail(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get(self, request):
        user = request.user
        cache_key = f"user_detail_{user.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        # Deactivate expired fitness goals
        FitnessGoal.objects.deactivate_expired(user=user)

        # Prefetch fitness goals related data
        fitness_goals_queryset = (
            user.fitness_goals
            .select_related('user')
            .annotate(
                total_goals=Count('id'),
                active_goals=Count('id', filter=Q(is_active=True))
            )
        )

        # Apply `is_active` filter if provided
        is_active = request.query_params.get('is_active_goals')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            fitness_goals_queryset = fitness_goals_queryset.filter(is_active=is_active)

        # Fetch aggregated metadata
        metadata = fitness_goals_queryset.aggregate(
            total_goals=Count('id'),
            active_goals=Count('id', filter=Q(is_active=True))
        )
        metadata['inactive_goals'] = metadata['total_goals'] - metadata['active_goals']

        # Serialize the data
        serializer = self.serializer_class(user)
        response_data = serializer.data
        response_data['fitness_goals'] = ListFitnessGoalSerializer(
            fitness_goals_queryset, many=True
        ).data
        response_data['metadata_for_goals'] = metadata

        # Cache the data for 1 hour
        cache.set(cache_key, response_data, timeout=3600)

        return Response(response_data)


class UserProfileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    lookup_field = 'unique_id'

    def get_queryset(self):
        """
        Prefetch fitness goals and deactivate expired ones before returning the queryset.
        """
        queryset = User.objects.prefetch_related('fitness_goals')
        return queryset

    def retrieve(self, request, *args, **kwargs):
        unique_id = self.kwargs.get('unique_id')
        cache_key = f"user_profile_{unique_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        # Fetch the user profile
        instance = self.get_object()

        FitnessGoal.objects.deactivate_expired(user=instance)

        fitness_goals = instance.fitness_goals.all()

        # Apply filters (if provided)
        is_active = request.query_params.get('is_active_goals')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            fitness_goals = fitness_goals.filter(is_active=is_active)

        # Collect metadata
        total_goals = instance.fitness_goals.count()
        active_goals = instance.fitness_goals.filter(is_active=True).count()
        inactive_goals = total_goals - active_goals

        serializer = self.get_serializer(instance)
        response_data = serializer.data
        response_data['fitness_goals'] = ListFitnessGoalSerializer(fitness_goals, many=True).data
        response_data['metadata_for_goals'] = {
            'total_goals': total_goals,
            'active_goals': active_goals,
            'inactive_goals': inactive_goals,
        }

        # Cache the data for 1 hour
        cache.set(cache_key, response_data, timeout=3600)

        return Response(response_data)


class CurrentUserProfileUpdate(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateUserProfileSerializer

    def patch(self, request):
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profile updated successfully.",
                "user": serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RefreshAccessTokenView(APIView):
    permission_classes = [AllowAny]
    serializer_class = None

    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        # Check if refresh token is provided in the body
        if not refresh_token:
            return self.logout_user_response('Refresh token not provided, you should login again')

        try:
            # Validate and use the refresh token to issue new tokens
            refresh = RefreshToken(refresh_token)

            # Issue new tokens
            new_access_token = str(refresh.access_token)
            new_refresh_token = str(refresh)  # Rotated refresh token

            # Create response with new tokens
            response = Response({
                'message': 'Access token refreshed',
                'access_token': new_access_token,
                'refresh_token': new_refresh_token,
            }, status=status.HTTP_200_OK)

            # Securely store the tokens
            set_jwt_cookie(response, new_access_token, new_refresh_token)

            return response

        except Exception as e:
            # Refresh token is invalid or expired
            return self.logout_user_response(f'Refresh token is invalid or expired {e}')

    def logout_user_response(self, message):
        """Helper to handle user logout and create a response"""
        try:
            refresh_token = self.request.COOKIES.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()  # Blacklist the token

        except Exception as e:
            pass

        # Clear the cookies
        response = Response({'error': message}, status=status.HTTP_401_UNAUTHORIZED)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        return response