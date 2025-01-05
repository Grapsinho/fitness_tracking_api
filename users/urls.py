from django.urls import path
from .views import RegisterUser, LoginUser, LogoutUser, CurrentUserManagement, RefreshAccessTokenView

urlpatterns = [
    path('register/', RegisterUser.as_view(), name='register'),
    path('login/', LoginUser.as_view(), name='login'),
    path('logout/', LogoutUser.as_view(), name='logout'),
    
    # get a current user
    path('current_user/', CurrentUserManagement.as_view(), name='current_user'),

    # refresh token
    path('token/refresh/', RefreshAccessTokenView.as_view(), name='token_refresh'),
]