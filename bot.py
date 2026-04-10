import asyncio
import logging
import json
import os
import time

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
    InlineKeyboardMarkup, InlineKeyboardButton
)

logging.basicConfig(level=logging.INFO)

# ====== НАСТРОЙКИ ======
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден. Добавь переменную окружения BOT_TOKEN.")

BOT_USERNAME = "kadima_cafe_bot"  # без @ (можно поменять позже)

# ✅ ДВА АДМИНА
ADMIN_IDS = {6013591658, 331273289}

# ✅ Ник второго админа
SECOND_ADMIN_USERNAME = "@Azi_za_M"

CHANNEL_ID = "@Kadimasignaturetaste"

# ✅ GitHub Pages Bakery CHOKOART
WEBAPP_URL = "https://tahirovdd-lang.github.io/bakery-chokoart/?v=1"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ====== АНТИ-ДУБЛЬ START ======
_last_start: dict[int, float] = {}

def allow_start(user_id: int, ttl: float = 2.0) -> bool:
    now = time.time()
    prev = _last_start.get(user_id, 0.0)
    if now - prev < ttl:
        return False
    _last_start[user_id] = now
    return True

# ====== КНОПКИ ======
BTN_OPEN_MULTI = "Ochish • Открыть • Open"

def kb_webapp_reply() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_OPEN_MULTI, web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True
    )

def kb_channel_deeplink() -> InlineKeyboardMarkup:
    deeplink = f"https://t.me/{BOT_USERNAME}?startapp=menu"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=BTN_OPEN_MULTI, url=deeplink)]]
    )

# ====== ТЕКСТ ======
def welcome_text() -> str:
    return (
        "🇷🇺 Добро пожаловать в <b>Bakery CHOKOART</b>! 👋 "
        "Выберите любимые позиции и оформите заказ — просто нажмите «Открыть» ниже.\n\n"
        "🇺🇿 <b>Bakery CHOKOART</b> ga xush kelibsiz! 👋 "
        "Sevimli mahsulotlarni tanlang va buyurtma bering — buning uchun pastdagi «Ochish» tugmasini bosing.\n\n"
        "🇬🇧 Welcome to <b>Bakery CHOKOART</b>! 👋 "
        "Choose your favorite items and place an order — just tap “Open” below."
    )

# ====== /start ======
@dp.message(CommandStart())
async def start(message: types.Message):
    if not allow_start(message.from_user.id):
        return
    await message.answer(welcome_text(), reply_markup=kb_webapp_reply())

@dp.message(Command("startapp"))
async def startapp(message: types.Message):
    if not allow_start(message.from_user.id):
        return
    await message.answer(welcome_text(), reply_markup=kb_webapp_reply())

