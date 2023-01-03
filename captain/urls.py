from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import update_last_login

# We need to add custom data with the auth tokens (user's name and email),
# For this we make a custom TokenObtainPairView and use that instead of the default one.


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['display_name'] = user.display_name
        token['email'] = user.email
        token['about'] = user.about
        token['is_staff'] = user.is_staff
        token['is_active'] = user.is_active
        token['is_superuser'] = user.is_superuser
        # ...
        update_last_login(None, user)
        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('website.urls', namespace='website')),
    
    # For user registration and token blacklisting
    path('api/user/', include('users.urls', namespace='users')),
    
    # For user login
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # For getting refresh token
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/', include('api.urls', namespace='api')),

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
