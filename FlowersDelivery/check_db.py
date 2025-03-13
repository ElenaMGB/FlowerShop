import os
import django
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FlowersDelivery.settings')
django.setup()

from apps.shop.models import TelegramNotification, TelegramUser

# Проверяем таблицу уведомлений
notifications = TelegramNotification.objects.all().order_by('-created_at')
print(f"Всего уведомлений: {notifications.count()}")
for n in notifications[:5]:
    print(f"ID: {n.id}, Telegram ID: {n.telegram_id}, Отправлено: {n.sent}, Дата: {n.created_at}")

# Проверяем пользователей Telegram
users = TelegramUser.objects.all()
print(f"\nВсего Telegram пользователей: {users.count()}")
for u in users:
    user_status = "Привязан" if u.user else "Не привязан"
    print(f"ID: {u.telegram_id}, Имя: {u.first_name}, Статус: {user_status}")

# Создаем тестовое уведомление, если есть пользователи
if users.exists():
    user = users.first()
    notification = TelegramNotification.objects.create(
        telegram_id=user.telegram_id,
        message_text="🔔 Тестовое уведомление для проверки работы бота\n\nЕсли вы видите это сообщение, значит бот работает правильно!"
    )
    print(f"\nСоздано тестовое уведомление ID: {notification.id} для Telegram ID: {user.telegram_id}")