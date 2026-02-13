import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.methods import DeleteWebhook

from mistralai import Mistral
from dotenv import load_dotenv

# ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ

load_dotenv()

TOKEN = os.getenv(“TELEGRAM_BOT_TOKEN”)
MISTRAL_KEY = os.getenv(“MISTRAL_API_KEY”)

# ИНИЦИАЛИЗАЦИЯ

logging.basicConfig(level=logging.INFO)
bot = Bot(TOKEN)
dp = Dispatcher()
mistral_client = Mistral(api_key=MISTRAL_KEY)

# КОНСТАНТЫ

DATA_FILE = “tracker_data.json”
IMAGES = {
“morning”: “https://ibb.co/JWSjnwyF
”,  # ЗАМЕНИ НА РЕАЛЬНЫЕ ССЫЛКИ
“turnik”: “https://ibb.co/wNJJk0B6”,
“stats”: “https://ibb.co/JWSjnwyF
https://ibb.co/wNJJk0B6
https://ibb.co/zTqnRSNm”,
“study”: “https://ibb.co/FbhTWYxs”,
“victory”: “https://ibb.co/j9fXftGX”,
}

# ФУНКЦИЯ ЗАГРУЗКИ ДАННЫХ

def load_data():
if Path(DATA_FILE).exists():
with open(DATA_FILE, “r”, encoding=“utf-8”) as f:
return json.load(f)
return {}

# ФУНКЦИЯ СОХРАНЕНИЯ ДАННЫХ

def save_data(data):
with open(DATA_FILE, “w”, encoding=“utf-8”) as f:
json.dump(data, f, ensure_ascii=False, indent=2)

# ФУНКЦИЯ СОЗДАНИЯ ПУСТОЙ ЗАПИСИ ДНЯ

def create_day_entry():
return {
“woke_up_630”: False,
“turnik_sets”: 0,
“homework_done”: False,
“sleep_9pm”: False,
“extra_exercises”: False,
“notes”: “”,
“ai_feedback”: “”
}

# ФУНКЦИЯ ПОЛУЧЕНИЯ СТАТИСТИКИ

def get_statistics(user_id):
data = load_data()
user_data = data.get(str(user_id), {})

```
if not user_data.get("reports"):
    return None

reports = user_data.get("reports", {})
total_days = len(reports)

woke_up_count = sum(1 for r in reports.values() if r.get("woke_up_630"))
turnik_count = sum(1 for r in reports.values() if r.get("turnik_sets", 0) > 0)
homework_count = sum(1 for r in reports.values() if r.get("homework_done"))
sleep_count = sum(1 for r in reports.values() if r.get("sleep_9pm"))

return {
    "total_days": total_days,
    "woke_up_630": woke_up_count,
    "turnik_days": turnik_count,
    "homework_days": homework_count,
    "sleep_days": sleep_count,
    "woke_up_percent": int((woke_up_count / total_days * 100) if total_days > 0 else 0),
    "homework_percent": int((homework_count / total_days * 100) if total_days > 0 else 0),
}
```

# ФУНКЦИЯ КРАСИВОГО ВИЗУАЛА СТАТИСТИКИ

def create_stats_text(user_id, stats):
if not stats:
return “📊 У тебя ещё нет данных. Начни с /report!”

```
text = f"""
```

╔══════════════════════════════════════╗
║     📊 ТВОЯ СТАТИСТИКА (15 ДНЕЙ)     ║
╚══════════════════════════════════════╝

🔥 ВСЕГО ДНЕЙ: {stats[‘total_days’]} / 15

📍 ВСТАЛ В 6:30
✅ {stats[‘woke_up_630’]} дней
📈 {stats[‘woke_up_percent’]}%
{‘🟢 ОТЛИЧНО!’ if stats[‘woke_up_percent’] >= 80 else ‘🟡 Можно лучше’ if stats[‘woke_up_percent’] >= 50 else ‘🔴 Нужна работа’}

🏋️ ТУРНИК
✅ {stats[‘turnik_days’]} дней
📈 {int((stats[‘turnik_days’] / stats[‘total_days’] * 100) if stats[‘total_days’] > 0 else 0)}%

📚 ДОМАШКА
✅ {stats[‘homework_days’]} дней
📈 {stats[‘homework_percent’]}%
{‘🟢 СУПЕР!’ if stats[‘homework_percent’] >= 90 else ‘🟡 Хорошо’ if stats[‘homework_percent’] >= 70 else ‘🔴 Работай!’}

😴 СОН В 9 PM
✅ {stats[‘sleep_days’]} дней
📈 {int((stats[‘sleep_days’] / stats[‘total_days’] * 100) if stats[‘total_days’] > 0 else 0)}%

╠══════════════════════════════════════╣
║ 💪 МОЛОДЕЦ! ДЕРЖИ КУРС! 💪          ║
╚══════════════════════════════════════╝
“””
return text

