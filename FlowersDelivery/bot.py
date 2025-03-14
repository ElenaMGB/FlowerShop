import asyncio
import logging
import os
import sys
import django
import re
import random
import string
from datetime import datetime
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from asgiref.sync import sync_to_async
import aiohttp

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
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


# --- Асинхронные обертки для работы с Django ORM ---

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
def get_order_items_by_order_id(order_id):
    """Получить элементы заказа по ID заказа"""
    try:
        order = Order.objects.get(id=order_id)
        items = list(OrderItem.objects.filter(order=order).select_related('product'))
        return items, order
    except Exception as e:
        logger.error(f"Ошибка при получении заказа #{order_id}: {e}")
        return None, None


@sync_to_async
def get_user_orders(user, limit=5):
    """Получить последние заказы пользователя"""
    return list(Order.objects.filter(user=user).order_by('-created_at')[:limit])


@sync_to_async
def get_status_choices():
    """Получить словарь статусов заказов"""
    return dict(Order._meta.get_field('status').choices)


# --- Обработчики команд бота ---

@dp.message(Command('start'))
async def cmd_start(message: Message):
    try:
        # Данные пользователя
        telegram_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        # Получаем или создаем пользователя
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

        # Если пользователь уже привязан к аккаунту на сайте
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
                except Exception:
                    return telegram_user.user.username

            welcome_name = await get_user_profile()
            await message.answer(f'Добро пожаловать, {welcome_name}! Ваш аккаунт привязан к профилю на сайте.')
        else:
            await message.answer(
                f'Добро пожаловать, {first_name}! Этот бот поможет вам получать уведомления о ваших заказах.\n\n'
                f'Чтобы привязать ваш Telegram к аккаунту на сайте, используйте команду /register'
            )
    except Exception as e:
        logging.error(f"Ошибка в обработчике /start: {e}", exc_info=True)
        await message.answer("Произошла ошибка при обработке команды")


@dp.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer(
        'Этот бот предназначен для уведомлений о заказах цветов.\n\n'
        'Доступные команды:\n'
        '/start - Начать работу с ботом\n'
        '/help - Показать справку\n'
        '/register - Получить код для привязки к аккаунту на сайте\n'
        '/orders - Показать ваши последние заказы (если аккаунт привязан)'
    )


@dp.message(Command('register'))
async def cmd_register(message: Message):
    try:
        telegram_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        # Получаем пользователя из базы
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

        # Если пользователь уже привязан
        @sync_to_async
        def check_user():
            return telegram_user.user is not None

        has_user = await check_user()

        if has_user:
            await message.answer('Ваш аккаунт уже привязан к профилю на сайте.')
            return

        # Генерируем новый код подтверждения
        verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        @sync_to_async
        def save_code():
            telegram_user.verification_code = verification_code
            telegram_user.save()

        await save_code()

        await message.answer(
            f'Ваш код для привязки аккаунта на сайте: <b>{verification_code}</b>\n\n'
            f'Введите его в разделе "Профиль" на нашем сайте.',
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка в обработчике /register: {e}", exc_info=True)
        await message.answer("Произошла ошибка при обработке команды")


@dp.message(Command('orders'))
async def cmd_orders(message: Message):
    try:
        telegram_id = message.from_user.id

        # Проверяем, привязан ли пользователь к аккаунту
        @sync_to_async
        def get_telegram_user_with_user():
            """Получает пользователя Telegram и проверяет связь с пользователем сайта"""
            try:
                telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
                # Проверяем наличие связанного пользователя и возвращаем его, если есть
                has_user = telegram_user.user is not None
                if has_user:
                    return telegram_user, telegram_user.user
                else:
                    return telegram_user, None
            except TelegramUser.DoesNotExist:
                return None, None

        telegram_user, user = await get_telegram_user_with_user()

        if not telegram_user or not user:
            await message.answer(
                'Для просмотра заказов необходимо привязать ваш Telegram к аккаунту на сайте.\n'
                'Используйте команду /register'
            )
            return

        # Получаем последние заказы пользователя
        orders = await get_user_orders(user)

        if not orders:
            await message.answer('У вас пока нет заказов.')
            return

        # Формируем сообщение со списком заказов
        response = '<b>Ваши последние заказы:</b>\n\n'

        # Получаем словарь статусов
        status_choices = await get_status_choices()

        for order in orders:
            status_display = status_choices.get(order.status, order.status)
            response += (
                f'<b>Заказ #{order.id}</b>\n'
                f'Дата: {order.created_at.strftime("%d.%m.%Y %H:%M")}\n'
                f'Статус: {status_display}\n'
                f'Сумма: {order.total_price} руб.\n\n'
            )

        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Ошибка в обработчике /orders: {e}", exc_info=True)
        await message.answer("Произошла ошибка при получении списка заказов")


# --- Функция для проверки и отправки уведомлений ---

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

                        # Выводим для отладки
                        logger.info(f"Обработка уведомления ID {notification.id} для получателя {recipient_id}")

                        # Отправляем сообщение
                        await bot.send_message(
                            chat_id=recipient_id,
                            text=notification.message_text,
                            parse_mode="HTML"
                        )

                        # Если сообщение для администратора и содержит информацию о новом заказе
                        if recipient_id == ADMIN_TELEGRAM_ID and "НОВЫЙ ЗАКАЗ" in notification.message_text:
                            # Извлекаем ID заказа из текста сообщения
                            order_id_match = re.search(r'НОВЫЙ ЗАКАЗ #(\d+)', notification.message_text)

                            if order_id_match:
                                order_id = int(order_id_match.group(1))
                                logger.info(f"Извлечен ID заказа: {order_id}")

                                # Получаем элементы заказа по ID
                                items, order = await get_order_items_by_order_id(order_id)

                                if items:
                                    logger.info(f"Найдено {len(items)} товаров в заказе #{order_id}")

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
                                                            logger.info(
                                                                f"Изображение товара {item.product.id} отправлено")
                                            except Exception as e:
                                                logger.error(f"Ошибка при отправке изображения: {e}")
                                else:
                                    logger.error(f"Не удалось найти товары для заказа #{order_id}")
                            else:
                                logger.error(f"Не удалось извлечь ID заказа из сообщения")

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


# --- Основная функция для запуска бота ---

async def main():
    try:
        # Запускаем фоновую задачу по обработке уведомлений
        asyncio.create_task(process_notifications())

        # Запускаем бота
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")


if __name__ == "__main__":
    asyncio.run(main())