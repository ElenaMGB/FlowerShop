import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
from pathlib import Path
import os

# Вывод отладочной информации для диагностики
current_dir = Path(__file__).resolve().parent
project_dir = current_dir.parent
print(f"Текущая директория теста: {current_dir}")
print(f"Директория проекта: {project_dir}")

# Добавляем все возможные пути к sys.path
sys.path.insert(0, str(project_dir))
sys.path.insert(0, str(project_dir / 'FlowersDelivery'))
print(f"sys.path: {sys.path[:5]}")  # Показываем только первые 5 путей для краткости

# Добавляем путь к директории, содержащей settings.py
settings_dir = project_dir / 'FlowersDelivery'
if os.path.exists(settings_dir / 'settings.py'):
    print(f"settings.py найден в {settings_dir}")
    sys.path.insert(0, str(settings_dir))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
else:
    print(f"settings.py не найден в {settings_dir}")

# Простой тест, который не требует Django
class SimpleTest(unittest.TestCase):
    def test_simple(self):
        """Простой тест для проверки запуска"""
        self.assertTrue(True)
        print("Простой тест прошел успешно")

# Запуск тестов
if __name__ == '__main__':
    unittest.main()