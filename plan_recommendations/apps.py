from django.apps import AppConfig


class PlanRecommendationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plan_recommendations'

    def ready(self):
        import plan_recommendations.signals
