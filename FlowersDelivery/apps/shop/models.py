from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import requests

from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    image = models.ImageField(upload_to='products/', blank=True, verbose_name='Изображение')
    # category = models.CharField(max_length=100, verbose_name='Категория')

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Корзина {self.user.full_name}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class Order(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,verbose_name='Пользователь')
    products = models.ManyToManyField(Product, through='OrderItem', verbose_name='Цветы')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата заказа')
    address = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'В ожидании'),
            ('completed', 'Завершён')
        ],
        default='pending',
        verbose_name='Статус'
    )
    order_key = models.CharField(max_length=20, unique=True, verbose_name='Ключ заказа')
    payment_status = models.CharField(max_length=50, default='pending')

    def __str__(self):
        return f"Заказ {self.id} ({self.user.full_name})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Цветы')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


@receiver(post_save, sender=Order)
def notify_bot_about_status_change(sender, instance, **kwargs):
    """Отправляет уведомление боту при изменении статуса заказа."""
    # Проверяем, изменился ли статус
    if instance._status_before_update != instance.status:
        data = {
            'telegram_id': 1367180406,  # ID пользователя из Telegram
            'order_id': instance.id,
            'new_status': instance.status,
            'total_price': float(instance.total_price),
        }
        try:
            # Отправка POST-запроса к вашему боту
            response = requests.post('http://127.0.0.1:8080/notify/', json=data)
            response.raise_for_status()
        except requests.RequestException as e:
            # Логируем ошибки
            print(f"Ошибка при отправке уведомления: {e}")