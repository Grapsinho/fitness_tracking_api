from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterUserSerializer, LoginUserSerializer, UpdateUserProfileSerializer
from utils.store_token import set_jwt_cookie
from .permissions import IsNotAuthenticated
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from .throttling import LoginRateThrottle
from rest_framework.exceptions import Throttled


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

    def get(self, request):
        user = request.user
        return Response({
            'username': user.first_name,
            'email': user.email,
            'weight': user.weight,
            'height': user.height,
            'gender': user.gender,
        }, status=200)


class CurrentUserProfileUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user

        serializer = UpdateUserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profile updated successfully.",
                "user": serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RefreshAccessTokenView(APIView):
    permission_classes = [AllowAny]

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