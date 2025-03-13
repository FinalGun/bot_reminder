## bot_reminder

### Технологии:

Python, telebot, threading, sqlite3, logging

### Описание:
Небольшой телеграм бот для напоминания о событиях. Получает, валидирует и записывает события в базу данных.
Программа разделена на два потока. Первый поток занимается записыванием событий, второй поток отдает эти события.

### Как развернуть:
Для работы нужны переменные окружения:

- TELEGRAM_TOKEN - токен вашего бота
- TELEGRAM_CHAT_ID - id чата для отправки сообщений


