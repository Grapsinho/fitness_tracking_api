from django.urls import path
from .views import RegisterUser, LoginUser, LogoutUser, CurrentUserDetail, RefreshAccessTokenView, CurrentUserProfileUpdate, UserProfileView

urlpatterns = [
    path('register/', RegisterUser.as_view(), name='register'),
    path('login/', LoginUser.as_view(), name='login'),
    path('logout/', LogoutUser.as_view(), name='logout'),
    
    # get a current user
    path('current_user/', CurrentUserDetail.as_view(), name='current_user'),
    path('current_user/profile_update/', CurrentUserProfileUpdate.as_view(), name='current_user_profile_update'),
    path('user_profile/<str:unique_id>/', UserProfileView.as_view(), name='user_profile'),

    # refresh token
    path('token/refresh/', RefreshAccessTokenView.as_view(), name='token_refresh'),
]