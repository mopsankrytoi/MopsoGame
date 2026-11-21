import os
import json
import hmac
import hashlib
import sqlite3
import threading
import time
from urllib.parse import parse_qsl
from flask import Flask, request, jsonify, send_from_directory
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
WEBAPP_URL = os.environ.get("WEBAPP_URL", "").strip().rstrip("/")
ADMIN_ID = os.environ.get("ADMIN_ID", "").strip()
PORT = int(os.environ.get("PORT", "8080"))
DB_PATH = os.environ.get("DB_PATH", "mopsogame.db")

if not BOT_TOKEN:
    raise RuntimeError("Set BOT_TOKEN in your hosting environment.")
if not WEBAPP_URL.startswith("https://"):
    raise RuntimeError("Set WEBAPP_URL to your public HTTPS app address.")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__, static_folder="static")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT DEFAULT '',
            first_name TEXT DEFAULT '', points INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1, joined_at INTEGER
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS claims (
            user_id INTEGER, task_id TEXT, claimed_at INTEGER,
            PRIMARY KEY(user_id, task_id)
        )""")

def verify_init_data(init_data):
    if not init_data:
        return None
    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = values.pop("hash", None)
    if not received_hash:
        return None
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        return None
    try:
        user = json.loads(values.get("user", "{}"))
        auth_date = int(values.get("auth_date", "0"))
        if time.time() - auth_date > 86400:
            return None
        return user
    except Exception:
        return None

def current_user():
    data = request.headers.get("X-Telegram-Init-Data", "")
    user = verify_init_data(data)
    if not user or not user.get("id"):
        return None
    return user

def ensure_user(user):
    with db() as con:
        con.execute("""INSERT INTO users(user_id, username, first_name, joined_at)
            VALUES(?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET username=excluded.username,
            first_name=excluded.first_name""",
            (int(user["id"]), user.get("username", ""),
             user.get("first_name", "Player"), int(time.time())))

TASKS = [
    {"id": "welcome", "title": "Добро пожаловать", "desc": "Открой приложение MopsoGame", "reward": 10},
    {"id": "tap10", "title": "Первый игровой шаг", "desc": "Нажми на игровую кнопку 10 раз", "reward": 20},
    {"id": "profile", "title": "Загляни в профиль", "desc": "Посмотри свой игровой профиль", "reward": 10},
]

@app.get("/")
def home():
    return send_from_directory("static", "index.html")

@app.get("/<path:path>")
def static_files(path):
    return send_from_directory("static", path)

@app.get("/api/me")
def me():
    user = current_user()
    if not user:
        return jsonify({"error": "Открой приложение через Telegram"}), 401
    ensure_user(user)
    with db() as con:
        row = con.execute("SELECT * FROM users WHERE user_id=?", (int(user["id"]),)).fetchone()
        claimed = {r["task_id"] for r in con.execute(
            "SELECT task_id FROM claims WHERE user_id=?", (int(user["id"]),)).fetchall()}
    data = dict(row)
    data["next_level"] = data["level"] * 100
    data["tasks"] = [{**t, "done": t["id"] in claimed} for t in TASKS]
    return jsonify(data)

@app.post("/api/tap")
def tap():
    user = current_user()
    if not user:
        return jsonify({"error": "Нет подтверждения Telegram"}), 401
    ensure_user(user)
    with db() as con:
        con.execute("UPDATE users SET points=points+1 WHERE user_id=?", (int(user["id"]),))
        con.execute("UPDATE users SET level=1+(points/100) WHERE user_id=?", (int(user["id"]),))
        row = con.execute("SELECT points, level FROM users WHERE user_id=?", (int(user["id"]),)).fetchone()
    return jsonify(dict(row))

@app.post("/api/claim")
def claim():
    user = current_user()
    if not user:
        return jsonify({"error": "Нет подтверждения Telegram"}), 401
    task_id = (request.json or {}).get("task_id", "")
    task = next((t for t in TASKS if t["id"] == task_id), None)
    if not task:
        return jsonify({"error": "Задание не найдено"}), 404
    ensure_user(user)
    with db() as con:
        try:
            con.execute("INSERT INTO claims(user_id, task_id, claimed_at) VALUES(?,?,?)",
                        (int(user["id"]), task_id, int(time.time())))
        except sqlite3.IntegrityError:
            return jsonify({"error": "Задание уже выполнено"}), 400
        con.execute("UPDATE users SET points=points+? WHERE user_id=?",
                    (task["reward"], int(user["id"])))
        con.execute("UPDATE users SET level=1+(points/100) WHERE user_id=?", (int(user["id"]),))
        row = con.execute("SELECT points, level FROM users WHERE user_id=?", (int(user["id"]),)).fetchone()
    return jsonify({"ok": True, "points": row["points"], "level": row["level"]})

@bot.message_handler(commands=["start"])
def start(message):
    if not WEBAPP_URL:
        bot.reply_to(message, "Приложение пока не настроено.")
        return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎮 Открыть MopsoGame", web_app=WebAppInfo(url=WEBAPP_URL)))
    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}! Добро пожаловать в MopsoGame.\n"
        "Играй, выполняй задания и повышай уровень!",
        reply_markup=markup
    )

@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.reply_to(message, "Команды:\n/start — открыть приложение\n/help — помощь")

@bot.message_handler(commands=["notify"])
def notify(message):
    if not ADMIN_ID or str(message.from_user.id) != ADMIN_ID:
        bot.reply_to(message, "Эта команда доступна только администратору.")
        return
    text = message.text.partition(" ")[2].strip()
    if not text:
        bot.reply_to(message, "Использование: /notify Текст уведомления")
        return
    with db() as con:
        ids = [r["user_id"] for r in con.execute("SELECT user_id FROM users").fetchall()]
    sent = 0
    for uid in ids:
        try:
            bot.send_message(uid, "🔔 MopsoGame\n\n" + text)
            sent += 1
        except Exception:
            pass
    bot.reply_to(message, f"Уведомление отправлено: {sent} пользователям.")

def run_bot():
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT, threaded=True)
