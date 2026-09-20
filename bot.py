import logging
import os
import random
import re
from datetime import datetime

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("AISELAMONBOT_TOKEN")


# ردود محلية بالكامل: لا تحتاج إنترنت أو مزود ذكاء اصطناعي.
RESPONSES = {
    "greeting": [
        "هلا والله 🧡!",
        "أهلين 🧡",
        "مرحبا مليون 🥹",
    ],
    "thanks": [
        "العفو 🧡",
        "تستاهل أكثر 😄",
        "يا حلوك!",
    ],
    "how_are_you": [
        "تمام 😎",
        "رايق ومروق 🔥",
        "بخير دامك بخير 🧡",
    ],
    "identity": [
        "أنا بوتك المحلي؛ أفهم الكلام الشائع وأرد بدون لف ودوران 🌪️",
        "أنا مساعدك السعودي، شغلي كله محلي وسريع 🧡",
    ],
    "help": [
        "أقدر أسولف معك، أقول نكتة، أعطيك دفعة حماس، وأرد على الكلام اليومي 🔥",
    ],
    "joke": [
        "واحد بخيل دخل مطعم… طلب المنيو وقال: تكفون خلّوه عندي، النظر مجاني 😂",
        "مرة جوال زعل من الشاحن وقال له: كل ما شفتني شبكتني! 😄",
        "واحد سأل الكمبيوتر: ليه ساكت؟ قال: أفكر بالموضوع من زمان 🤖😂",
    ],
    "encouragement": [
        "أنت قدّها يا بطل، خذها خطوة خطوة والباقي يهون 💪",
        "لا تشيل هم، كثير من الأشياء الصعبة تصير سهلة مع أول خطوة 🧡",
        "شد حيلك، تعب اليوم هو سالفة نجاح بكرة بإذن الله 🔥",
    ],
    "sad": [
        "الله يشرح صدرك ويفرج همّك. خذها بهدوء، يومك بيتعدل بإذن ال��ه 🧡",
        "أفهم شعورك يا بعدي، لا تضغط على نفسك؛ ارتح شوي وبتزين الأمور.",
        "الله يبدّل ضيقتك راحة وفرح، أنت أقوى مما تتخيل 🤍",
    ],
    "compliment": [
        "يا زين ذوقك، كلامك يرفع المعنويات والله 🥹",
        "شهادتك أعتز فيها يا بعدي، كفو عليك 🧡",
    ],
    "goodbye": [
        "باي يا بعدي 👋",
        "سلام! في أمان الله 🧡",
    ],
}


def normalize(text: str) -> str:
    """توحيد بسيط للنص حتى يتعرف البوت على اختلافات الكتابة العربية."""
    text = text.strip().lower()
    text = re.sub(r"[ًٌٍَُِّْـ]", "", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي").replace("ة", "ه")
    return re.sub(r"\s+", " ", text)


def has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def fallback_reply(text: str) -> str:
    """ينشئ ردًا محليًا ذكيًا ومتنوّعًا باللهجة السعودية دون أي خدمة خارجية."""
    normalized = normalize(text)

    if not normalized:
        return "اكتب اللي بخاطرك يا بعدي، وأنا حاضر 🧡"
    if has_any(normalized, ("هلا", "مرحبا", "يا هلا", "السلام عليكم", "اهلين", "hello", "hi")):
        category = "greeting"
    elif has_any(normalized, ("شكرا", "مشكور", "يعطيك العافيه", "تسلم", "ممتن")):
        category = "thanks"
    elif has_any(normalized, ("كيفك", "شلونك", "وش اخبارك", "كيف حالك", "علومك")):
        category = "how_are_you"
    elif has_any(normalized, ("من انت", "وش انت", "وش اسمك", "عرفني عليك")):
        category = "identity"
    elif has_any(normalized, ("ساعدني", "وش تقدر", "كيف استخدمك", "ماذا تفعل", "وش تسوي")):
        category = "help"
    elif has_any(normalized, ("نكت", "اضحكني", "ضحكني", "مزحه", "نكتة")):
        category = "joke"
    elif has_any(normalized, ("حزين", "حزينه", "زعلان", "زعلانه", "متضايق", "مضايق", "طفشان")):
        category = "sad"
    elif has_any(normalized, ("احبك", "كفو", "مبدع", "رهيب", "حلو ردك", "ممتاز")):
        category = "compliment"
    elif has_any(normalized, ("باي", "مع السلامه", "اشوفك", "تصبح على خير")):
        category = "goodbye"
    elif has_any(normalized, ("تعبت", "ما اقدر", "فاشل", "خايف", "خايفه", "محتار")):
        category = "encouragement"
    elif has_any(normalized, ("الوقت", "كم الساعه", "الساعه كم")):
        return f"الساعة الآن تقريبًا {datetime.now().strftime('%I:%M')} بتوقيت الجهاز ⏰"
    elif has_any(normalized, ("التاريخ", "اي يوم", "اليوم كم")):
        return f"اليوم {datetime.now().strftime('%Y-%m-%d')} حسب توقيت الجهاز 📅"
    elif has_any(normalized, ("الجو", "الطقس", "درجه الحراره")):
        return "ما عندي بيانات طقس مباشرة، لكن شيّك تطبيق الطقس عشان تعرف الوضع بدقة 🌤️"
    else:
        replies = (
            "وصلت فكرتك يا بعدي؛ خلّنا نمسكها وحدة وحدة وبهدوء 🧡",
            "كلامك على العين والرأس. بعطيك الزبدة: خلك واضح مع نفسك وخذ أقرب خطوة مفيدة.",
            "تم يا كفو، فهمت عليك. الأمور غالبًا تنحل بالتدرّج، لا تستعجل على نفسك 🔥",
            "أبشر، كلامك مفهوم. خلّها بسيطة ولا تعقّدها، خطوة صغيرة اليوم تفرق كثير.",
        )
        return random.choice(replies)

    return random.choice(RESPONSES[category])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("يا هلا! اكتب اللي تبيه وأنا أجاوبك على السريع 🥹🧡")


async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    await update.message.chat.send_action(ChatAction.TYPING)
    await update.message.reply_text(fallback_reply(text))


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("The AISELAMONBOT_TOKEN environment secret is not set")

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
