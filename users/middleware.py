from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.response import Response
from django.http import JsonResponse

from django.utils.deprecation import MiddlewareMixin
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from datetime import datetime, timezone
from utils.store_token import set_jwt_cookie

class TokenRefreshMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            # If no Authorization header or not Bearer type, skip the token validation
            return None

        # Extract the token from the Authorization header
        access_token = auth_header.split(' ')[1]
        refresh_token = request.COOKIES.get('refresh_token')

        # If no access token is present, skip (anonymous user)
        if not access_token:
            return None

        try:
            # Validate the access token
            token = AccessToken(access_token)

            if datetime.fromtimestamp(token['exp'], tz=timezone.utc) < datetime.now(tz=timezone.utc):
                raise TokenError("Token has expired")
            
        except (TokenError, InvalidToken) as e:
            # If access token is invalid or expired, try refreshing it
            if not refresh_token:
                return self.logout_user_response("Authentication required. Please log in again.", request)

            try:
                # Use the refresh token to issue new tokens
                refresh = RefreshToken(refresh_token)
                new_access_token = str(refresh.access_token)
                new_refresh_token = str(refresh)

                # Update cookies for the response
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access_token}'  # Pass the new token to the request
                request.new_tokens = {
                    'access_token': new_access_token,
                    'refresh_token': new_refresh_token,
                }

            except (TokenError, InvalidToken) as refresh_error:
                return self.logout_user_response(
                    f"Refresh token invalid or expired, you should login again: {refresh_error}", request
                )
            except Exception as e:
                return Response(
                    {"details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Exception as e:
            return Response(
                {"details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return None

    def process_response(self, request, response):
        # Attach new tokens if available
        if hasattr(request, 'new_tokens'):
            tokens = request.new_tokens
            set_jwt_cookie(response, tokens['access_token'], tokens['refresh_token'])
        return response

    def logout_user_response(self, message, request):
        """Handle user logout by clearing tokens"""
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except (InvalidToken, TokenError) as e:
            pass

        # Clear the cookies
        response = JsonResponse({'error': message}, status=401)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response