# инициализацию Django
import asyncio
import logging
import os
import sys
import django
from datetime import datetime
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from asgiref.sync import sync_to_async
import random
import string
from pathlib import Path


# Определяем путь к корню проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# URL вашего сайта для формирования полных URL изображений
BASE_URL = "http://127.0.0.1:8000"  # Замените на реальный URL в продакшн

# Добавляем путь к директориям проекта
sys.path.append(str(BASE_DIR))

# Устанавливаем настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FlowersDelivery.settings')

# Инициализируем Django
django.setup()

# # Настройка логирования
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# код запуска бота
import asyncio
import logging
import os
import sys
import django
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import random
import string
from pathlib import Path

from asgiref.sync import sync_to_async

# Настройка вывода ошибок для отладки
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Определяем путь к корню проекта
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FlowersDelivery.settings')
django.setup()

# Теперь импортируем модели Django
from apps.shop.models import Order, OrderItem, TelegramUser, TelegramNotification
from apps.users.models import UserProfile

from config import TOKEN

# Создаем экземпляры бота и диспетчера

bot = Bot(token=TOKEN)
dp = Dispatcher()

# async def get_or_create_telegram_user(telegram_id, username, first_name, last_name):
#     """Асинхронная обёртка для get_or_create пользователя Telegram"""
#     def _get_or_create():  # Обычная функция, не async
#         return TelegramUser.objects.get_or_create(
#             telegram_id=telegram_id,
#             defaults={
#                 'username': username,
#                 'first_name': first_name,
#                 'last_name': last_name
#             }
#         )
#     return await sync_to_async(_get_or_create)()
#
# async def save_telegram_user(user):
#     """Асинхронная обёртка для сохранения пользователя Telegram"""
#     def _save():  # Обычная функция, не async
#         user.save()
#         return user
#     return await sync_to_async(_save)()
#
# async def get_unsent_notifications():
#     """Асинхронная обёртка для получения неотправленных уведомлений"""
#     def _get_notifications():  # Обычная функция, не async
#         return list(TelegramNotification.objects.filter(sent=False).order_by('created_at'))
#     return await sync_to_async(_get_notifications)()
#
# async def save_notification(notification):
#     """Асинхронная обёртка для сохранения уведомления"""
#     def _save():  # Обычная функция, не async
#         notification.save()
#         return notification
#     return await sync_to_async(_save)()

# Асинхронные обёртки для работы с Django ORM
async def get_or_create_telegram_user(telegram_id, username, first_name, last_name):
    """Асинхронная обёртка для get_or_create пользователя Telegram"""
    def _get_or_create():  # Обычная функция, не async
        return TelegramUser.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'username': username,
                'first_name': first_name,
                'last_name': last_name
            }
        )
    return await sync_to_async(_get_or_create)()



async def save_telegram_user(user):
    """Асинхронная обёртка для сохранения пользователя Telegram"""
    def _save():  # Обычная функция, не async
        user.save()
        return user
    return await sync_to_async(_save)()


async def get_unsent_notifications():
    """Асинхронная обёртка для получения неотправленных уведомлений"""

    async def _get_notifications():
        return list(TelegramNotification.objects.filter(sent=False).order_by('created_at'))

    return await sync_to_async(_get_notifications)()


async def save_notification(notification):
    """Асинхронная обёртка для сохранения уведомления"""

    async def _save():
        notification.save()
        return notification

    return await sync_to_async(_save)()

# Обработчик команды /start
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


# Обработчик команды /help
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


# Функция для отправки уведомлений
# async def check_notifications():
#     while True:
#         try:
#             # Получаем неотправленные уведомления
#             notifications = await get_unsent_notifications()
#             logging.info(f"Найдено {len(notifications)} неотправленных уведомлений")
#
#             for notification in notifications:
#                 try:
#                     # Отправляем уведомление
#                     await bot.send_message(
#                         chat_id=notification.telegram_id,
#                         text=notification.message_text,
#                         parse_mode="HTML"
#                     )
#
#                     # Помечаем как отправленное
#                     notification.sent = True
#                     notification.sent_at = datetime.now()
#                     await save_notification(notification)
#
#                     logging.info(f"Отправлено уведомление {notification.id} пользователю {notification.telegram_id}")
#
#                 except Exception as e:
#                     logging.error(f"Ошибка при отправке уведомления {notification.id}: {e}")
#
#             # Пауза между проверками
#             await asyncio.sleep(15)
#
#         except Exception as e:
#             logging.error(f"Ошибка в функции проверки уведомлений: {e}", exc_info=True)
#             await asyncio.sleep(60)
#

# # big messages
# async def check_notifications():
#     while True:
#         try:
#             # Получаем все неотправленные уведомления
#             notifications = await get_unsent_notifications()
#
#             for notification in notifications:
#                 try:
#                     # Отправляем сообщение
#                     await bot.send_message(
#                         chat_id=notification.telegram_id,
#                         text=notification.message_text,
#                         parse_mode="HTML"
#                     )
#
#                     # Если это новый заказ, также отправляем изображения букетов
#                     if "НОВЫЙ ЗАКАЗ" in notification.message_text:
#                         # Извлекаем ID заказа из текста уведомления
#                         import re
#                         order_id_match = re.search(r'НОВЫЙ ЗАКАЗ #(\d+)', notification.message_text)
#
#                         if order_id_match:
#                             order_id = int(order_id_match.group(1))
#
#                             # Асинхронное получение информации о заказе
#                             async def get_order_images(order_id):
#                                 order = Order.objects.get(id=order_id)
#                                 order_items = OrderItem.objects.filter(order=order)
#                                 return [(item.product.name, item.product.image.url if item.product.image else None)
#                                         for item in order_items]
#
#                             product_images = await sync_to_async(get_order_images)(order_id)
#
#                             # Отправляем изображения букетов, если они есть
#                             for product_name, image_url in product_images:
#                                 if image_url:
#                                     full_url = f"{BASE_URL}{image_url}"  # BASE_URL - URL вашего сайта
#                                     await bot.send_photo(
#                                         chat_id=notification.telegram_id,
#                                         photo=full_url,
#                                         caption=f"Букет: {product_name}"
#                                     )
#
#                     # Отмечаем как отправленное
#                     notification.sent = True
#                     notification.sent_at = datetime.now()
#                     await save_notification(notification)
#
#                 except Exception as e:
#                     logging.error(f"Ошибка при отправке уведомления {notification.id}: {e}")
#
#             # Пауза между проверками
#             await asyncio.sleep(15)
#
#         except Exception as e:
#             logging.error(f"Ошибка при проверке уведомлений: {e}")
#             await asyncio.sleep(60)

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