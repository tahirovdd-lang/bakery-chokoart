import asyncio
import logging
import json
import os
import time

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ====== НАСТРОЙКИ ======
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден. Добавь переменную окружения BOT_TOKEN.")

# ВАЖНО: укажи реальный username бота БЕЗ @
BOT_USERNAME = "kadima_cafe_bot"

# ✅ АДМИНЫ
ADMIN_IDS = {6013591658, 331273289}

# ✅ WEB APP
WEBAPP_URL = "https://tahirovdd-lang.github.io/bakery-chokoart/?v=1"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML"),
)
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
BTN_OPEN_MULTI = "Наш каталог"

def kb_webapp_reply() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_OPEN_MULTI, web_app=WebAppInfo(url=WEBAPP_URL))]
        ],
        resize_keyboard=True
    )

def kb_catalog_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Наш каталог", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )

# ====== ТЕКСТ ======
def welcome_text() -> str:
    return (
        "🇷🇺 Добро пожаловать в <b>Bakery CHOKOART</b>! 👋\n"
        "Нажмите кнопку <b>«Наш каталог»</b>, чтобы открыть меню и оформить заказ.\n\n"
        "🇺🇿 <b>Bakery CHOKOART</b> ga xush kelibsiz! 👋\n"
        "<b>«Наш каталог»</b> tugmasini bosib menyuni oching va buyurtma bering.\n\n"
        "🇬🇧 Welcome to <b>Bakery CHOKOART</b>! 👋\n"
        "Tap <b>“Наш каталог”</b> to open the menu and place your order."
    )

def pinned_catalog_text() -> str:
    return (
        "📌 <b>Наш каталог</b>\n\n"
        "Добро пожаловать в <b>Bakery CHOKOART</b>!\n"
        "Нажмите кнопку ниже, чтобы открыть каталог и оформить заказ."
    )

# ====== СТАРТ ======
@dp.message(CommandStart())
async def start(message: types.Message):
    logging.info(
        "START | chat_id=%s | chat_type=%s | user_id=%s | text=%s",
        message.chat.id,
        message.chat.type,
        message.from_user.id if message.from_user else None,
        message.text,
    )

    if not allow_start(message.from_user.id):
        return

    await message.answer(welcome_text(), reply_markup=kb_webapp_reply())

@dp.message(Command("startapp"))
async def startapp(message: types.Message):
    logging.info(
        "STARTAPP | chat_id=%s | chat_type=%s | user_id=%s | text=%s",
        message.chat.id,
        message.chat.type,
        message.from_user.id if message.from_user else None,
        message.text,
    )

    if not allow_start(message.from_user.id):
        return

    await message.answer(welcome_text(), reply_markup=kb_webapp_reply())

# ====== CHAT ID ======
@dp.message(Command("chatid"))
async def chat_id_info(message: types.Message):
    logging.info(
        "CHATID COMMAND | chat_id=%s | chat_type=%s | title=%s | user_id=%s | text=%s",
        message.chat.id,
        message.chat.type,
        message.chat.title,
        message.from_user.id if message.from_user else None,
        message.text,
    )

    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⛔️ Нет доступа.")

    try:
        await message.answer(
            "🆔 <b>ID текущего чата:</b> "
            f"<code>{message.chat.id}</code>\n"
            f"📛 <b>Тип чата:</b> <code>{message.chat.type}</code>\n"
            f"📝 <b>Название:</b> {message.chat.title or 'Личный чат'}"
        )
    except Exception as e:
        logging.exception("CHATID ANSWER ERROR")
        try:
            await bot.send_message(
                message.from_user.id,
                f"❌ Не смог ответить в группе.\nОшибка: <code>{e}</code>\n"
                f"chat_id: <code>{message.chat.id}</code>"
            )
        except Exception:
            pass

# ====== ПРОВЕРКА ПИСЬМА В ГРУППУ ======
@dp.message(Command("testgroup"))
async def testgroup(message: types.Message):
    logging.info(
        "TESTGROUP COMMAND | chat_id=%s | chat_type=%s | title=%s | user_id=%s | text=%s",
        message.chat.id,
        message.chat.type,
        message.chat.title,
        message.from_user.id if message.from_user else None,
        message.text,
    )

    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⛔️ Нет доступа.")

    try:
        await bot.send_message(
            message.chat.id,
            "✅ Тестовое сообщение от бота.\nБот видит этот чат и умеет сюда писать."
        )
    except Exception as e:
        logging.exception("TESTGROUP ERROR")
        try:
            await bot.send_message(
                message.from_user.id,
                f"❌ Бот не смог написать в группу.\nОшибка: <code>{e}</code>\n"
                f"chat_id: <code>{message.chat.id}</code>"
            )
        except Exception:
            pass

