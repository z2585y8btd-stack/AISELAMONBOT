import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover
    AsyncOpenAI = None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("AISELAMONBOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ADMIN_ID = int(os.getenv("BOT_ADMIN_ID", "8561249287"))
USER_STORE_FILE = Path(os.getenv("USER_STORE_FILE", "bot_users.json"))
CHANNEL_URL = "https://t.me/+LIVzUK7_TxphNGZk"
CONTACT_ADMIN_CALLBACK = "contact_admin"

SYSTEM_PROMPT = """أنت مساعد تيليجرام سعودي لطيف وخفيف دم.

التزم دائمًا بهذه القواعد:
- أجب مباشرة ولا تسأل المستخدم أي سؤال.
- اجعل الرد قصيرًا وعلى قد السؤال، غالبًا جملة أو جملتين فقط.
- لا تكتب مقدمات أو شرحًا طويلًا ولا تكرر كلام المستخدم.
- استخدم اللهجة السعودية الطبيعية بدون مبالغة.
- أضف أحيانًا إيموجي لطيفًا مثل 🥹 🧡 🔥 😂، ولا تكثر منها.
- كن كوميديًا ولطيفًا، ويمكنك استخدام إيحاء خفيف ومرح غير فاضح وغير جنسي صريح.
- لا تستخدم محتوى جنسيًا صريحًا أو يستغل القاصنين أو يتضمن إكراهًا.
- لا تختم بسؤال مثل: هل تحتاج شيئًا آخر؟
- إذا كان الطلب غير واضح، أعطِ أفضل جواب مفيد بدل طرح سؤال.
"""

client: Optional[object] = None
if OPENAI_API_KEY and AsyncOpenAI:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)


def load_store() -> dict[str, Any]:
    default = {"next_person": 1, "users": {}, "admin_messages": {}}
    try:
        if USER_STORE_FILE.exists():
            data = json.loads(USER_STORE_FILE.read_text(encoding="utf-8"))
            default.update(data)
    except (OSError, json.JSONDecodeError):
        logger.exception("Could not load user store; starting with an empty store")
    return default


STORE = load_store()


def save_store() -> None:
    temporary = USER_STORE_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(STORE, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(USER_STORE_FILE)


def user_record(user_id: int, user: Any) -> dict[str, Any]:
    key = str(user_id)
    record = STORE["users"].get(key)
    if not record:
        person_number = int(STORE["next_person"])
        STORE["next_person"] = person_number + 1
        record = {
            "person_number": person_number,
            "name": f"شخص {person_number}",
            "user_id": user_id,
        }
        STORE["users"][key] = record
    record["username"] = user.username or ""
    record["first_name"] = user.first_name or ""
    save_store()
    return record


def display_name(record: dict[str, Any]) -> str:
    return record.get("name") or f"شخص {record['person_number']}"


def channel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📣 انضم الآن إلى القناة", url=CHANNEL_URL)],
            [InlineKeyboardButton("✉️ إرسال رسالة لصاحب البوت", callback_data=CONTACT_ADMIN_CALLBACK)],
        ]
    )


def is_channel_link_request(text: str) -> bool:
    normalized = text.strip().lower()
    link_words = ("رابط", "لينك", "link", "url", "join", "انضم", "دخول")
    channel_words = ("القناة", "قناه", "قناة", "channel")
    return CHANNEL_URL.lower() in normalized or (
        any(word in normalized for word in link_words)
        and any(word in normalized for word in channel_words)
    )


def fallback_reply(text: str) -> str:
    lowered = text.strip().lower()
    if any(word in lowered for word in ("هلا", "مرحبا", "السلام", "hello")):
        return "يا هلا والله 🧡 نورت!"
    if "شكرا" in lowered or "مشكور" in lowered:
        return "العفو يا بعدي 🥹"
    if "كيفك" in lowered or "شلونك" in lowered:
        return "بخير دامك بخير 🔥"
    return "تم يا بعدي، بس فعّل مفتاح الذكاء الاصطناعي عشان أعطيك رد أذكى 🧡"


async def send_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "حياك الله بالقناة 🧡\nاضغط الزر للدخول مباشرة:",
            reply_markup=channel_keyboard(),
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "يا هلا! نورت يا بعدي 🥹🧡\n\nتقدر تدخل القناة أو ترسل رسالة مباشرة لصاحب البوت:",
            reply_markup=channel_keyboard(),
        )


async def contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.from_user:
        return
    await query.answer()
    context.user_data["awaiting_admin_message"] = True
    await query.message.reply_text("اكتب رسالتك ال��ن، وبوصلها لصاحب البوت ويرد عليك 🧡")


