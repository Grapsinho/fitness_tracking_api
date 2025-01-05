from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

# class IsTrainer(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.is_trainer
    
class IsNotAuthenticated(BasePermission):
    """
    Allows access only to unauthenticated users.
    """

    def has_permission(self, request, view):
        auth = JWTAuthentication()
        try:
            result = auth.authenticate(request)
            # If authentication succeeds, user is authenticated
            if result is not None:
                return False
        except AuthenticationFailed:
            pass  # Authentication failed, treat user as unauthenticated

        return True