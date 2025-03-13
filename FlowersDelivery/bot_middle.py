# bot_middle.py
import asyncio
import logging
import os
import django
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from asgiref.sync import sync_to_async  # Добавьте эту строку!

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FlowersDelivery.settings')
django.setup()

# Импортируем только User для проверки
from django.contrib.auth.models import User

# Инициализация бота
from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    # Используем sync_to_async для обертывания вызова Django ORM
    get_user_count = sync_to_async(User.objects.count)
    user_count = await get_user_count()

    await message.answer(f'Бот с Django-интеграцией работает! Пользователей в базе: {user_count}')


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}", exc_info=True)