from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

# class IsTrainer(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.is_trainer
    
class IsNotAuthenticated(BasePermission):
    """
    Allows access only to unauthenticated users.
    """

    message = "You are already logged in. Please log out to register."

    def has_permission(self, request, view):
        refresh_token = request.COOKIES.get('refresh_token')
        access_token = request.COOKIES.get('access_token')

        if refresh_token or access_token:
            raise PermissionDenied(self.message)

        return True