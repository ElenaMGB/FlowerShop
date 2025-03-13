import asyncio
import logging
import os
import django
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Настроим расширенное логирование
logging.basicConfig(
    level=logging.DEBUG,  # Используем DEBUG уровень
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FlowersDelivery.settings')
django.setup()

from config import TOKEN

# Создаем экземпляры бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    logger.info(f"Получена команда /start от {message.from_user.id}")
    await message.answer("Бот запущен и готов к работе!")

@dp.message()
async def echo(message: types.Message):
    logger.info(f"Получено сообщение от {message.from_user.id}: {message.text}")
    await message.answer(f"Получено сообщение: {message.text}")

async def main():
    logger.info("Запускаем бота...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)