import unittest
import os
import sys
from pathlib import Path


class ProjectStructureTest(unittest.TestCase):
    """Тест для проверки структуры проекта и поиска правильных путей"""

    def setUp(self):
        # Определяем базовые пути
        self.current_dir = Path(__file__).resolve().parent
        self.project_dir = self.current_dir.parent
        print(f"\nТекущая директория: {self.current_dir}")
        print(f"Директория проекта: {self.project_dir}")

    def test_file_existence(self):
        """Проверка существования ключевых файлов"""
        # Список проверяемых файлов
        files_to_check = [
            self.project_dir / "bot.py",
            self.project_dir / "config.py",
            self.project_dir / "manage.py"
        ]

        # Поиск settings.py
        settings_possibilities = [
            self.project_dir / "settings.py",
            self.project_dir / "FlowersDelivery" / "settings.py"
        ]

        # Проверяем существование основных файлов
        for file_path in files_to_check:
            exists = file_path.exists()
            print(f"Файл {file_path}: {'существует' if exists else 'не существует'}")
            if exists:
                # Читаем первые 3 строки файла для определения содержимого
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_lines = [next(f).strip() for _ in range(3) if f.readable()]
                print(f"  Начало файла: {first_lines}")

        # Поиск файла settings.py
        settings_path = None
        for path in settings_possibilities:
            if path.exists():
                settings_path = path
                break

        if settings_path:
            print(f"Найден settings.py: {settings_path}")
            # Определяем, как его импортировать
            relative_path = settings_path.relative_to(self.project_dir)
            import_path = str(relative_path).replace('\\', '.').replace('/', '.').replace('.py', '')
            print(f"Путь для импорта: {import_path}")
        else:
            print("settings.py не найден в обычных местах. Ищем в других директориях...")
            # Искать во всех поддиректориях
            settings_files = list(self.project_dir.glob("**/settings.py"))
            for path in settings_files:
                print(f"Найден settings.py: {path}")
                relative_path = path.relative_to(self.project_dir)
                import_path = str(relative_path).replace('\\', '.').replace('/', '.').replace('.py', '')
                print(f"Возможный путь для импорта: {import_path}")

    def test_django_module_structure(self):
        """Проверка структуры Django-приложений"""
        # Проверяем директорию apps
        apps_dir = self.project_dir / "apps"
        if apps_dir.exists() and apps_dir.is_dir():
            print(f"\nДиректория apps существует: {apps_dir}")
            # Список поддиректорий (приложений)
            apps = [d for d in apps_dir.iterdir() if d.is_dir()]
            print(f"Найдены приложения: {[app.name for app in apps]}")

            # Проверяем наличие моделей
            for app in apps:
                models_path = app / "models.py"
                if models_path.exists():
                    print(f"Найден models.py в приложении {app.name}")
                    # Читаем первые строки для определения моделей
                    try:
                        with open(models_path, 'r', encoding='utf-8') as f:
                            content = f.read(500)  # Читаем первые 500 символов
                            # Ищем определения классов моделей
                            if "class" in content:
                                print(f"  Файл models.py содержит определения классов")
                    except Exception as e:
                        print(f"  Ошибка при чтении models.py: {e}")
        else:
            print(f"\nДиректория apps не найдена: {apps_dir}")


# Запуск тестов
if __name__ == '__main__':
    unittest.main()