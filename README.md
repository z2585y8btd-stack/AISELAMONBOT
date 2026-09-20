# AISELAMONBOT

بوت تيليجرام يرد باللهجة السعودية، بردود قصيرة ولطيفة وخفيفة دم 🥹🧡

## التشغيل

1. ثبّت الاعتمادات:

```bash
pip install -r requirements.txt
```

2. أضف الأسرار إلى بيئة التشغيل، ولا تضعها داخل الملفات أو GitHub:

```bash
export AISELAMONBOT_TOKEN="توكن البوت"
export OPENAI_API_KEY="مفتاح OpenAI"
```

`AISELAMONBOT_TOKEN` مطلوب. أما `OPENAI_API_KEY` فهو اختياري؛ بدونه يعمل البوت بردود محلية بسيطة.

3. شغّل البوت:

```bash
python bot.py
```

في GitHub Actions أو أي منصة استضافة، أضف السر باسم `AISELAMONBOT_TOKEN`، وأضف `OPENAI_API_KEY` إذا كنت تريد ردود الذكاء الاصطناعي.
