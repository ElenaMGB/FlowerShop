import sys
import os
from pathlib import Path

# Вывод текущей информации о путях
print(f"Текущая директория: {os.getcwd()}")
current_dir = Path(__file__).resolve().parent
project_dir = current_dir.parent

print(f"Файл теста: {__file__}")
print(f"Директория теста: {current_dir}")
print(f"Директория проекта: {project_dir}")
print(f"Содержимое директории проекта: {os.listdir(project_dir)}")

# Исходные пути Python
print("\nИсходные пути в sys.path:")
for i, path in enumerate(sys.path):
    print(f"{i}: {path}")

# Добавляем пути до манипуляций с sys.path
original_sys_path = sys.path.copy()


# Метод для проверки импорта
def try_import(module_name, path_list=None):
    """Пытается импортировать модуль с указанным именем, возвращает результат"""
    if path_list:
        # Сохраняем оригинальный sys.path
        original = sys.path.copy()
        # Устанавливаем новый sys.path
        sys.path = path_list.copy()

    print(f"\nПопытка импорта: {module_name}")
    print(f"sys.path (первые 3 пути): {sys.path[:3]}")

    try:
        module = __import__(module_name, fromlist=['*'])
        print(f"✓ Успешно импортирован: {module_name}")
        result = True
    except ImportError as e:
        print(f"✗ Ошибка импорта {module_name}: {e}")
        result = False
    except Exception as e:
        print(f"✗ Другая ошибка при импорте {module_name}: {type(e).__name__} - {e}")
        result = False

    if path_list:
        # Восстанавливаем оригинальный sys.path
        sys.path = original

    return result


# Проверяем импорт django с исходными путями
django_imported = try_import('django')

# Проверяем разные варианты путей
print("\n=== Проверка разных комбинаций путей ===")

# Вариант 1: Добавляем только директорию проекта
paths_1 = [str(project_dir)] + original_sys_path
print("\nВариант 1: Только директория проекта")
try_import('bot', paths_1)
try_import('apps.shop.models', paths_1)
try_import('FlowersDelivery.settings', paths_1)
try_import('settings', paths_1)

# Вариант 2: Добавляем директорию проекта и FlowersDelivery внутри нее
paths_2 = [str(project_dir), str(project_dir / 'FlowersDelivery')] + original_sys_path
print("\nВариант 2: Директория проекта + FlowersDelivery")
try_import('bot', paths_2)
try_import('apps.shop.models', paths_2)
try_import('settings', paths_2)

# Вариант 3: Полностью подготовленные пути
paths_3 = [
              str(project_dir),  # FlowersDelivery/
              str(project_dir / 'FlowersDelivery'),  # FlowersDelivery/FlowersDelivery/
              str(project_dir / 'apps'),  # FlowersDelivery/apps/
              str(project_dir / 'apps' / 'shop'),  # FlowersDelivery/apps/shop/
              str(project_dir / 'apps' / 'users'),  # FlowersDelivery/apps/users/
          ] + original_sys_path
print("\nВариант 3: Все возможные пути")
try_import('bot', paths_3)
try_import('apps.shop.models', paths_3)
try_import('settings', paths_3)

# Проверяем разные имена для settings
print("\n=== Проверка разных имен для settings ===")
for settings_name in ['settings', 'FlowersDelivery.settings', 'settings.py', 'FlowersDelivery.settings.py']:
    try_import(settings_name, paths_3)

# Попытка импорта напрямую из файла
print("\n=== Проверка прямого импорта из файлов ===")
if os.path.exists(project_dir / 'bot.py'):
    print(f"✓ Файл bot.py существует")

    # Устанавливаем sys.path для импорта
    sys.path = [str(project_dir)] + original_sys_path

    try:
        import bot

        print(f"✓ Успешно импортирован модуль bot")
        # Проверяем наличие функций в модуле
        if hasattr(bot, 'cmd_start'):
            print(f"✓ Функция cmd_start существует в модуле bot")
        else:
            print(f"✗ Функция cmd_start не найдена в модуле bot")
    except ImportError as e:
        print(f"✗ Ошибка импорта bot: {e}")
else:
    print(f"✗ Файл bot.py не найден")