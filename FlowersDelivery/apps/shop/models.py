from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import requests
from model_utils import FieldTracker


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
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
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
    # Добавляем поле total_price
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Общая сумма')
    tracker = FieldTracker(fields=['status'])

    def __str__(self):
        return f"Заказ {self.id} ({self.user.username})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Цветы')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    """Создает уведомление о заказе для отправки через Telegram"""
    if created or instance.tracker.has_changed('status'):  # Нужен django-model-utils для tracker
        # Получаем все товары в заказе
        order_items = OrderItem.objects.filter(order=instance)
        items_text = "\n".join([f"- {item.product.name} x{item.quantity}: {item.price * item.quantity} руб."
                                for item in order_items])

        # Формируем текст сообщения
        message_text = (
            f"🌸 <b>Заказ #{instance.id}</b> 🌸\n\n"
            f"<b>Дата:</b> {instance.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"<b>Статус:</b> {instance.get_status_display()}\n"
            f"<b>Адрес доставки:</b> {instance.address}\n\n"
            f"<b>Состав заказа:</b>\n{items_text}\n\n"
            f"<b>Итого:</b> {instance.total_price} руб.\n\n"
        )

        # Добавляем сообщение о смене статуса, если это обновление
        if not created and instance.tracker.has_changed('status'):
            message_text += f"<b>Статус заказа изменен на:</b> {instance.get_status_display()}\n\n"

        message_text += "Спасибо за ваш заказ!"

        # Пытаемся найти Telegram ID пользователя
        telegram_user = None
        try:
            telegram_user = TelegramUser.objects.get(user=instance.user)
        except TelegramUser.DoesNotExist:
            # Если не нашли, то просто логируем
            print(f"Telegram ID для пользователя {instance.user.username} не найден")
            return

        # Создаем уведомление
        TelegramNotification.objects.create(
            telegram_id=telegram_user.telegram_id,
            message_text=message_text
        )
# @receiver(post_save, sender=Order)
# def notify_bot_about_status_change(sender, instance, **kwargs):
#     """Отправляет уведомление боту при изменении статуса заказа."""
#     # Проверяем, изменился ли статус
#     if instance._status_before_update != instance.status:
#         data = {
#             'telegram_id': 1367180406,  # ID пользователя из Telegram
#             'order_id': instance.id,
#             'new_status': instance.status,
#             'total_price': float(instance.total_price),
#         }
#         try:
#             # Отправка POST-запроса к вашему боту
#             response = requests.post('http://127.0.0.1:8080/notify/', json=data)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             # Логируем ошибки
#             print(f"Ошибка при отправке уведомления: {e}")


# @receiver(post_save, sender=Order)
# def notify_bot_about_status_change(sender, instance, created, **kwargs):
#     """Отправляет уведомление боту при создании заказа."""
#     if created:  # Проверяем, что заказ только что создан
#         # Вычисляем total_price из элементов заказа
#         order_items = OrderItem.objects.filter(order=instance)
#         total_price = sum(item.price * item.quantity for item in order_items)
#
#         data = {
#             'telegram_id': 1367180406,  # ID пользователя из Telegram
#             'order_id': instance.id,
#             'new_status': instance.status,
#             'total_price': float(total_price),
#         }
#         try:
#             # Отправка POST-запроса к вашему боту
#             response = requests.post('http://127.0.0.1:8080/notify/', json=data)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             # Логируем ошибки
#             print(f"Ошибка при отправке уведомления: {e}")


class TelegramUser(models.Model):
    """Модель для хранения данных пользователей Telegram"""
    telegram_id = models.BigIntegerField(primary_key=True, verbose_name='ID Telegram')
    username = models.CharField(max_length=100, blank=True, null=True, verbose_name='Username в Telegram')
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='telegram_profile', verbose_name='Пользователь сайта')
    verification_code = models.CharField(max_length=20, blank=True, null=True, verbose_name='Код подтверждения')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Telegram: {self.telegram_id} ({self.username or 'No username'})"

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"


class TelegramNotification(models.Model):
    """Модель для хранения уведомлений, которые должен отправить бот"""
    id = models.AutoField(primary_key=True)
    telegram_id = models.BigIntegerField(verbose_name='ID получателя в Telegram')
    message_text = models.TextField(verbose_name='Текст сообщения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    sent = models.BooleanField(default=False, verbose_name='Отправлено')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата отправки')

    def __str__(self):
        return f"Уведомление для {self.telegram_id} ({self.sent and 'отправлено' or 'не отправлено'})"

    class Meta:
        verbose_name = "Уведомление Telegram"
        verbose_name_plural = "Уведомления Telegram"