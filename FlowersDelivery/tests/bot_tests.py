import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
from pathlib import Path
import os

# Настройка путей
current_dir = Path(__file__).resolve().parent
project_dir = current_dir.parent  # FlowersDelivery/

# Добавляем только корень проекта в путь
sys.path = [str(project_dir)] + sys.path

# Базовый тест, который не требует инициализации Django
class BotBasicTest(unittest.TestCase):
    """Базовые тесты функциональности бота"""

    def setUp(self):
        # Создаем моки для сообщений
        self.message_mock = AsyncMock()
        self.message_mock.from_user = MagicMock()
        self.message_mock.from_user.id = 123456789
        self.message_mock.from_user.username = "test_user"
        self.message_mock.from_user.first_name = "Test"
        self.message_mock.from_user.last_name = "User"
        self.message_mock.answer = AsyncMock()

    def test_imports(self):
        """Проверка доступности импортов модуля бота"""
        import test_bot  # Простая проверка, что модуль существует
        self.assertTrue(hasattr(test_bot, 'cmd_help'), "Функция cmd_help должна быть в модуле bot")


# Запуск тестов
if __name__ == '__main__':
    unittest.main()