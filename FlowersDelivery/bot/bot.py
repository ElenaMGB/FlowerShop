# import asyncio
# import logging
# from aiogram import Bot, Dispatcher
#
# from config import TOKEN
#
# # TOKEN = "YOUR_BOT_TOKEN"
#
# bot = Bot(token=TOKEN)
# dp = Dispatcher(bot)
#
# async def main():
#     logging.basicConfig(level=logging.INFO)
#     await dp.start_polling()
#
# if __name__ == "__main__":
#     asyncio.run(main())

# telegram_bot/bot.py

# telegram_bot/bot.py

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

# Настраиваем путь к Django проекту и инициализируем его
sys.path.append('C:/Users/el/PycharmProjects/FlowerShop')  # Путь к корню вашего Django проекта
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FlowersDelivery.settings')  # Имя вашего проекта
django.setup()

# Правильные импорты с учетом структуры проекта
from django.contrib.auth.models import User
from FlowersDelivery.apps.shop.models import (
    Order, OrderItem, TelegramUser, TelegramNotification
)
from FlowersDelivery.apps.users.models import UserProfile

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Ваш токен Telegram бота
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# Создаем экземпляры бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Обработчик команды /start
@dp.message(Command('start'))
async def cmd_start(message: Message):
    # Получаем или создаем пользователя в нашей базе
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    telegram_user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            'username': username,
            'first_name': first_name,
            'last_name': last_name
        }
    )

    # Если пользователь уже привязан к аккаунту на сайте
    if telegram_user.user:
        # Получаем дополнительную информацию о пользователе из его профиля
        try:
            profile = UserProfile.objects.get(user=telegram_user.user)
            welcome_name = profile.full_name or telegram_user.user.username
        except UserProfile.DoesNotExist:
            welcome_name = telegram_user.user.username

        await message.answer(
            f'Добро пожаловать, {welcome_name}! Ваш аккаунт привязан к профилю на сайте.'
        )
    else:
        await message.answer(
            f'Добро пожаловать, {first_name}! Этот бот поможет вам получать уведомления о ваших заказах.\n\n'
            f'Чтобы привязать ваш Telegram к аккаунту на сайте, используйте команду /register'
        )


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


# Обработчик для регистрации пользователя
@dp.message(Command('register'))
async def cmd_register(message: Message):
    telegram_id = message.from_user.id

    # Получаем пользователя из базы
    telegram_user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name
        }
    )

    # Если пользователь уже привязан
    if telegram_user.user:
        await message.answer(
            'Ваш аккаунт уже привязан к профилю на сайте.'
        )
        return

    # Генерируем новый код подтверждения
    verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    telegram_user.verification_code = verification_code
    telegram_user.save()

    await message.answer(
        f'Ваш код для привязки аккаунта на сайте: <b>{verification_code}</b>\n\n'
        f'Введите его в разделе "Профиль" на нашем сайте.',
        parse_mode="HTML"
    )


# Обработчик для просмотра заказов
@dp.message(Command('orders'))
async def cmd_orders(message: Message):
    telegram_id = message.from_user.id

    # Проверяем, привязан ли пользователь к аккаунту
    try:
        telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)

        if not telegram_user.user:
            await message.answer(
                'Для просмотра заказов необходимо привязать ваш Telegram к аккаунту на сайте.\n'
                'Используйте команду /register'
            )
            return

        # Получаем последние заказы пользователя
        orders = Order.objects.filter(user=telegram_user.user).order_by('-created_at')[:5]

        if not orders:
            await message.answer('У вас пока нет заказов.')
            return

        # Формируем сообщение со списком заказов
        response = '<b>Ваши последние заказы:</b>\n\n'

        for order in orders:
            status_display = dict(Order._meta.get_field('status').choices).get(order.status, order.status)
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


# Функция для периодической проверки и отправки уведомлений
async def check_notifications():
    while True:
        try:
            # Получаем все неотправленные уведомления
            notifications = TelegramNotification.objects.filter(sent=False).order_by('created_at')

            for notification in notifications:
                try:
                    # Отправляем сообщение
                    await bot.send_message(
                        chat_id=notification.telegram_id,
                        text=notification.message_text,
                        parse_mode="HTML"
                    )

                    # Отмечаем как отправленное
                    notification.sent = True
                    notification.sent_at = datetime.now()
                    notification.save()

                    # Пауза между отправками, чтобы не превысить лимиты Telegram
                    await asyncio.sleep(0.5)

                except Exception as e:
                    # Если ошибка, логируем, но не прерываем цикл
                    logging.error(f"Ошибка при отправке уведомления {notification.id}: {e}")

            # Пауза между проверками, чтобы не нагружать базу данных
            await asyncio.sleep(15)

        except Exception as e:
            logging.error(f"Ошибка при проверке уведомлений: {e}")
            await asyncio.sleep(60)  # Более длительная пауза при ошибке


# Функция для запуска бота
async def main():
    # Запускаем проверку уведомлений в фоновом режиме
    asyncio.create_task(check_notifications())

    # Запускаем бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())