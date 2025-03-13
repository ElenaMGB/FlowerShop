from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    # path('login/', views.login, name='login'),
# для привязки Telegram
    path('profile/', views.profile, name='profile'),
    path('profile/telegram/', views.connect_telegram, name='connect_telegram'),
]