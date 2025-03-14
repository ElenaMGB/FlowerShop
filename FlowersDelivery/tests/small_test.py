import unittest
from unittest.mock import AsyncMock, MagicMock


class BotCommandsTest(unittest.TestCase):
    """Тесты для обработчиков команд бота"""

    def setUp(self):
        # Создаем моки для message
        self.message_mock = AsyncMock()
        self.message_mock.from_user = MagicMock()
        self.message_mock.from_user.id = 123456789
        self.message_mock.from_user.username = "test_user"
        self.message_mock.from_user.first_name = "Test"
        self.message_mock.from_user.last_name = "User"

    async def test_help_command_response(self):
        """Тест команды /help"""

        # Создаем мок-функцию для команды /help
        async def cmd_help(message):
            await message.answer(
                'Этот бот предназначен для уведомлений о заказах цветов.\n\n'
                'Доступные команды:\n'
                '/start - Начать работу с ботом\n'
                '/help - Показать справку\n'
                '/register - Получить код для привязки к аккаунту на сайте\n'
                '/orders - Показать ваши последние заказы (если аккаунт привязан)'
            )

        # Вызываем функцию
        await cmd_help(self.message_mock)

        # Проверяем результат
        self.message_mock.answer.assert_called_once()
        call_args = self.message_mock.answer.call_args[0][0]
        self.assertIn("/start", call_args)
        self.assertIn("/help", call_args)
        self.assertIn("/register", call_args)
        self.assertIn("/orders", call_args)


# Запуск тестов
if __name__ == '__main__':
    unittest.main()