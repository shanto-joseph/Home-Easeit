# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.CustomerRegistrationView.as_view(), name='register'),
    path('register/landlord/', views.LandlordRegistrationView.as_view(), name='register_landlord'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),
]
