from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import FitnessGoal, User
from django.core.cache import cache

@receiver([post_save, post_delete], sender=FitnessGoal)
def invalidate_current_user_cache(sender, instance, **kwargs):
    """
    Invalidate cache for CurrentUserDetail when fitness goals change.
    Also invalidate UserProfileView cache since it includes fitness goal metadata.
    """
    # Invalidate CurrentUserDetail cache
    current_user_cache_key = f"user_detail_{instance.user.id}"
    cache.delete(current_user_cache_key)

    # Invalidate UserProfileView cache
    user_profile_cache_key = f"user_profile_{instance.user.unique_id}"
    cache.delete(user_profile_cache_key)

@receiver([post_save, post_delete], sender=User)
def invalidate_user_profile_cache(sender, instance, **kwargs):
    """
    Invalidate cache for UserProfileView when user profile changes.
    """
    user_profile_cache_key = f"user_profile_{instance.unique_id}"
    cache.delete(user_profile_cache_key)