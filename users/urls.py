from django.urls import path
from .views import *

app_name = 'users'

urlpatterns = [
    path('all/', allUsers, name="Get All Users"),
    path('info/<int:pk>/', userInfo, name="User Info"),
    path('register/', CustomUserCreate.as_view(), name="Create User"),
    path('logout/blacklist/', BlacklistTokenUpdateView.as_view(),
         name='blacklist')
]
