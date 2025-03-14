import asyncio
import logging
import os
import sys
import django
from datetime import datetime
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from asgiref.sync import sync_to_async
import aiohttp

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Определяем путь к корню проекта Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FlowersDelivery.settings')
django.setup()

# Импортируем модели Django
from apps.shop.models import Order, OrderItem, TelegramUser, TelegramNotification
from apps.users.models import UserProfile
from config import TOKEN, ADMIN_TELEGRAM_ID

# URL для изображений
BASE_URL = "http://127.0.0.1:8000"

# Создаем экземпляры бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()


# Асинхронные обертки для работы с Django ORM
@sync_to_async
def get_pending_notifications():
    return list(TelegramNotification.objects.filter(sent=False).order_by('created_at')[:10])


@sync_to_async
def mark_notification_sent(notification):
    notification.sent = True
    notification.sent_at = datetime.now()
    notification.save()


@sync_to_async
def save_notification_error(notification, error):
    notification.error_message = str(error)
    notification.save()


@sync_to_async
def get_order_items_for_telegram_id(telegram_id):
    """Получить последний заказ для пользователя с указанным telegram_id"""
    try:
        # Находим пользователя по telegram_id
        telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
        if telegram_user.user:
            # Находим последний заказ этого пользователя
            latest_order = Order.objects.filter(user=telegram_user.user).order_by('-created_at').first()
            if latest_order:
                # Получаем элементы заказа
                return list(OrderItem.objects.filter(order=latest_order).select_related('product')), latest_order
    except Exception as e:
        logger.error(f"Ошибка при поиске заказа: {e}")
    return None, None


# Асинхронный обработчик уведомлений
async def process_notifications():
    """Проверяет неотправленные уведомления и отправляет их"""
    while True:
        try:
            # Получаем неотправленные уведомления
            notifications = await get_pending_notifications()

            if notifications:
                logger.info(f"Найдено {len(notifications)} неотправленных уведомлений")

                for notification in notifications:
                    try:
                        # Определяем, кому отправляем сообщение
                        recipient_id = notification.telegram_id

                        # Если сообщение для администратора, заменяем ID на ID админа из config
                        if recipient_id == ADMIN_TELEGRAM_ID or "НОВЫЙ ЗАКАЗ" in notification.message_text:
                            recipient_id = ADMIN_TELEGRAM_ID
                            logger.info(f"Отправка сообщения администратору (ID: {ADMIN_TELEGRAM_ID})")

                        # Отправляем сообщение
                        await bot.send_message(
                            chat_id=recipient_id,
                            text=notification.message_text,
                            parse_mode="HTML"
                        )

                        # Если сообщение для администратора, добавляем изображения продуктов
                        if recipient_id == ADMIN_TELEGRAM_ID:
                            items, order = await get_order_items_for_telegram_id(notification.telegram_id)
                            if items:
                                for item in items:
                                    if item.product and hasattr(item.product, 'image') and item.product.image:
                                        try:
                                            image_url = f"{BASE_URL}{item.product.image.url}"
                                            logger.info(f"Загрузка изображения с URL: {image_url}")

                                            async with aiohttp.ClientSession() as session:
                                                async with session.get(image_url) as response:
                                                    if response.status == 200:
                                                        image_data = await response.read()

                                                        # Отправляем изображение
                                                        await bot.send_photo(
                                                            chat_id=ADMIN_TELEGRAM_ID,
                                                            photo=types.BufferedInputFile(
                                                                image_data,
                                                                filename=f"product_{item.product.id}.jpg"
                                                            ),
                                                            caption=f"{item.product.name} - {item.price} руб. x {item.quantity} шт."
                                                        )
                                                        logger.info(f"Изображение товара {item.product.id} отправлено")
                                        except Exception as e:
                                            logger.error(f"Ошибка при отправке изображения: {e}")

                        # Помечаем уведомление как отправленное
                        await mark_notification_sent(notification)
                        logger.info(f"Уведомление успешно отправлено")

                    except Exception as e:
                        logger.error(f"Ошибка при обработке уведомления {notification.id}: {e}")
                        await save_notification_error(notification, e)

            # Пауза между проверками
            await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"Глобальная ошибка в процессе обработки уведомлений: {e}")
            await asyncio.sleep(60)


# Основные обработчики команд бота
@dp.message(Command('start'))
async def cmd_start(message: Message):
    try:
        telegram_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        @sync_to_async
        def get_or_create_user():
            return TelegramUser.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name
                }
            )

        telegram_user, created = await get_or_create_user()
        logging.info(f"Пользователь {'создан' if created else 'найден'}: {telegram_id}")

        @sync_to_async
        def check_user():
            return telegram_user.user is not None

        has_user = await check_user()

        if has_user:
            @sync_to_async
            def get_user_profile():
                try:
                    profile = UserProfile.objects.get(user=telegram_user.user)
                    return profile.full_name or telegram_user.user.username
                except UserProfile.DoesNotExist:
                    return telegram_user.user.username

            welcome_name = await get_user_profile()
            await message.answer(f'Добро пожаловать, {welcome_name}! Ваш аккаунт привязан к профилю.')
        else:
            await message.answer('Добро пожаловать! Используйте команду /link для привязки аккаунта.')

    except Exception as e:
        logging.error(f"Ошибка в обработчике start: {e}")
        await message.answer('Произошла ошибка при обработке команды.')


# Запуск бота
async def main():
    # Запускаем фоновую задачу по обработке уведомлений
    asyncio.create_task(process_notifications())

    # Запускаем бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())