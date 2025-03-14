# tests/test_bot.py (упрощенная версия бота для тестов)

async def cmd_start(message):
    await message.answer(
        f'Добро пожаловать! Этот бот поможет вам получать уведомления о ваших заказах.\n\n'
        f'Чтобы привязать ваш Telegram к аккаунту на сайте, используйте команду /register'
    )

async def cmd_help(message):
    await message.answer(
        'Этот бот предназначен для уведомлений о заказах цветов.\n\n'
        'Доступные команды:\n'
        '/start - Начать работу с ботом\n'
        '/help - Показать справку\n'
        '/register - Получить код для привязки к аккаунту на сайте\n'
        '/orders - Показать ваши последние заказы (если аккаунт привязан)'
    )

async def cmd_register(message):
    await message.answer(
        f'Ваш код для привязки аккаунта на сайте: <b>TESTCODE</b>\n\n'
        f'Введите его в разделе "Профиль" на нашем сайте.',
        parse_mode="HTML"
    )

async def cmd_orders(message):
    await message.answer('У вас пока нет заказов.')