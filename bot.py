import logging
import os
from typing import Optional

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

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
CHANNEL_URL = "https://t.me/+LIVzUK7_TxphNGZk"

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


def channel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("📣 انضم الآن إلى القناة", url=CHANNEL_URL)]]
    )


def is_channel_link_request(text: str) -> bool:
    normalized = text.strip().lower()
    link_words = ("رابط", "لينك", "link", "url", "join", "انضم", "دخول")
    channel_words = ("القناة", "قناه", "قناة", "channel")
    return (
        CHANNEL_URL.lower() in normalized
        or (any(word in normalized for word in link_words) and any(word in normalized for word in channel_words))
    )


def fallback_reply(text: str) -> str:
    """A small local response so the bot still works without an AI provider key."""
    lowered = text.strip().lower()
    if any(word in lowered for word in ("هلا", "مرحبا", "السلام", "hello")):
        return "يا هلا والله 🧡 نورت!"
    if "شكرا" in lowered or "مشكور" in lowered:
        return "العفو يا بعدي 🥹"
    if "كيفك" in lowered or "شلونك" in lowered:
        return "بخير دامك بخير 🔥"
    return "تم يا بعدي، بس فعّل مفتاح الذكاء الاصطناعي عشان أعطيك رد أذكى 🧡"


async def send_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "حياك الله بالقناة 🧡\nاضغط الزر للدخول مباشرة:",
        reply_markup=channel_keyboard(),
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "يا هلا! نورت يا بعدي 🥹🧡\n\nتقدر تدخل القناة من الزر تحت:",
        reply_markup=channel_keyboard(),
    )


async def set_commands(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            BotCommand("start", "بدء البوت والدخول للقناة"),
            BotCommand("channel", "رابط القناة لمدة 30 يوم"),
        ]
    )


async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    await update.message.chat.send_action(ChatAction.TYPING)

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

    await update.message.reply_text(reply)


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("The AISELAMONBOT_TOKEN environment secret is not set")

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(set_commands)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("channel", send_channel_link))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
