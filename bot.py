import telebot
from telebot.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import requests
import threading
import time
import re
import json
from datetime import datetime
from flask import Flask
import os

TOKEN = "8976297430:AAH0EGG6kp089dQdhHWtLQEUdyI3Yo2YAEo"
bot = telebot.TeleBot(TOKEN)

YOUR_USER_ID = 5732725470
SBERBANK_TOKEN = "СЮДА_ТОКЕН_ОТ_BOTFATHER_ДЛЯ_ЮKASSA"

GIFTS_FILE = "gifts_cache.json"

base_gifts = {
    "🧸 Плюшевый мишка": {"id": "5170233102089322756", "price": 15, "limited": False},
    "❤️ Сердце": {"id": "5170145012310081615", "price": 15, "limited": False},
    "🎁 Подарок": {"id": "5170250947678437525", "price": 25, "limited": False},
    "🌹 Роза": {"id": "5168103777563050263", "price": 25, "limited": False},
    "🎂 Торт": {"id": "5170144170496491616", "price": 50, "limited": False},
    "💐 Букет": {"id": "5170314324215857265", "price": 50, "limited": False},
    "🚀 Ракета": {"id": "5170564780938756245", "price": 50, "limited": False},
    "🍾 Шампанское": {"id": "6028601630662853006", "price": 50, "limited": False},
    "🏆 Кубок": {"id": "5168043875654172773", "price": 100, "limited": False},
    "💍 Кольцо": {"id": "5170690322832818290", "price": 100, "limited": False},
    "💎 Алмаз": {"id": "5170521118301225164", "price": 100, "limited": False},
    "🧸 Новогодний мишка": {"id": "5956217000635139069", "price": 50, "limited": True},
    "🎄 Новогодняя ёлка": {"id": "5922558454332916696", "price": 50, "limited": True},
    "🧸 Мишка 14 февраля": {"id": "5800655655995968830", "price": 50, "limited": True},
    "❤️ Сердце 14 февраля": {"id": "5801108895304779062", "price": 50, "limited": True},
    "🧸 Мишка 1 мая": {"id": "5866352046986232958", "price": 50, "limited": True},
    "🧸 Мишка 17 марта": {"id": "5893356958802511476", "price": 50, "limited": True},
    "🧸 Мишка 1 апреля": {"id": "5935895822435615975", "price": 50, "limited": True},
    "🧸 Пасхальный мишка": {"id": "5969796561943660080", "price": 50, "limited": True},
    "🧸 Мишка ЧМ2026": {"id": "5974210632977745012", "price": 50, "limited": True},
    "🧸 Мишка 13 августа": {"id": "6046178578163303744", "price": 50, "limited": True}
}

gift_names = {}