# ====== КАТАЛОГ ======
@dp.message(Command("post_catalog"))
async def post_catalog(message: types.Message):
    logging.info(
        "POST_CATALOG | chat_id=%s | chat_type=%s | title=%s | user_id=%s | text=%s",
        message.chat.id,
        message.chat.type,
        message.chat.title,
        message.from_user.id if message.from_user else None,
        message.text,
    )

    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⛔️ Нет доступа.")

    try:
        sent = await bot.send_message(
            message.chat.id,
            pinned_catalog_text(),
            reply_markup=kb_catalog_inline()
        )
        try:
            await bot.pin_chat_message(
                message.chat.id,
                sent.message_id,
                disable_notification=True
            )
            await message.answer("✅ Сообщение «Наш каталог» отправлено и закреплено.")
        except Exception as e:
            logging.exception("PIN ERROR")
            await message.answer(
                f"✅ Сообщение отправлено.\n"
                f"⚠️ Закрепить не удалось: <code>{e}</code>"
            )
    except Exception as e:
        logging.exception("POST_CATALOG ERROR")
        try:
            await message.answer(f"❌ Ошибка отправки: <code>{e}</code>")
        except Exception:
            try:
                await bot.send_message(
                    message.from_user.id,
                    f"❌ Бот увидел команду, но не смог ответить в группе.\nОшибка: <code>{e}</code>"
                )
            except Exception:
                pass

# ====== ЗАКАЗЫ ======
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

@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    logging.info(
        "WEB_APP_DATA | chat_id=%s | user_id=%s",
        message.chat.id,
        message.from_user.id if message.from_user else None,
    )

    raw = message.web_app_data.data
    await message.answer("✅ <b>Получил заказ.</b> Обрабатываю…")

    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        data = {}

    lines, _ = build_order_lines(data)

    total_num = safe_int(data.get("total_num"), 0)
    if total_num <= 0:
        total_num = safe_int(data.get("total"), 0)

    payment_check = clean_str(data.get("payment"))
    order_type_check = clean_str(data.get("type"))
    address_check = clean_str(data.get("address"))
    phone_check = clean_str(data.get("phone"))
    order_id_check = clean_str(data.get("order_id"))

    if not lines or lines == ["⚠️ Корзина пустая"]:
        await message.answer("❌ Корзина пустая. Добавьте товары в заказ.")
        return

    if total_num <= 0:
        await message.answer("❌ Сумма заказа не указана. Проверьте корзину.")
        return

    if not payment_check:
        await message.answer("❌ Выберите способ оплаты.")
        return

    if not order_type_check:
        await message.answer("❌ Выберите тип заказа: доставка или самовывоз.")
        return

    if order_type_check == "delivery" and not address_check:
        await message.answer("❌ Заполните адрес доставки.")
        return

    if order_type_check == "delivery" and not phone_check:
        await message.answer("❌ Введите номер телефона для доставки.")
        return

    if not order_id_check:
        await message.answer("❌ Не удалось создать номер заказа. Попробуйте оформить заказ ещё раз.")
        return

    total_str = clean_str(data.get("total_with_delivery")) or clean_str(data.get("total")) or "0"
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

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text)
        except Exception as e:
            logging.exception("ORDER SEND ERROR to admin %s: %s", admin_id, e)

    await message.answer(
        "✅ <b>Ваш заказ принят!</b>\n"
        "🙏 Спасибо, мы скоро свяжемся с вами."
    )

# ====== СТАТУС БОТА В ЧАТЕ ======
@dp.my_chat_member()
async def on_my_chat_member(event: types.ChatMemberUpdated):
    logging.info(
        "MY_CHAT_MEMBER | chat_id=%s | chat_type=%s | title=%s | old=%s | new=%s",
        event.chat.id,
        event.chat.type,
        event.chat.title,
        event.old_chat_member.status,
        event.new_chat_member.status,
    )

    try:
        if event.new_chat_member.status in ("administrator", "member"):
            await bot.send_message(
                event.chat.id,
                "✅ Бот подключён к чату.\n"
                "Для проверки напишите: /chatid\n"
                "Для каталога: /post_catalog"
            )
    except Exception as e:
        logging.exception("MY_CHAT_MEMBER SEND ERROR: %s", e)

# ====== ЛОГ ВСЕХ СООБЩЕНИЙ ======
@dp.message()
async def debug_any_message(message: types.Message):
    logging.info(
        "ANY MESSAGE | chat_id=%s | chat_type=%s | title=%s | user_id=%s | text=%s",
        message.chat.id,
        message.chat.type,
        message.chat.title,
        message.from_user.id if message.from_user else None,
        message.text,
    )

# ====== ЗАПУСК ======
async def main():
    me = await bot.get_me()
    logging.info("BOT STARTED | id=%s | username=@%s | full_name=%s", me.id, me.username, me.full_name)

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(
        bot,
        allowed_updates=[
            "message",
            "edited_message",
            "callback_query",
            "my_chat_member",
            "chat_member",
        ],
    )

if __name__ == "__main__":
    asyncio.run(main())