async def deliver_to_admin(update: Update) -> bool:
    message = update.message
    if not message or not message.from_user or message.from_user.id == ADMIN_ID:
        return False
    record = user_record(message.from_user.id, message.from_user)
    header = await message.get_bot().send_message(
        chat_id=ADMIN_ID,
        text=(
            f"📩 رسالة جديدة من {display_name(record)}\n"
            f"🆔 ID: {message.from_user.id}\n"
            f"👤 username: @{message.from_user.username}"
            if message.from_user.username
            else f"📩 رسالة جديدة من {display_name(record)}\n🆔 ID: {message.from_user.id}"
        ),
    )
    STORE["admin_messages"][str(header.message_id)] = message.from_user.id
    try:
        copied = await message.copy(
            chat_id=ADMIN_ID,
            reply_to_message_id=header.message_id,
        )
        STORE["admin_messages"][str(copied.message_id)] = message.from_user.id
    except Exception:
        logger.exception("Could not copy user message to admin")
        await message.get_bot().send_message(
            chat_id=ADMIN_ID,
            text="تعذر نسخ ن��ع هذه الرسالة تلقائيًا؛ تواصل مع المستخدم عبر الـ ID أعلاه.",
            reply_to_message_id=header.message_id,
        )
    save_store()
    await message.reply_text("وصلت رسالتك لصاحب البوت ✅ إذا رد، يوصلك الرد هنا.")
    return True


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    message = update.message
    if not message or not message.from_user or message.from_user.id != ADMIN_ID:
        return False
    replied = message.reply_to_message
    if not replied:
        return False
    recipient_id = STORE["admin_messages"].get(str(replied.message_id))
    if not recipient_id:
        return False
    try:
        await message.copy(chat_id=int(recipient_id))
        await message.reply_text("تم إرسال الرد ✅")
    except Exception:
        logger.exception("Could not send admin reply")
        await message.reply_text("ما قدرت أرسل الرد؛ يمكن المستخدم حظر البوت.")
    return True


async def rename(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.from_user or update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("الاستخدام: /rename <رقم الشخص أو ID> <الاسم الجديد>")
        return
    identifier, new_name = context.args[0], " ".join(context.args[1:]).strip()
    record = None
    for candidate in STORE["users"].values():
        if str(candidate.get("person_number")) == identifier or str(candidate.get("user_id")) == identifier:
            record = candidate
            break
    if not record or not new_name:
        await update.message.reply_text("ما لقيت هذا الشخص. استخدم /people لمعرفة الأرقام.")
        return
    record["name"] = new_name[:64]
    save_store()
    await update.message.reply_text(f"تم تغيير الاسم إلى: {record['name']} ✅")


async def people(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.from_user or update.message.from_user.id != ADMIN_ID:
        return
    records = sorted(STORE["users"].values(), key=lambda item: item["person_number"])
    if not records:
        await update.message.reply_text("ما عندك متلقين مسجلين حتى الآن.")
        return
    lines = [f"{display_name(item)} — ID: {item['user_id']}" for item in records]
    await update.message.reply_text("📋 الأشخاص:\n" + "\n".join(lines))


async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.text or not message.from_user:
        return
    if await admin_reply(update, context):
        return
    if context.user_data.pop("awaiting_admin_message", False):
        if await deliver_to_admin(update):
            return
    text = message.text.strip()
    await message.chat.send_action(ChatAction.TYPING)
    if is_channel_link_request(text):
        await send_channel_link(update, context)
        return
    if not client:
        reply = fallback_reply(text)
    else:
        try:
            completion = await client.chat.completions.create(
                model=OPENAI_MODEL,
                temperature=0.85,
                max_tokens=120,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
            )
            reply = (completion.choices[0].message.content or "تم يا بعدي 🧡").strip()
        except Exception:
            logger.exception("AI request failed")
            reply = "صار تعليق بسيط، جرّب مرة ثانية يا بعدي 🥹"
    await message.reply_text(reply)


async def forward_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("awaiting_admin_message"):
        context.user_data.pop("awaiting_admin_message", None)
        await deliver_to_admin(update)
        return
    await admin_reply(update, context)


async def set_commands(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            BotCommand("start", "بدء البوت"),
            BotCommand("channel", "رابط القناة"),
            BotCommand("rename", "تغيير اسم شخص - للمالك فقط"),
            BotCommand("people", "عرض الأشخاص - للمالك فقط"),
        ]
    )


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("The AISELAMONBOT_TOKEN environment secret is not set")
    application = Application.builder().token(BOT_TOKEN).post_init(set_commands).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("channel", send_channel_link))
    application.add_handler(CommandHandler("rename", rename))
    application.add_handler(CommandHandler("people", people))
    application.add_handler(CallbackQueryHandler(contact_admin, pattern=f"^{CONTACT_ADMIN_CALLBACK}$"))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_any_message), group=0)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond), group=1)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
