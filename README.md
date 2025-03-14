# FlowerShop
Django, aiogram, TG-bot


Цель: вебсайт для заказа доставки цветов с базовой интеграцией заказов через телеграм-бота. Telegram бот, вступает в работу после оформления заказа:
получение заказа с информацией о букетах и доставке (для магазина). В сообщение входят изображение букета, стоимость, дата, время и место доставки

Этот объединенный бот имеет полный функционал:

    Для клиентов:
        Регистрация и привязка аккаунта
        Просмотр своих заказов
        Получение уведомлений о статусе заказов

    Для администратора:
        Получение подробных уведомлений о новых заказах
        Просмотр фотографий товаров в заказах
        Уведомления работают как для клиентов с Telegram-аккаунтами, так и без них

Все асинхронные операции правильно обработаны через декораторы sync_to_async, добавлено логирование для отслеживания работы бота.

Telegram-бот, который:

    Работает с обычными пользователями: регистрация, привязка аккаунтов, просмотр заказов
    Отправляет администратору полную информацию о новых заказах с изображениями товаров
    Корректно обрабатывает заказы от пользователей и с привязкой к Telegram, и без неё

Этот подход с правильным использованием sync_to_async решает типичные проблемы интеграции между синхронным Django и асинхронным Telegram API.