# ФУНКЦИЯ ИИ АНАЛИЗА (MISTRAL)

async def get_ai_feedback(user_id, report_data, stats):
“”“Mistral анализирует прогресс и даёт мотивацию”””

```
context = f"""
```

Ты - личный AI тренер для подростка 14 лет по имени Артём.
Артём начал челлендж на 15 дней: вставать в 6:30, ходить на турник, делать домашку, спать в 9 PM.

СЕГОДНЯШНИЙ ОТЧЁТ АРТЁМА:

- Встал в 6:30: {‘ДА’ if report_data.get(‘woke_up_630’) else ‘НЕТ’}
- Турник подходов: {report_data.get(‘turnik_sets’, 0)}
- Домашка: {‘СДЕЛАНА’ if report_data.get(‘homework_done’) else ‘НЕ СДЕЛАНА’}
- Спал в 9 PM: {‘ДА’ if report_data.get(‘sleep_9pm’) else ‘НЕТ’}
- Доп упражнения: {‘ДА’ if report_data.get(‘extra_exercises’) else ‘НЕТ’}
- Заметки: {report_data.get(‘notes’, ‘нет’)}

СТАТИСТИКА ПРОГРЕССА:

- Дней в челлендже: {stats[‘total_days’]} / 15
- Встал в 6:30: {stats[‘woke_up_percent’]}%
- Домашка: {stats[‘homework_percent’]}%
- Дни на турнике: {stats[‘turnik_days’]} дней

ТВОЯ ЗАДАЧА:

1. Похвали Артёма за то, что он ДЕЛАЕТ
1. Если что-то не получилось - дай КОНКРЕТНЫЙ совет, не ругай
1. Дай МОТИВАЦИЮ на завтра (максимум 3-4 предложения)
1. Если прогресс идёт - скажи “ТЫ НА ПРАВИЛЬНОМ ПУТИ”
1. Напиши НА РУССКОМ, эмоционально, как тренер, как друг

ОТВЕТ ДОЛЖЕН БЫТЬ:

- Коротким (3-4 абзаца)
- Мотивирующим
- С конкретными советами
- БЕЗ формальности - как тренер говорит
  “””
  
  try:
  response = mistral_client.chat.complete(
  model=“mistral-large-latest”,
  messages=[
  {
  “role”: “system”,
  “content”: context
  },
  {
  “role”: “user”,
  “content”: “Дай мне мотивационный фидбэк на сегодняшний день”
  }
  ],
  temperature=0.7,
  max_tokens=300
  )
  return response.choices[0].message.content
  except Exception as e:
  logging.error(f”Mistral error: {e}”)
  return “💪 Ты молодец! Продолжай в том же духе!”

# ОБРАБОТЧИК /start

@dp.message(Command(“start”))
async def cmd_start(message: Message):
user_id = message.from_user.id
data = load_data()

```
if str(user_id) not in data:
    data[str(user_id)] = {"reports": {}, "start_date": datetime.now().isoformat()}
    save_data(data)

text = """
```

╔════════════════════════════════════════╗
║  🏋️ ДОБРО ПОЖАЛОВАТЬ В ARTEMTRACKER  ║
╚════════════════════════════════════════╝

Это твой личный ИИ тренер.

📋 КОМАНДЫ:
/report - Дневной отчёт (встал в 6:30? турник? домашка? сон?)
/stats - Статистика за 15 дней
/reset - Начать заново

🎯 ЧЕЛЛЕНДЖ:
15 дней дисциплины:
✅ Встаёшь в 6:30
✅ Идёшь на турник
✅ Делаешь домашку БЕЗ тик-тока
✅ Спишь в 9 PM

Давай, начнём! Напиши /report
“””

```
keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📋 Начать отчёт", callback_data="report_start")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats_show")]
    ]
)

await message.answer_photo(
    photo=IMAGES["morning"],
    caption=text,
    reply_markup=keyboard,
    parse_mode="HTML"
)
```

# ОБРАБОТЧИК /report

@dp.message(Command(“report”))
async def cmd_report(message: Message):
user_id = str(message.from_user.id)
today = datetime.now().strftime(”%Y-%m-%d”)

```
text = """
```

📋 ДНЕВНОЙ ОТЧЁТ

Отвечай на вопросы:

1️⃣ Встал в 6:30? (напиши: да или нет)
2️⃣ Сколько подходов на турнике? (напиши число, например: 3)
3️⃣ Домашка сделана? (напиши: да или нет)
4️⃣ Спал в 9 PM? (напиши: да или нет)
5️⃣ Доп упражнения? (напиши: да или нет)
6️⃣ Заметки (напиши что угодно или “нет”)

Пример ответа:
да
3
да
нет
нет
Сложновато было с домашкой
“””

