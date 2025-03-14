# tests/run_tests.py
import unittest
import asyncio
from bot_commands_test import BotCommandsTest
from model_mock_test import TelegramUserMockTest


# Класс для запуска асинхронных тестов
class AsyncTestRunner:
    def __init__(self):
        pass

    def run_async_test(self, test_case_class, test_method_name):
        # Создаем новый экземпляр тестового класса для каждого теста
        test_case = test_case_class()
        test_case.setUp()

        try:
            test_method = getattr(test_case, test_method_name)
            asyncio.run(test_method())
            return True
        except AssertionError as e:
            print(f"FAILED: {e}")
            return False
        finally:
            test_case.tearDown()


# Создаем набор тестов с использованием современного API
def create_test_suite():
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    # Добавляем тесты моделей (они синхронные)
    test_suite.addTests(loader.loadTestsFromTestCase(TelegramUserMockTest))

    return test_suite


# Отдельно запускаем асинхронные тесты
def run_async_tests():
    print("\nЗапуск асинхронных тестов:")
    runner = AsyncTestRunner()

    success = True

    print("test_cmd_help...", end=" ")
    if runner.run_async_test(BotCommandsTest, 'test_cmd_help'):
        print("OK")
    else:
        success = False

    print("test_cmd_register...", end=" ")
    if runner.run_async_test(BotCommandsTest, 'test_cmd_register'):
        print("OK")
    else:
        success = False

    return success


if __name__ == '__main__':
    # Запускаем синхронные тесты
    print("Запуск синхронных тестов:")
    runner = unittest.TextTestRunner()
    test_suite = create_test_suite()
    sync_result = runner.run(test_suite)

    # Запускаем асинхронные тесты
    async_success = run_async_tests()

    if sync_result.wasSuccessful() and async_success:
        print("\nВсе тесты выполнены успешно!")
    else:
        print("\nНекоторые тесты не прошли!")
        exit(1)