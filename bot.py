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

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден. Добавь переменную окружения BOT_TOKEN.")

BOT_USERNAME = "kadima_cafe_bot"

ADMIN_IDS = {6013591658, 331273289}

WEBAPP_URL = "https://tahirovdd-lang.github.io/bakery-chokoart/?v=1"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML"),
)
dp = Dispatcher()

_last_start: dict[int, float] = {}


def allow_start(user_id: int, ttl: float = 2.0) -> bool:
    now = time.time()
    prev = _last_start.get(user_id, 0.0)
    if now - prev < ttl:
        return False
    _last_start[user_id] = now
    return True


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


@dp.message(CommandStart())
async def start(message: types.Message):
    if not message.from_user:
        return

    logging.info(
        "START | chat_id=%s | chat_type=%s | user_id=%s | text=%s",
        message.chat.id,
        message.chat.type,
        message.from_user.id,
        message.text,
    )

    if not allow_start(message.from_user.id):
        return

    await message.answer(welcome_text(), reply_markup=kb_webapp_reply())


@dp.message(Command("startapp"))
async def startapp(message: types.Message):
    if not message.from_user:
        return

    logging.info(
        "STARTAPP | chat_id=%s | chat_type=%s | user_id=%s | text=%s",
        message.chat.id,
        message.chat.type,
        message.from_user.id,
        message.text,
    )

    if not allow_start(message.from_user.id):
        return

    await message.answer(welcome_text(), reply_markup=kb_webapp_reply())


@dp.message(Command("chatid"))
async def chat_id_info(message: types.Message):
    if not message.from_user:
        return

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


@dp.message(Command("testgroup"))
async def testgroup(message: types.Message):
    if not message.from_user:
        return

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


@dp.message(Command("post_catalog"))
async def post_catalog(message: types.Message):
    if not message.from_user:
        return

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
            pass


def fmt_sum(n: int) -> str:
    try:
        n = int(n)
    except Exception:
        n = 0
    return f"{n:,}".replace(",", " ")


def tg_label(u: types.User | None) -> str:
    if not u:
        return "—"
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

    return lines, order_dict


def validate_order(data: dict, lines: list[str]) -> str | None:
    total = safe_int(data.get("total"), 0)
    payment = clean_str(data.get("payment"))
    order_type = clean_str(data.get("type"))
    address = clean_str(data.get("address"))
    order_id = clean_str(data.get("order_id"))

    if not lines:
        return "❌ Корзина пустая. Добавьте товары в заказ."

    if total <= 0:
        return "❌ Сумма заказа не указана. Проверьте корзину."

    if not payment:
        return "❌ Выберите способ оплаты."

    if not order_type:
        return "❌ Выберите тип заказа: доставка или самовывоз."

    if order_type == "delivery" and not address:
        return "❌ Заполните адрес доставки."

    if not order_id:
        return "❌ Не удалось создать номер заказа. Попробуйте оформить заказ ещё раз."

    return None


@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    logging.info(
        "WEB_APP_DATA | chat_id=%s | user_id=%s",
        message.chat.id,
        message.from_user.id if message.from_user else None,
    )

    raw = message.web_app_data.data

    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        data = {}

    lines, _ = build_order_lines(data)

    error = validate_order(data, lines)
    if error:
        await message.answer(error)
        return

    total_str = clean_str(data.get("total")) or "0"
    payment = clean_str(data.get("payment")) or "—"
    order_type = clean_str(data.get("type")) or "—"
    address = clean_str(data.get("address")) or "—"
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


async def main():
    me = await bot.get_me()
    logging.info(
        "BOT STARTED | id=%s | username=@%s | full_name=%s",
        me.id,
        me.username,
        me.full_name
    )

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
