from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from users.models import FitnessGoal
from workout_management.models import WorkoutPlan
from django.core.cache import cache

@receiver([post_save, post_delete], sender=FitnessGoal)
@receiver([post_save, post_delete], sender=WorkoutPlan)
def invalidate_recommendations_cache(sender, instance, **kwargs):
    # Increment cache version for the affected user(s)
    if isinstance(instance, FitnessGoal):
        user_id = instance.user.id
        cache_key = f"recommendation_version_{user_id}"
    elif isinstance(instance, WorkoutPlan):
        # Update version for all users (if needed)
        user_id = None  # Example: implement logic to find affected users
        cache_key = f"recommendation_version_{user_id}"  # Adjust as per logic

    # Increment version
    current_version = cache.get(cache_key, 1)
    cache.set(cache_key, current_version + 1)