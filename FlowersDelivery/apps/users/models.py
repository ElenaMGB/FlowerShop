from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, verbose_name='ФИО')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Телефон')
    address = models.TextField(verbose_name='Адрес', blank=True, null=True)
    telegram_id = models.BigIntegerField(blank=True, null=True, verbose_name='ID Telegram')

    def __str__(self):
        return f"Профиль {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создаем профиль при создании пользователя."""
    if created:
        UserProfile.objects.create(user=instance)