# ====== ПОСТ В КАНАЛ ======
@dp.message(Command("post_menu"))
async def post_menu(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⛔️ Нет доступа.")

    text = (
        "🇷🇺 <b>Bakery CHOKOART</b>\nНажмите кнопку ниже, чтобы открыть меню.\n\n"
        "🇺🇿 <b>Bakery CHOKOART</b>\nPastdagi tugma orqali menyuni oching.\n\n"
        "🇬🇧 <b>Bakery CHOKOART</b>\nTap the button below to open the menu."
    )

    try:
        sent = await bot.send_message(CHANNEL_ID, text, reply_markup=kb_channel_deeplink())
        try:
            await bot.pin_chat_message(CHANNEL_ID, sent.message_id, disable_notification=True)
            await message.answer("✅ Пост отправлен в канал и закреплён.")
        except Exception:
            await message.answer(
                "✅ Пост отправлен в канал.\n"
                "⚠️ Не удалось закрепить — дай боту право «Закреплять сообщения»."
            )
    except Exception as e:
        logging.exception("CHANNEL POST ERROR")
        await message.answer(f"❌ Ошибка отправки в канал: <code>{e}</code>")

# ====== ВСПОМОГАТЕЛЬНЫЕ ======
def fmt_sum(n: int) -> str:
    try:
        n = int(n)
    except Exception:
        n = 0
    return f"{n:,}".replace(",", " ")

def tg_label(u: types.User) -> str:
    return f"@{u.username}" if u.username else u.full_name

def clean_str(v) -> str:
    return ("" if v is None else str(v)).strip()

def safe_int(v, default=0) -> int:
    try:
        if v is None or isinstance(v, bool):
            return default
        if isinstance(v, (int, float)):
            return int(v)
        s = str(v).strip().replace(" ", "")
        if s == "":
            return default
        return int(float(s))
    except Exception:
        return default

# ====== ЧТЕНИЕ ЗАКАЗА ======
def build_order_lines(data: dict) -> tuple[list[str], dict]:
    order_dict: dict = {}

    raw_order = data.get("order")
    raw_items = data.get("items")
    raw_cart = data.get("cart")

    if isinstance(raw_order, dict):
        for k, v in raw_order.items():
            q = safe_int(v, 0)
            if q > 0:
                order_dict[str(k)] = q

    if not order_dict and isinstance(raw_cart, dict):
        for k, v in raw_cart.items():
            q = safe_int(v, 0)
            if q > 0:
                order_dict[str(k)] = q

    lines: list[str] = []
    if isinstance(raw_items, list):
        for it in raw_items:
            if not isinstance(it, dict):
                continue
            name = clean_str(it.get("name")) or clean_str(it.get("id")) or "—"
            qty = safe_int(it.get("qty"), 0)
            if qty <= 0:
                continue
            price = safe_int(it.get("price"), 0)
            if price > 0:
                lines.append(f"• {name} × {qty} = {fmt_sum(price * qty)} сум")
            else:
                lines.append(f"• {name} × {qty}")

    if not lines and order_dict:
        for k, q in order_dict.items():
            lines.append(f"• {k} × {q}")

    if not lines:
        lines = ["⚠️ Корзина пустая"]

    return lines, order_dict

# ====== ЗАКАЗ ИЗ WEBAPP ======
@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    raw = message.web_app_data.data
    await message.answer("✅ <b>Получил заказ.</b> Обрабатываю…")

    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        data = {}

    lines, _ = build_order_lines(data)

    total_str = clean_str(data.get("total")) or "0"
    payment = clean_str(data.get("payment")) or "—"
    order_type = clean_str(data.get("type")) or "—"
    address = clean_str(data.get("address")) or "—"
    phone = clean_str(data.get("phone")) or "—"
    comment = clean_str(data.get("comment"))
    order_id = clean_str(data.get("order_id")) or "—"

    admin_text = (
        "🚨 <b>НОВЫЙ ЗАКАЗ Bakery CHOKOART</b>\n"
        f"🆔 <b>{order_id}</b>\n\n"
        + "\n".join(lines) +
        f"\n\n💰 <b>Сумма:</b> {total_str} сум"
        f"\n🚚 <b>Тип:</b> {order_type}"
        f"\n💳 <b>Оплата:</b> {payment}"
        f"\n📍 <b>Адрес:</b> {address}"
        f"\n📞 <b>Телефон:</b> {phone}"
        f"\n👤 <b>Telegram:</b> {tg_label(message.from_user)}"
    )

    if comment:
        admin_text += f"\n💬 <b>Комментарий:</b> {comment}"

    # ✅ Отправка заказа обоим администраторам
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text)
        except Exception as e:
            logging.exception(f"ORDER SEND ERROR to admin {admin_id}: {e}")

    await message.answer(
        "✅ <b>Ваш заказ принят!</b>\n"
        "🙏 Спасибо, мы скоро свяжемся с вами."
    )

# ====== КОМАНДА ДЛЯ ПРОВЕРКИ АДМИНОВ ======
@dp.message(Command("admins"))
async def admins_info(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⛔️ Нет доступа.")

    await message.answer(
        "👑 <b>Администраторы бота:</b>\n"
        "• ID: <code>6013591658</code>\n"
        "• ID: <code>331273289</code> — @Azi_za_M"
    )

# ====== ЗАПУСК ======
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
