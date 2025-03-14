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
import random
import string
from io import BytesIO

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Определяем путь к корню проекта Django (для доступа к базе данных)
BASE_DIR = Path(__file__).resolve().parent.parent

# Настраиваем Django для доступа к моделям
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FlowersDelivery.settings')
django.setup()

# URL вашего сайта для формирования полных URL изображений
BASE_URL = "http://127.0.0.1:8000"  # Замените на реальный URL в продакшене

# Теперь импортируем модели Django
from apps.shop.models import Order, OrderItem, TelegramUser, TelegramNotification
from apps.users.models import UserProfile

from config import TOKEN, ADMIN_TELEGRAM_ID


# Создаем экземпляры бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()


# Асинхронный обработчик уведомлений
async def process_notifications():
    """Проверяет неотправленные уведомления и отправляет их администратору"""
    while True:
        try:
            # Получаем неотправленные уведомления
            async def get_pending_notifications():
                return list(
                    TelegramNotification.objects.filter(sent=False).select_related('order').order_by('created_at')[:10])

            notifications = await sync_to_async(get_pending_notifications)()

            if notifications:
                logger.info(f"Найдено {len(notifications)} неотправленных уведомлений")

                for notification in notifications:
                    try:
                        # Получаем данные заказа
                        async def get_order_details():
                            order = notification.order
                            items = OrderItem.objects.filter(order=order).select_related('product')
                            return order, list(items)

                        order, items = await sync_to_async(get_order_details)()

                        # Формируем сообщение о заказе
                        order_message = (
                            f"📦 НОВЫЙ ЗАКАЗ #{order.id}\n\n"
                            f"📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                            f"👤 Покупатель: {order.full_name}\n"
                            f"📱 Телефон: {order.phone}\n"
                            f"🏠 Адрес доставки: {order.address}\n"
                        )

                        if hasattr(order, 'comment') and order.comment:
                            order_message += f"📝 Комментарий: {order.comment}\n"

                        order_message += f"\n🛒 Товары в заказе:\n"

                        total_price = 0

                        # Добавляем информацию о каждом товаре
                        for item in items:
                            item_price = item.price * item.quantity
                            total_price += item_price
                            order_message += f"- {item.product.name} x{item.quantity} = {item_price} руб.\n"

                        order_message += f"\n💰 Итого: {total_price} руб."

                        # Отправляем общую информацию о заказе
                        await bot.send_message(
                            chat_id=ADMIN_TELEGRAM_ID,
                            text=order_message,
                            parse_mode="HTML"
                        )

                        # Отправляем изображения для каждого товара в заказе
                        for item in items:
                            if hasattr(item.product, 'image') and item.product.image:
                                try:
                                    image_url = f"{BASE_URL}{item.product.image.url}"

                                    # Скачиваем изображение
                                    async with aiohttp.ClientSession() as session:
                                        async with session.get(image_url) as response:
                                            if response.status == 200:
                                                image_data = await response.read()

                                                # Отправляем изображение с подписью
                                                await bot.send_photo(
                                                    chat_id=ADMIN_TELEGRAM_ID,
                                                    photo=types.BufferedInputFile(
                                                        image_data,
                                                        filename=f"product_{item.product.id}.jpg"
                                                    ),
                                                    caption=f"{item.product.name} - {item.price} руб. x {item.quantity} шт."
                                                )
                                except Exception as e:
                                    logger.error(f"Ошибка при отправке изображения: {e}")

                        # Помечаем уведомление как отправленное
                        async def mark_as_sent():
                            notification.sent = True
                            notification.sent_at = datetime.now()
                            notification.save()

                        await sync_to_async(mark_as_sent)()
                        logger.info(f"Уведомление для заказа #{order.id} успешно отправлено")

                    except Exception as e:
                        # Записываем ошибку и продолжаем с другими уведомлениями
                        logger.error(f"Ошибка при обработке уведомления {notification.id}: {e}")

                        async def mark_error():
                            notification.error_message = str(e)
                            notification.save()

                        await sync_to_async(mark_error)()

            # Пауза между проверками
            await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"Глобальная ошибка в процессе обработки уведомлений: {e}")
            await asyncio.sleep(60)  # При ошибке делаем более длинную паузу


# Основные обработчики команд бота (оставляем как есть)
@dp.message(Command('start'))
async def cmd_start(message: Message):
    try:
        # Данные пользователя
        telegram_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        # Правильное использование sync_to_async
        def get_or_create_user():
            return TelegramUser.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name
                }
            )

        telegram_user, created = await sync_to_async(get_or_create_user)()

        logging.info(f"Пользователь {'создан' if created else 'найден'}: {telegram_id}")

        # Если пользователь уже привязан к аккаунту на сайте
        if telegram_user.user:
            def get_user_profile():
                try:
                    profile = UserProfile.objects.get(user=telegram_user.user)
                    return profile.full_name or telegram_user.user.username
                except Exception:
                    return telegram_user.user.username

            welcome_name = await sync_to_async(get_user_profile)()
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

