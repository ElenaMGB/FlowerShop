import os
import sys
from pathlib import Path

# Вывод информации о путях
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
print(f"BASE_DIR: {BASE_DIR}")
print(f"sys.path: {sys.path}")

# Проверка структуры директории проекта
print("\nСтруктура проекта:")
print(f"Содержимое BASE_DIR: {[f.name for f in BASE_DIR.iterdir()]}")

# Поиск файла settings.py
settings_found = False
for root, dirs, files in os.walk(BASE_DIR):
    if 'settings.py' in files:
        settings_path = Path(root) / 'settings.py'
        rel_path = settings_path.relative_to(BASE_DIR)
        print(f"\nНайден settings.py: {rel_path}")

        # Попробуем понять, как импортировать этот файл
        module_path = str(rel_path).replace('\\', '.').replace('/', '.').replace('.py', '')
        print(f"Возможный путь импорта: {module_path}")

        # Добавляем родительскую директорию найденного settings.py в sys.path
        parent_dir = settings_path.parent
        if parent_dir != BASE_DIR:
            sys.path.append(str(parent_dir))
            print(f"Добавлен путь: {parent_dir}")

        settings_found = True

if not settings_found:
    print("\nФайл settings.py не найден в проекте!")

# Проверяем разные возможные пути для настроек Django
possible_settings = [
    'settings',  # settings.py в корне проекта
    'FlowersDelivery.settings',  # FlowersDelivery/settings.py
    'config.settings',  # config/settings.py
    module_path if settings_found else 'unknown'  # Найденный путь
]

print("\nПроверка возможных путей к settings.py:")
for settings_path in possible_settings:
    try:
        print(f"Пробуем: {settings_path}")
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_path)
        import django

        django.setup()
        print(f"✓ Успешно! Правильный путь: {settings_path}")

        # Если успешно, пробуем импортировать модели
        try:
            from apps.shop.models import TelegramUser

            print("✓ Модель TelegramUser успешно импортирована")
        except ImportError as e:
            print(f"✗ Ошибка импорта моделей: {e}")

        try:
            import bot

            print("✓ Модуль бота успешно импортирован")
        except ImportError as e:
            print(f"✗ Ошибка импорта бота: {e}")

        break
    except Exception as e:
        print(f"✗ Ошибка: {e}")

print("\nПроверка импортов завершена")