from django.urls import path
from . import views

urlpatterns = [
    path('', views.weather_view, name='weather'),
    path('save-favorite/', views.save_favorite, name='save_favorite'),
    path('remove-favorite/', views.remove_favorite, name='remove_favorite'),
    path('signup/', views.signup, name='signup')
]