from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

class IsTrainer(BasePermission):
    message = "You have to be a trainer to create exercises or workouts"
    def has_permission(self, request, view):
        if not request.user.is_trainer:
            raise PermissionDenied(self.message)
        
        return True