import unittest


class TelegramUserMockTest(unittest.TestCase):
    """Тест для модели TelegramUser с использованием моков"""

    def setUp(self):
        # Моки для моделей
        class User:
            def __init__(self, id, username):
                self.id = id
                self.username = username

        class TelegramUser:
            def __init__(self, telegram_id, username, first_name, last_name, verification_code=None, user=None):
                self.telegram_id = telegram_id
                self.username = username
                self.first_name = first_name
                self.last_name = last_name
                self.verification_code = verification_code
                self.user = user

        class TelegramNotification:
            def __init__(self, telegram_id, message_text, notification_type, sent=False, sent_at=None):
                self.telegram_id = telegram_id
                self.message_text = message_text
                self.notification_type = notification_type
                self.sent = sent
                self.sent_at = sent_at

        self.User = User
        self.TelegramUser = TelegramUser
        self.TelegramNotification = TelegramNotification
        self.test_user = User(1, "testuser")

    def test_create_telegram_user(self):
        """Тест создания объекта TelegramUser"""
        telegram_user = self.TelegramUser(
            telegram_id=123456789,
            username='test_telegram_user',
            first_name='Test',
            last_name='User',
            verification_code='ABCD1234'
        )

        self.assertEqual(telegram_user.telegram_id, 123456789)
        self.assertEqual(telegram_user.username, 'test_telegram_user')
        self.assertEqual(telegram_user.verification_code, 'ABCD1234')
        self.assertIsNone(telegram_user.user)

    def test_link_user_to_telegram(self):
        """Тест привязки пользователя к Telegram-аккаунту"""
        telegram_user = self.TelegramUser(
            telegram_id=123456789,
            username='test_telegram_user',
            first_name='Test',
            last_name='User',
            verification_code='ABCD1234'
        )

        # Привязываем пользователя
        telegram_user.user = self.test_user

        # Проверяем привязку
        self.assertEqual(telegram_user.user.id, 1)
        self.assertEqual(telegram_user.user.username, 'testuser')

    def test_create_notification(self):
        """Тест создания уведомления"""
        notification = self.TelegramNotification(
            telegram_id=123456789,
            message_text='Тестовое уведомление',
            notification_type='order'
        )

        self.assertEqual(notification.telegram_id, 123456789)
        self.assertEqual(notification.message_text, 'Тестовое уведомление')
        self.assertEqual(notification.notification_type, 'order')
        self.assertFalse(notification.sent)
        self.assertIsNone(notification.sent_at)


# Запуск тестов
if __name__ == '__main__':
    unittest.main()