def load_gifts_cache():
    try:
        with open(GIFTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def save_gifts_cache(gifts_data):
    try:
        with open(GIFTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(gifts_data, f, ensure_ascii=False, indent=2)
    except:
        pass

def update_gifts_from_api():
    global gift_names
    print("🔄 Обновление списка подарков...")
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getAvailableGifts"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return False
        data = response.json()
        if not data.get('ok'):
            return False
        gifts = data.get('result', {}).get('gifts', [])
        if not gifts:
            return False
        new_gifts = {}
        for gift in gifts:
            title = gift.get('title', {}).get('ru', 'Неизвестный подарок')
            gift_id = str(gift.get('id', ''))
            if not gift_id:
                continue
            price = gift.get('star_count', 0)
            is_limited = gift.get('is_limited', False)
            display_name = f"{get_gift_emoji(title)} {title}"
            new_gifts[display_name] = {
                "id": gift_id,
                "price": price,
                "limited": is_limited,
                "title": title,
                "emoji": get_gift_emoji(title)
            }
        for old_name, old_data in gift_names.items():
            if old_name not in new_gifts:
                new_gifts[old_name] = old_data
        gift_names = new_gifts
        save_gifts_cache(gift_names)
        return True
    except:
        return False

def get_gift_emoji(title):
    emoji_map = {
        "Плюшевый мишка": "🧸", "Сердце": "❤️", "Подарок": "🎁",
        "Роза": "🌹", "Торт": "🎂", "Букет": "💐", "Ракета": "🚀",
        "Шампанское": "🍾", "Кубок": "🏆", "Кольцо": "💍", "Алмаз": "💎"
    }
    for key, emoji in emoji_map.items():
        if key in title:
            return emoji
    return "🎁"

def get_gift_id(gift_name):
    if gift_name in gift_names:
        return gift_names[gift_name].get("id")
    return None

def background_gift_updater():
    while True:
        try:
            update_gifts_from_api()
            time.sleep(43200)
        except:
            time.sleep(3600)

translations = {
    "ru": {
        "gifts_title": "🎁 Доступные подарки:\n\n",
        "gifts_hint": "\n📌 Напиши НОМЕР подарка (например, 1)",
        "choose_gift": "🎁 Ты выбрал: {gift} ({price} ⭐️)\n\nКому отправить?",
        "to_self": "👤 Себе",
        "to_other": "👥 Другому",
        "enter_username": "✏️ Введи @username получателя\n\n💡 Или отправь ID пользователя (число)",
        "user_found": "✅ Найден: @{username}",
        "user_not_found": "❌ Пользователь @{username} не найден\n\n💡 Попробуй ввести ID\n📌 Узнай ID в @id_bot",
        "enter_number": "❌ Напиши НОМЕР подарка",
        "wrong_number": "❌ Такого номера нет",
        "select_gift_first": "❌ Сначала выбери подарок",
        "sending_to_self": "👤 Отправляю тебе!",
        "sending_to_other": "👥 Введи username или ID",
        "select_payment": "💳 Выбери способ оплаты:",
        "pay_stars": "⭐️ Оплатить Stars",
        "pay_card": "💳 Оплатить картой",
        "id_bot_hint": "📌 **Как узнать ID?**\n\n1️⃣ Зайди в @id_bot\n2️⃣ Отправь любое сообщение\n3️⃣ Получи свой ID",
        "username_hint": "💡 Введи username или ID получателя",
        "enter_id": "✅ Отправляем подарок ID: {user_id}"
    }
}

user_data = {}

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_gifts = KeyboardButton("🎁 Подарки")
    btn_update = KeyboardButton("🔄 Обновить")
    btn_help = KeyboardButton("❓ Помощь")
    btn_profile = KeyboardButton("👤 Профиль")
    keyboard.add(btn_gifts, btn_update)
    keyboard.add(btn_profile, btn_help)
    return keyboard

def show_profile(message):
    user_id = message.from_user.id
    user = bot.get_chat(user_id)
    bot.reply_to(message, f"👤 Профиль\n\n📛 {user.first_name}\n🆔 {user.id}")

def show_help(message):
    bot.reply_to(message, "❓ **Помощь**\n\n1. Нажми '🎁 Подарки'\n2. Выбери номер\n3. Укажи получателя\n4. Оплати\n\n👤 @PruzrakTytR", parse_mode="Markdown")

def send_notification(buyer_id, buyer_username, gift_name, price, recipient_id, payment_type, recipient_username=None):
    try:
        message = f"🛍️ НОВАЯ ПОКУПКА!\n\n👤 Покупатель: {buyer_id}\n🎁 {gift_name}\n⭐️ {price} Stars\n📦 Получатель: {recipient_id}"
        bot.send_message(YOUR_USER_ID, message)
    except:
        pass

def send_real_gift(user_id, gift_name, recipient_id=None):
    if recipient_id is None:
        recipient_id = user_id
    gift_id = get_gift_id(gift_name)
    if not gift_id:
        return False
    try:
        bot.send_gift(user_id=recipient_id, gift_id=gift_id, text="🎉 Вам отправили подарок! ❤️")
        return True
    except:
        return False

def find_user_by_username(username):
    username = username.strip().lstrip("@")
    if not username:
        return None
    try:
        return bot.get_chat(f"@{username}")
    except:
        return None

def find_user_by_id(user_id_str):
    try:
        return bot.get_chat(int(user_id_str))
    except:
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_data[user_id] = {}
    bot.send_message(
        message.chat.id,
        "🎁 **Добро пожаловать в GiftMart!**\n\nВыбери действие:",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

@bot.message_handler(commands=['update'])
def update_gifts_command(message):
    bot.reply_to(message, "🔄 Обновляю...")
    if update_gifts_from_api():
        bot.reply_to(message, "✅ Список обновлён!")
    else:
        bot.reply_to(message, "❌ Ошибка")

@bot.message_handler(commands=['gifts'])
def show_gifts(message):
    if not gift_names:
        bot.reply_to(message, "❌ Список пуст. Нажми '🔄 Обновить'")
        return
    text = "🎁 Подарки:\n\n"
    for i, (name, data) in enumerate(gift_names.items(), 1):
        price = data.get("price", 0)
        limited = " ⭐️Лимит" if data.get("limited", False) else ""
        text += f"{i}. {name} — {price} ⭐️{limited}\n"
    text += "\n📌 Напиши номер подарка"
    bot.reply_to(message, text)

@bot.message_handler(func=lambda message: message.text in ["🎁 Подарки", "🔄 Обновить", "👤 Профиль", "❓ Помощь"])
def handle_menu_buttons(message):
    if message.text == "🎁 Подарки":
        show_gifts(message)
    elif message.text == "🔄 Обновить":
        update_gifts_command(message)
    elif message.text == "👤 Профиль":
        show_profile(message)
    elif message.text == "❓ Помощь":
        show_help(message)

@bot.message_handler(func=lambda message: True)
def handle_choice(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {}
    
    if message.text in ["🎁 Подарки", "🔄 Обновить", "👤 Профиль", "❓ Помощь"]:
        return
    
    if user_data[user_id].get("waiting_for_username"):
        handle_username_input(message)
        return
    
    try:
        text = message.text.strip()
        if not text.isdigit():
            bot.reply_to(message, "❌ Напиши НОМЕР подарка")
            return
        index = int(text) - 1
        gift_list = list(gift_names.items())
        if index < 0 or index >= len(gift_list):
            bot.reply_to(message, "❌ Такого номера нет")
            return
        gift_name, gift_data = gift_list[index]
        price = gift_data.get("price", 0)
        user_data[user_id]["gift_name"] = gift_name
        user_data[user_id]["price"] = price
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("👤 Себе", callback_data="recipient_self"),
            InlineKeyboardButton("👥 Другому", callback_data="recipient_other")
        )
        bot.send_message(message.chat.id, f"🎁 {gift_name} ({price} ⭐️)\n\nКому отправить?", reply_markup=keyboard)
    except:
        bot.reply_to(message, "❌ Ошибка. Попробуй снова")

@bot.callback_query_handler(func=lambda call: call.data.startswith("recipient_"))
def handle_recipient_choice(call):
    user_id = call.from_user.id
    if "gift_name" not in user_data.get(user_id, {}):
        bot.answer_callback_query(call.id, "❌ Сначала выбери подарок")
        return
    if call.data == "recipient_self":
        user_data[user_id]["recipient_id"] = user_id
        show_payment_options(call.message, user_id)
    else:
        user_data[user_id]["waiting_for_username"] = True
        bot.send_message(call.message.chat.id, "✏️ Введи @username или ID получателя")

def handle_username_input(message):
    user_id = message.from_user.id
    input_text = message.text.strip()
    if input_text.isdigit():
        user = find_user_by_id(input_text)
        if user:
            user_data[user_id]["recipient_id"] = user.id
            user_data[user_id]["waiting_for_username"] = False
            show_payment_options(message, user_id)
            return
    username = input_text.lstrip("@")
    user = find_user_by_username(username)
    if user:
        user_data[user_id]["recipient_id"] = user.id
        user_data[user_id]["waiting_for_username"] = False
        show_payment_options(message, user_id)
    else:
        bot.reply_to(message, f"❌ Пользователь @{username} не найден\n\n💡 Попробуй ввести ID\n📌 Узнай ID в @id_bot")

def show_payment_options(message, user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("⭐️ Stars", callback_data="pay_stars"),
        InlineKeyboardButton("💳 Карта", callback_data="pay_card")
    )
    bot.send_message(message.chat.id, "💳 Выбери оплату:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def handle_payment_choice(call):
    user_id = call.from_user.id
    if call.data == "pay_stars":
        send_invoice_stars(call.message, user_id)
    else:
        bot.answer_callback_query(call.id, "❌ Временно недоступно")

def send_invoice_stars(message, buyer_id):
    gift_name = user_data[buyer_id].get("gift_name")
    price = user_data[buyer_id].get("price")
    recipient_id = user_data[buyer_id].get("recipient_id", buyer_id)
    if not gift_name or not price:
        return
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(f"⭐️ Оплатить {price} Stars", pay=True))
    try:
        bot.send_invoice(
            chat_id=message.chat.id,
            title=f"🎁 {gift_name}",
            description=f"Покупка подарка",
            invoice_payload=f"stars_{gift_name}_{YOUR_USER_ID}_{recipient_id}_{buyer_id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label=gift_name, amount=price)],
            reply_markup=keyboard
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    user_id = message.from_user.id
    payload = message.successful_payment.invoice_payload
    parts = payload.split("_")
    gift_name = parts[1]
    recipient_id = int(parts[3])
    buyer_id = int(parts[4])
    price = user_data.get(user_id, {}).get("price", 0)
    gift_sent = send_real_gift(buyer_id, gift_name, recipient_id)
    username = message.from_user.username or "не указан"
    send_notification(buyer_id, username, gift_name, price, recipient_id, "stars")
    if gift_sent:
        bot.send_message(message.chat.id, "🎉 Подарок отправлен!")
    else:
        bot.send_message(message.chat.id, "⚠️ Ошибка отправки, свяжись с @PruzrakTytR")

# ═══════════════════════════════════════════════════════════
# 🌐 ВЕБ-СЕРВЕР ДЛЯ RENDER
# ═══════════════════════════════════════════════════════════

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Бот работает!"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()
print("🌐 Flask-сервер запущен!")

# ═══════════════════════════════════════════════════════════
# 🚀 ЗАПУСК
# ═══════════════════════════════════════════════════════════

def main():
    global gift_names
    saved = load_gifts_cache()
    if saved:
        gift_names = saved
    else:
        gift_names = base_gifts.copy()
    updater = threading.Thread(target=background_gift_updater, daemon=True)
    updater.start()
    time.sleep(5)
    update_gifts_from_api()
    print("🤖 Бот готов!")
    bot.infinity_polling()

if __name__ == "__main__":
    main()