from rest_framework_simplejwt.tokens import AccessToken
from users.models import User
from rest_framework.exceptions import AuthenticationFailed

def get_user_from_jwt(token):
    try:
        access_token = AccessToken(token)

        # i know i should use unique_id here but i forget to do that from the first time so now i'm tired
        user_id = access_token['user_id']

        # Get the user from the database
        user = User.objects.get(id=user_id)
        return user
    except User.DoesNotExist:
        raise AuthenticationFailed("User not found")
    except Exception as e:
        raise AuthenticationFailed("Invalid or expired token")