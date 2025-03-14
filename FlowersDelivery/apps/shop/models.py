from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from model_utils import FieldTracker
# from config import ADMIN_TELEGRAM_ID
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название категории')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    image = models.ImageField(upload_to='products/', blank=True, verbose_name='Изображение')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name='Категория')

    def __str__(self):
        return self.name

# class Cart(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"Корзина {self.user.full_name}"
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Проверяем наличие профиля у пользователя
        if hasattr(self.user, 'profile') and self.user.profile.full_name:
            full_name = self.user.profile.full_name
        else:
            full_name = self.user.username
        return f"Корзина {full_name}"


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


import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    """Создает уведомление о заказе для отправки через Telegram"""
    if created or instance.tracker.has_changed('status'):
        # Получаем все товары в заказе
        order_items = OrderItem.objects.filter(order=instance)

        # Формируем список товаров для сообщения
        items_text = "\n".join([
            f"• {item.product.name} x{item.quantity}: {item.price * item.quantity} руб."
            for item in order_items
        ])

        # Формируем текст сообщения для клиента
        client_message = (
            f"🌸 <b>Информация о заказе #{instance.id}</b> 🌸\n\n"
            f"<b>Дата:</b> {instance.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"<b>Статус:</b> {instance.get_status_display()}\n"
            f"<b>Адрес доставки:</b> {instance.address}\n\n"
            f"<b>Состав заказа:</b>\n{items_text}\n\n"
            f"<b>Итого:</b> {instance.total_price} руб.\n\n"
        )

        # Добавляем сообщение о статусе заказа для клиента
        if created:
            client_message += "Спасибо за ваш заказ! Мы свяжемся с вами для уточнения деталей доставки."
        elif instance.tracker.has_changed('status'):
            client_message += f"Статус вашего заказа изменен на: <b>{instance.get_status_display()}</b>"

        # Формируем отдельное сообщение для администратора (более детальное)
        admin_message = (
            f"🌸 <b>НОВЫЙ ЗАКАЗ #{instance.id}</b> 🌸\n\n"
            f"<b>Дата:</b> {instance.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"<b>Покупатель:</b> {instance.user.username}\n"
            f"<b>Телефон:</b> {getattr(instance, 'phone', 'Не указан')}\n"
            f"<b>Адрес доставки:</b> {instance.address}\n\n"
            # f"<b>Состав заказа:</b>\n{items_text}\n\n"
            f"<b>Итого:</b> {instance.total_price} руб."
        )

        # 1. Отправляем уведомление клиенту, если у него есть Telegram
        try:
            telegram_user = TelegramUser.objects.get(user=instance.user)

            # Создаем уведомление для клиента
            TelegramNotification.objects.create(
                telegram_id=telegram_user.telegram_id,
                message_text=client_message
            )
            print(f"Создано уведомление для клиента {instance.user.username}")
        except TelegramUser.DoesNotExist:
            print(f"Telegram ID для пользователя {instance.user.username} не найден")

        # 2. ВСЕГДА создаем уведомление для администратора
        try:
            # Импортируем ADMIN_TELEGRAM_ID из config
            from FlowersDelivery.config import ADMIN_TELEGRAM_ID

            # Создаем уведомление для администратора
            TelegramNotification.objects.create(
                telegram_id=ADMIN_TELEGRAM_ID,
                message_text=admin_message
            )
            print(f"Создано уведомление для администратора о заказе #{instance.id}")
        except Exception as e:
            print(f"Ошибка при создании уведомления для администратора: {e}")
# Очень подробные уведомления с картинками
# @receiver(post_save, sender=Order)
# def create_order_notification(sender, instance, created, **kwargs):
#     """Создает уведомление о заказе для отправки через Telegram"""
#     if created or instance.tracker.has_changed('status'):
#         # Получаем все товары в заказе
#         order_items = OrderItem.objects.filter(order=instance)
#
#         # Формируем текст сообщения с более подробной информацией
#         items_text = "\n".join([
#             f"• <b>{item.product.name}</b> x{item.quantity}: {item.price * item.quantity} руб."
#             for item in order_items
#         ])
#
#         # Получаем дату и время доставки в удобном формате
#         order_date = instance.created_at.strftime("%d.%m.%Y")
#         order_time = instance.created_at.strftime("%H:%M")
#
#         # Формируем текст сообщения
#         message_text = (
#             f"🌸 <b>НОВЫЙ ЗАКАЗ #{instance.id}</b> 🌸\n\n"
#             f"<b>Дата заказа:</b> {order_date}\n"
#             f"<b>Время заказа:</b> {order_time}\n"
#             f"<b>Статус:</b> {instance.get_status_display()}\n"
#             f"<b>Адрес доставки:</b> {instance.address}\n\n"
#             f"<b>Состав заказа:</b>\n{items_text}\n\n"
#             f"<b>Итого:</b> {instance.total_price} руб.\n\n"
#         )
#
#         # Добавляем сообщение о смене статуса, если это обновление
#         if not created and instance.tracker.has_changed('status'):
#             message_text += f"<b>Статус заказа изменен на:</b> {instance.get_status_display()}\n\n"
#
#         message_text += "Спасибо за ваш заказ! Мы свяжемся с вами для уточнения деталей."
#
#         # Пытаемся найти Telegram ID пользователя
#         telegram_user = None
#         try:
#             telegram_user = TelegramUser.objects.get(user=instance.user)
#         except TelegramUser.DoesNotExist:
#             print(f"Telegram ID для пользователя {instance.user.username} не найден")
#             return
#
#         # Создаем уведомление
#         TelegramNotification.objects.create(
#             telegram_id=telegram_user.telegram_id,
#             message_text=message_text
#         )
#
#         # Также отправляем уведомление администратору магазина
#         # (замените на реальный Telegram ID администратора)
#         admin_telegram_id = 123456789  # Укажите ID администратора
#
#         # Текст для администратора
#         admin_message = (
#             f"🔔 <b>НОВЫЙ ЗАКАЗ #{instance.id}</b> 🔔\n\n"
#             f"<b>Покупатель:</b> {instance.user.username}\n"
#             f"<b>Дата:</b> {order_date} {order_time}\n"
#             f"<b>Адрес:</b> {instance.address}\n\n"
#             f"<b>Состав заказа:</b>\n{items_text}\n\n"
#             f"<b>Итого:</b> {instance.total_price} руб."
#         )
#
#         # Создаем уведомление для администратора
#         try:
#             TelegramNotification.objects.create(
#                 telegram_id=admin_telegram_id,
#                 message_text=admin_message
#             )
#         except:
#             pass  # Игнорируем ошибку, если ID администратора не указан

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