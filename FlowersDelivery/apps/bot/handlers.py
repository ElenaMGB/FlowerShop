from aiogram import types, Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

async def start_command(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📦 Оформить заказ"), KeyboardButton("📜 Каталог"))
    await message.answer("Добро пожаловать в FlowerDelivery!", reply_markup=keyboard)

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, commands="start")