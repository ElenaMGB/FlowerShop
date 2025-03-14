import unittest
import sys
from pathlib import Path
import os

# Настройка путей
current_dir = Path(__file__).resolve().parent
project_dir = current_dir.parent
print(f"Текущая директория теста: {current_dir}")
print(f"Директория проекта: {project_dir}")

# Добавляем путь к директории с settings.py
settings_dir = project_dir / 'FlowersDelivery'
sys.path.insert(0, str(settings_dir))
sys.path.insert(0, str(project_dir))
print(f"sys.path: {sys.path[:5]}")

# Устанавливаем переменную окружения для Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# Пробуем инициализировать Django
try:
    import django

    django.setup()
    print("Django успешно инициализирован")
    django_initialized = True
except Exception as e:
    print(f"Ошибка при инициализации Django: {e}")
    django_initialized = False


class DjangoTest(unittest.TestCase):

    def test_django_initialization(self):
        """Проверка, что Django инициализирован"""
        self.assertTrue(django_initialized, "Django не был инициализирован")
        if django_initialized:
            print("Тест инициализации Django пройден")


# Запуск тестов
if __name__ == '__main__':
    unittest.main()