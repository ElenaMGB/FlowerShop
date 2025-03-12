from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, verbose_name='ФИО')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(verbose_name='Адрес', blank=True, null=True)

    def __str__(self):
        return self.user.username
