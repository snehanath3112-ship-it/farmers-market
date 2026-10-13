from django.urls import path
from . import views

urlpatterns = [
    path('farmer/register/', views.farmer_register, name='farmer_register'),
    path('farmer/login/', views.farmer_login, name='farmer_login'),
    path('farmer/dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
    path('farmer/listings/', views.farmer_listings, name='farmer_listings'),
    path('farmer/logout/', views.farmer_logout, name='farmer_logout'),
]