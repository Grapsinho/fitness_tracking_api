from django.contrib import admin
from .models import User, FitnessGoal

admin.site.register(User)
admin.site.register(FitnessGoal)

from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.token_blacklist.admin import OutstandingTokenAdmin

admin.site.unregister(OutstandingToken)

@admin.register(OutstandingToken)
class CustomOutstandingTokenAdmin(OutstandingTokenAdmin):
    list_display = ('user', 'jti', 'created_at', 'expires_at')  # Customize the fields displayed

    # Add a custom admin action to delete all tokens
    actions = ['delete_all_tokens']

    def delete_all_tokens(self, request, queryset):
        queryset.delete()
        self.message_user(request, "Selected tokens have been deleted.")
    delete_all_tokens.short_description = "Delete selected tokens"