## Обработчик для регистрации пользователя
@dp.message(Command('register'))
async def cmd_register(message: Message):
    try:
        telegram_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        # Получаем пользователя из базы
        def get_or_create_user():
            return TelegramUser.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name
                }
            )

        telegram_user, created = await sync_to_async(get_or_create_user)()

        # Если пользователь уже привязан
        if telegram_user.user:
            await message.answer('Ваш аккаунт уже привязан к профилю на сайте.')
            return

        # Генерируем новый код подтверждения
        verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        telegram_user.verification_code = verification_code

        # Сохраняем изменения
        def save_user():
            telegram_user.save()

        await sync_to_async(save_user)()

        await message.answer(
            f'Ваш код для привязки аккаунта на сайте: <b>{verification_code}</b>\n\n'
            f'Введите его в разделе "Профиль" на нашем сайте.',
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка в обработчике /register: {e}", exc_info=True)
        await message.answer("Произошла ошибка при обработке команды")


# Обработчик для просмотра заказов
@dp.message(Command('orders'))
async def cmd_orders(message: Message):
    try:
        telegram_id = message.from_user.id

        # Проверяем, привязан ли пользователь к аккаунту
        try:
            # Получаем пользователя Telegram с использованием sync_to_async
            get_telegram_user = sync_to_async(TelegramUser.objects.get)
            telegram_user = await get_telegram_user(telegram_id=telegram_id)

            if not telegram_user.user:
                await message.answer(
                    'Для просмотра заказов необходимо привязать ваш Telegram к аккаунту на сайте.\n'
                    'Используйте команду /register'
                )
                return

            # Получаем последние заказы пользователя с использованием sync_to_async
            async def get_orders():
                return list(Order.objects.filter(user=telegram_user.user).order_by('-created_at')[:5])

            orders = await sync_to_async(get_orders)()

            if not orders:
                await message.answer('У вас пока нет заказов.')
                return

            # Формируем сообщение со списком заказов
            response = '<b>Ваши последние заказы:</b>\n\n'

            # Получаем словарь статусов
            async def get_status_choices():
                return dict(Order._meta.get_field('status').choices)

            status_choices = await sync_to_async(get_status_choices)()

            for order in orders:
                status_display = status_choices.get(order.status, order.status)
                response += (
                    f'<b>Заказ #{order.id}</b>\n'
                    f'Дата: {order.created_at.strftime("%Y-%m-%d %H:%M")}\n'
                    f'Статус: {status_display}\n'
                    f'Сумма: {order.total_price} руб.\n\n'
                )

            await message.answer(response, parse_mode="HTML")

        except TelegramUser.DoesNotExist:
            await message.answer(
                'Вы еще не зарегистрированы в боте. Используйте команду /start для начала работы.'
            )
    except Exception as e:
        logging.error(f"Ошибка в обработчике /orders: {e}", exc_info=True)
        await message.answer("Произошла ошибка при получении списка заказов")


async def check_notifications():
    while True:
        try:
            # Правильное использование sync_to_async
            def get_notifications():
                return list(TelegramNotification.objects.filter(sent=False).order_by('created_at'))

            notifications = await sync_to_async(get_notifications)()

            for notification in notifications:
                try:
                    # Отправляем сообщение
                    await bot.send_message(
                        chat_id=notification.telegram_id,
                        text=notification.message_text,
                        parse_mode="HTML"
                    )

                    # Отмечаем как отправленное
                    def mark_as_sent():
                        notification.sent = True
                        notification.sent_at = datetime.now()
                        notification.save()

                    await sync_to_async(mark_as_sent)()

                    logging.info(f"Отправлено уведомление {notification.id} пользователю {notification.telegram_id}")

                except Exception as e:
                    logging.error(f"Ошибка при отправке уведомления {notification.id}: {e}")

            # Пауза между проверками
            await asyncio.sleep(5)

        except Exception as e:
            logging.error(f"Ошибка при проверке уведомлений: {e}")
            await asyncio.sleep(30)

# Функция для запуска бота
async def main():
    try:
        # Запускаем проверку уведомлений в фоновом режиме
        asyncio.create_task(check_notifications())

        # Запускаем бота
        logging.info("Бот запускается...")
        await dp.start_polling(bot)

    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}", exc_info=True)

# # Главная функция запуска бота
# async def main():
#     # Запускаем задачу обработки уведомлений в фоновом режиме
#     asyncio.create_task(process_notifications())
#
#     # Запускаем бота
#     await dp.start_polling(bot)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())