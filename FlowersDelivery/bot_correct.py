# correct_bot.py
import asyncio
import logging
import os
import django
from datetime import datetime
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from asgiref.sync import sync_to_async
import random
import string

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FlowersDelivery.settings')
django.setup()

# Импорт моделей
from apps.shop.models import TelegramUser, TelegramNotification
from apps.users.models import UserProfile
from django.contrib.auth.models import User

# Инициализация бота
from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()


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
async def cmd_start(message: types.Message):
    logger.info(f"Получена команда /start от {message.from_user.id}")

    try:
        # Получаем или создаем пользователя Telegram
        telegram_user, created = await get_or_create_telegram_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name
        )

        logger.info(f"Telegram пользователь {'создан' if created else 'найден'}: {telegram_user.telegram_id}")

        # Проверяем привязку к аккаунту на сайте
        if telegram_user.user:
            await message.answer(f"Добро пожаловать! Ваш Telegram привязан к аккаунту на сайте.")
        else:
            await message.answer(
                f"Добро пожаловать, {message.from_user.first_name}!\n\n"
                f"Чтобы получать уведомления о заказах, используйте команду /register для привязки "
                f"к вашему аккаунту на сайте."
            )

    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}", exc_info=True)
        await message.answer("Произошла ошибка при обработке команды.")


# Обработчик команды /register
@dp.message(Command('register'))
async def cmd_register(message: types.Message):
    logger.info(f"Получена команда /register от {message.from_user.id}")

    try:
        # Получаем или создаем пользователя Telegram
        telegram_user, created = await get_or_create_telegram_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name
        )

        # Проверяем, не привязан ли уже
        if telegram_user.user:
            await message.answer("Ваш Telegram уже привязан к аккаунту на сайте.")
            return

        # Генерируем код подтверждения
        verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        telegram_user.verification_code = verification_code

        # Сохраняем изменения
        await save_telegram_user(telegram_user)

        await message.answer(
            f"Ваш код для привязки аккаунта: <b>{verification_code}</b>\n\n"
            f"Введите его в разделе профиля на нашем сайте.",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка в команде /register: {e}", exc_info=True)
        await message.answer("Произошла ошибка при обработке команды.")


# Функция для отправки уведомлений
async def check_notifications():
    while True:
        try:
            # Получаем неотправленные уведомления
            notifications = await get_unsent_notifications()
            logger.info(f"Найдено {len(notifications)} неотправленных уведомлений")

            for notification in notifications:
                try:
                    # Отправляем уведомление
                    await bot.send_message(
                        chat_id=notification.telegram_id,
                        text=notification.message_text,
                        parse_mode="HTML"
                    )

                    # Помечаем как отправленное
                    notification.sent = True
                    notification.sent_at = datetime.now()
                    await save_notification(notification)

                    logger.info(f"Отправлено уведомление {notification.id} пользователю {notification.telegram_id}")

                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления {notification.id}: {e}")

            # Пауза между проверками
            await asyncio.sleep(15)

        except Exception as e:
            logger.error(f"Ошибка в функции проверки уведомлений: {e}", exc_info=True)
            await asyncio.sleep(60)


# Главная функция
async def main():
    try:
        # Запускаем проверку уведомлений в фоновом режиме
        asyncio.create_task(check_notifications())

        # Запускаем бота
        logger.info("Бот запускается...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)