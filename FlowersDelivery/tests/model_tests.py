import unittest
import sys
from pathlib import Path
import os

# Настройка путей
current_dir = Path(__file__).resolve().parent
project_dir = current_dir.parent  # FlowersDelivery/

# Добавляем только корень проекта в путь
sys.path = [str(project_dir)] + sys.path

# Устанавливаем переменную окружения для Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'FlowersDelivery.settings'

# Инициализация Django
import django

django.setup()


# Простой тест для проверки моделей
class ModelImportTest(unittest.TestCase):
    """Тест для проверки доступности моделей"""

    def test_model_imports(self):
        """Проверка импорта моделей"""
        # Определяем пути к моделям
        try:
            # Пробуем импортировать TelegramUser
            from apps.shop.models import TelegramUser
            self.assertTrue(True, "TelegramUser должен быть доступен")
        except ImportError as e:
            self.fail(f"Не удалось импортировать TelegramUser: {e}")

        try:
            # Пробуем импортировать UserProfile
            from apps.users.models import UserProfile
            self.assertTrue(True, "UserProfile должен быть доступен")
        except ImportError as e:
            self.fail(f"Не удалось импортировать UserProfile: {e}")


# Запуск тестов
if __name__ == '__main__':
    unittest.main()