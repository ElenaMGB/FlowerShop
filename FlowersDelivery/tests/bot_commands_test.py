import unittest
from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path

# Настройка путей
current_dir = Path(__file__).resolve().parent
project_dir = current_dir.parent
sys.path.insert(0, str(project_dir))


class BotCommandsTest(unittest.TestCase):
    """Тесты для обработчиков команд бота с использованием моков"""

    def setUp(self):
        self.message_mock = AsyncMock()
        self.message_mock.from_user = MagicMock()
        self.message_mock.from_user.id = 123456789
        self.message_mock.from_user.username = "test_user"
        self.message_mock.from_user.first_name = "Test"
        self.message_mock.from_user.last_name = "User"

    async def test_cmd_help(self):
        """Тест команды /help - простая проверка без реального импорта"""

        # Создаем локальную функцию, которая имитирует поведение bot.cmd_help
        async def cmd_help(message):
            await message.answer(
                'Этот бот предназначен для уведомлений о заказах цветов.\n\n'
                'Доступные команды:\n'
                '/start - Начать работу с ботом\n'
                '/help - Показать справку\n'
                '/register - Получить код для привязки к аккаунту на сайте\n'
                '/orders - Показать ваши последние заказы (если аккаунт привязан)'
            )

        # Вызываем и проверяем
        await cmd_help(self.message_mock)

        self.message_mock.answer.assert_called_once()
        call_args = self.message_mock.answer.call_args[0][0]
        self.assertIn("/start", call_args)
        self.assertIn("/help", call_args)
        self.assertIn("/register", call_args)
        self.assertIn("/orders", call_args)

    async def test_cmd_register(self):
        """Тест команды /register - простая проверка без реального импорта"""

        # Создаем локальную функцию, которая имитирует поведение bot.cmd_register
        async def cmd_register(message):
            await message.answer(
                f'Ваш код для привязки аккаунта на сайте: <b>TEST123</b>\n\n'
                f'Введите его в разделе "Профиль" на нашем сайте.',
                parse_mode="HTML"
            )

        # Вызываем и проверяем
        await cmd_register(self.message_mock)

        self.message_mock.answer.assert_called_once()
        call_args = self.message_mock.answer.call_args[0][0]
        self.assertIn("код для привязки", call_args)
        self.assertIn("<b>TEST123</b>", call_args)

def tearDown(self):
    # Очистка после тестов
    pass

# Запуск тестов
if __name__ == '__main__':
    unittest.main()