import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import TOKEN

# TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())