```
await message.answer(text)

# Сохраняем состояние что ждём отчёт
data = load_data()
if user_id not in data:
    data[user_id] = {"reports": {}}
data[user_id]["awaiting_report"] = True
save_data(data)
```

# ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ (ОБРАБОТКА ОТЧЁТОВ)

@dp.message(F.text)
async def process_report(message: Message):
user_id = str(message.from_user.id)
data = load_data()

```
if not data.get(user_id, {}).get("awaiting_report"):
    # Если не ожидаем отчёт - просто ответим
    await message.answer("Используй /report для дневного отчёта или /stats для статистики")
    return

lines = message.text.strip().split("\n")

if len(lines) < 6:
    await message.answer("❌ Не хватает ответов! Напиши /report и заполни все 6 вопросов")
    return

# ПАРСИМ ОТВЕТЫ
try:
    woke_up = lines[0].lower() in ["да", "yes", "y"]
    turnik_sets = int(lines[1]) if lines[1].isdigit() else 0
    homework = lines[2].lower() in ["да", "yes", "y"]
    sleep = lines[3].lower() in ["да", "yes", "y"]
    extra = lines[4].lower() in ["да", "yes", "y"]
    notes = lines[5] if len(lines) > 5 else ""
except:
    await message.answer("❌ Ошибка парсинга! Проверь формат")
    return

# СОХРАНЯЕМ ОТЧЁТ
today = datetime.now().strftime("%Y-%m-%d")
if "reports" not in data[user_id]:
    data[user_id]["reports"] = {}

data[user_id]["reports"][today] = {
    "woke_up_630": woke_up,
    "turnik_sets": turnik_sets,
    "homework_done": homework,
    "sleep_9pm": sleep,
    "extra_exercises": extra,
    "notes": notes,
    "timestamp": datetime.now().isoformat()
}

data[user_id]["awaiting_report"] = False
save_data(data)

# ПОЛУЧАЕМ СТАТИСТИКУ
stats = get_statistics(message.from_user.id)

# ПОЛУЧАЕМ ИИ ФИДБЭК ОТ MISTRAL
ai_feedback = await get_ai_feedback(
    message.from_user.id,
    data[user_id]["reports"][today],
    stats
)

# ВЫБИРАЕМ ПРАВИЛЬНОЕ ИЗОБРАЖЕНИЕ
if woke_up and turnik_sets > 0 and homework:
    image = IMAGES["victory"]
elif woke_up and turnik_sets > 0:
    image = IMAGES["turnik"]
else:
    image = IMAGES["morning"]

# ФОРМИРУЕМ КРАСИВЫЙ ОТВЕТ
emoji_woke = "✅" if woke_up else "❌"
emoji_turnik = "✅" if turnik_sets > 0 else "❌"
emoji_hw = "✅" if homework else "❌"
emoji_sleep = "✅" if sleep else "❌"

report_text = f"""
```

╔════════════════════════════════════════╗
║          ОТЧЁТ НА {datetime.now().strftime(”%d.%m.%Y”)}            ║
╚════════════════════════════════════════╝

{emoji_woke} Встал в 6:30
{emoji_turnik} Турник: {turnik_sets} подходов
{emoji_hw} Домашка
{emoji_sleep} Сон в 9 PM
{(‘✅’ if extra else ‘❌’)} Доп упражнения

💬 Заметки: {notes if notes != ‘нет’ else ‘нет’}

╠════════════════════════════════════════╣
║         🤖 ИИ ФИДБЭК ОТ ТРЕНЕРА        ║
╚════════════════════════════════════════╝

{ai_feedback}

✨ Статистика обновлена!
Напиши /stats для полной статистики
“””

```
await message.answer_photo(
    photo=image,
    caption=report_text,
    parse_mode="HTML"
)
```

# ОБРАБОТЧИК /stats

@dp.message(Command(“stats”))
async def cmd_stats(message: Message):
user_id = message.from_user.id
stats = get_statistics(user_id)

```
if not stats:
    await message.answer("📊 Ещё нет данных! Начни с /report")
    return

text = create_stats_text(user_id, stats)

await message.answer_photo(
    photo=IMAGES["stats"],
    caption=text,
    parse_mode="HTML"
)
```

# ОБРАБОТЧИК /reset

@dp.message(Command(“reset”))
async def cmd_reset(message: Message):
user_id = str(message.from_user.id)
data = load_data()

```
if user_id in data:
    data[user_id] = {"reports": {}, "start_date": datetime.now().isoformat()}
    save_data(data)

await message.answer("🔄 Данные очищены! Челлендж начинается заново.\nНапиши /report")
```

# ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА

async def main():
await bot(DeleteWebhook(drop_pending_updates=True))
await dp.start_polling(bot)

if **name** == “**main**”:
asyncio.run(main())
