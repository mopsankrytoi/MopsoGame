MopsoGame — стартовый проект Telegram-бота и Mini App

Что уже есть:
- /start с кнопкой открытия Mini App
- профиль пользователя
- очки и уровни
- задания с наградами
- мини-игра «тапай»
- команда администратора /notify Текст уведомления
- проверка Telegram Web App initData на сервере

ВАЖНО:
1. Не отправляй BOT_TOKEN никому и не вставляй его в публичный код.
2. Приложение должно быть опубликовано по HTTPS.
3. SQLite в бесплатном облачном хостинге может сбрасываться при перезапуске/пересоздании сервиса. Для постоянных данных нужен постоянный диск или внешняя база данных.
4. Для Telegram Mini App открой бота и нажми кнопку из /start. Прямое открытие сайта в браузере не авторизует пользователя.

Переменные окружения:
BOT_TOKEN = токен от @BotFather
WEBAPP_URL = HTTPS адрес опубликованного приложения, например https://your-app.onrender.com
ADMIN_ID = твой числовой Telegram ID (необязательно; нужен для /notify)

Запуск локально:
pip install -r requirements.txt
python main.py

Для Render:
- Создай новый Web Service из GitHub-репозитория с этими файлами.
- Build Command: pip install -r requirements.txt
- Start Command: python main.py
- Добавь BOT_TOKEN.
- Добавь WEBAPP_URL после получения адреса сервиса.
- Добавь ADMIN_ID (необязательно).
- После первого деплоя открой адрес приложения через кнопку /start в Telegram.

Как узнать числовой Telegram ID:
Напиши @userinfobot в Telegram. Не путай ID с токеном бота.
