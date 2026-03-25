import asyncio
import os
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, ContentType
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.utils.deep_linking import create_start_link, decode_payload
from supabase import create_client, Client
from aiocryptopay import AioCryptoPay
import time
from keyboards_app import get_main_menu_with_app
import json
import re
from aiogram.filters import Command, CommandObject
from aiogram import BaseMiddleware
from cachetools import TTLCache
from typing import Callable, Dict, Any, Awaitable
from PIL import Image
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import Message
import time
import os
from dotenv import load_dotenv

load_dotenv()

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class KeepAliveServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Virtus Fit Bot is ALIVE!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080)) # Render сам выдаст нужный порт
    server = HTTPServer(('0.0.0.0', port), KeepAliveServer)
    server.serve_forever()

# 3. Запускаем сервер параллельно с твоим ботом
threading.Thread(target=run_web_server, daemon=True).start()

# --- БЕЗПЕЧНИЙ ІМПОРТ CRYPTOBOT ---
try:
    from aiocryptopay import AioCryptoPay
    CryptoInstance = AioCryptoPay
except ImportError:
    try:
        from aiocryptopay import CryptoPay
        CryptoInstance = CryptoPay
    except ImportError:
        import aiocryptopay
        CryptoInstance = getattr(aiocryptopay, 'AioCryptoPay', getattr(aiocryptopay, 'CryptoPay', None))

if not CryptoInstance:
    print("❌ Помилка: Бібліотека aiocryptopay не знайдена!")

# Создаем пустую переменную, запустим крипту позже!
crypto = None

async def get_user_language(user_id: int) -> str:
    try:
        res = supabase.table("users").select("language").eq("user_id", user_id).execute()
        if res.data and len(res.data) > 0:
            return res.data[0].get("language", "ru")
    except Exception as e:
        print(f"Помилка отримання мови: {e}")
    return "ru"

TRANSLATIONS = {
    "ru": {
        "welcome": "👊 Привет! 👋😊 Добро пожаловать в Virtus — твоего цифрового тренера.\n\n❌ Никаких шаблонных программ — только индивидуальный подход!\n🤖 Наша нейросеть создает идеальный план. Тут ты можешь консультироваться с тренером, психологом и врачом.\n🍔 Тут ты сможешь узнать сколько каллорий в твоем любимом бургере прямо по фото!\n\n🎁 Подпишись на каналы спонсоров и получи 10 бесплатных генераций!",
        "check_subs_btn": "✅ ПРОВЕРИТЬ ПОДПИСКИ",
        "subs_checked": "🎉 Доступ открыт! Как мне к Вам обращаться?",
        "ask_name": "⚠️ Имя не может содержать цифры. Введите ваше настоящее имя:",
        "valid_name": "Как мне к Вам обращаться?",
        "ask_age": "Сколько вам полных лет? (Введите число)",
        "invalid_age": "⚠️ Пожалуйста, введите возраст цифрами (например: 25):",
        "ask_weight": "Какой ваш вес (кг)? (например: 75.5)",
        "invalid_weight": "⚠️ Введите вес числом (например: 80 или 75.5):",
        "ask_goal": "Какая ваша главная цель?",
        "profile_complete": "✅ Профиль настроен!",
        "referral_notification": "🎁 Твой друг зарегистрировался! +3 попытки.",
        "sub_error": "❌ Ошибка! Подпишитесь на все каналы.",
        "subs_instruction": "Нажмите кнопку ниже, чтобы подписаться. После этого вернитесь и нажмите Проверить.",
        "subs_redirect": "➡️ ПЕРЕЙТИ В КАНАЛ",
        "subs_wait": "⏳ Подождите еще {sec} сек. Проверка идет...",
        "subs_not_all": "❌ Вы открыли не все ссылки!",
        "web_app_btn": "📊 Мой Прогресс (Web App)",
        "food_analysis": "🔬 Анализ калорийности еды",
        "nutrition": "🍎 Питание",
        "balance": "💳 Баланс",
        "ai_chat": "💬 Чат с AI",
        "account": "👤 Аккаунт",
        "support": "🆘 Поддержка",
        "referral": "🔗 Рефералка",
        "subscription": "💎 Подписка",
        "profile_title": "👤 **Профиль**",
        "profile_not_found": "❌ Профиль не найден. Нажмите /start",
        "name_label": "Имя: ",
        "age_label": "Возраст: ",
        "weight_label": "Вес: ",
        "goal_label": "Цель: ",
        "balance_label": "💳 Баланс: ",
        "attempts": " спрос.",
        "your_balance": "💰 Ваш баланс: ",
        "payment_success": "🎉 Оплата прошла успешно! Вам начислено 100 запросов. Ваш текущий баланс: ",
        "subscription_title": "Месячная подписка Virtus Fit",
        "subscription_desc": "Безлимитные генерации и анализ еды на 30 дней",
        "subscription_": "Подписка",
        "stars_label": "⭐️ Оплатить Stars (250 ⭐)",
        "crypto_label": "₿ Оплатить Криптой",
        "bank_payment":" 💳 Оплата картой (UAH/RUB/USD)",
        "payment_label": "Выберите удобный способ пополнения баланса (доступ к ИИ на месяц):",
        "select_role": "Выберите режим работы ИИ ассистента:",
        "role_coach": "🏋️ Тренер",
        "role_psy": "🧠 Психолог",
        "role_doc": "🏥 Врач-консультант",
        "role_changed": "✅ Режим изменен на: ",
        "ask_question": "Теперь пишите вопрос или шлите голос.",
        "thinking": "⏳ Думаю",
        "insufficient_balance": "❌ Недостаточно средств!",
        "analyzing": "🔍 Анализирую фото и описание...",
        "ai_error": "⚠️ Ошибка ИИ: ",
        "ask_bug": "🪲 Опишите проблему одним сообщением:",
        "bug_sent": "✅ Отправлено разработчику!",
        "bug_notification": "🚨 БАГ от ",
        "referral_title": "🎁 Реферальная программа",
        "referral_desc": "Приглашай друзей и получай +3 генерации за каждого, кто пройдет регистрацию!\n\n",
        "referral_count": "👥 Приглашено друзей: `",
        "referral_link": "`\n🔗 Твоя ссылка:\n`",
        "channel_fitness": "🔥 Фитнес Хаб",
        "channel_health": "🍏 Здоровье",
        "prompt_nutrition": "📸 Пришли мне фото своего блюда и, если нужно, добавь описание текстом (например, состав или вес). Я посчитаю калории!",
        "prompt_workouts": "Составь подробный план тренировок на неделю",
        "prompt_diet": "Составь подробный рацион питания на день",
        "dietitian_prompt": "Ты профессиональный диетолог. Проанализируй фото еды с учетом текста пользователя. Определи блюдо, вес, ккал и БЖУ. Дай совет, подходит ли это под цель пользователя.",
        "user_context": "Юзер: ",
        "years_old": " лет, ",
        "kg": "кг, цель: ",
        "user_text": "Текст от пользователя: ",
        "input_placeholder": "Можешь спросить тут что угодно...",
    },
    "en": {
        "welcome": "👊 Hello! 👋😊 Welcome to Virtus — your digital coach.\n\n❌ No template programs — only an individual approach!\n🤖 Our neural network creates the perfect plan. Here you can consult with a coach, psychologist, and doctor.\n🍔 Here you can find out how many calories are in your favorite burger right from the photo!\n\n🎁 Subscribe to sponsor channels and get 10 free generations!",
        "check_subs_btn": "✅ CHECK SUBSCRIPTIONS",
        "subs_checked": "🎉 Access granted! What's your name?",
        "ask_name": "⚠️ Name cannot contain numbers. Please enter your real name:",
        "valid_name": "What's your name?",
        "ask_age": "How old are you? (Enter a number)",
        "invalid_age": "⚠️ Please enter your age as a number (e.g., 25):",
        "ask_weight": "What's your weight (kg)? (e.g., 75.5)",
        "invalid_weight": "⚠️ Enter weight as a number (e.g., 80 or 75.5):",
        "ask_goal": "What is your main goal?",
        "profile_complete": "✅ Profile set up!",
        "referral_notification": "🎁 Your friend registered! +3 attempts.",
        "sub_error": "❌ Error! Subscribe to all channels.",
        "subs_instruction": "Click the button below to subscribe. Then return and click Check.",
        "subs_redirect": "➡️ GO TO CHANNEL",
        "subs_wait": "⏳ Wait another {sec} sec. Checking...",
        "subs_not_all": "❌ You haven't opened all links!",
        "web_app_btn": "📊 My Progress (Web App)",
        "food_analysis": "🔬 Food Calorie Analysis",
        "nutrition": "🍎 Nutrition",
        "balance": "💳 Balance",
        "ai_chat": "💬 Chat with AI",
        "account": "👤 Account",
        "support": "🆘 Support",
        "referral": "🔗 Referral",
        "subscription": "💎 Subscription",
        "profile_title": "👤 **Profile**",
        "profile_not_found": "❌ Profile not found. Press /start",
        "name_label": "Name: ",
        "age_label": "Age: ",
        "weight_label": "Weight: ",
        "goal_label": "Goal: ",
        "balance_label": "💳 Balance: ",
        "attempts": " attempts",
        "your_balance": "💰 Your balance: ",
        "payment_success": "🎉 Payment successful! Unlimited requests credited.",
        "subscription_title": "Virtus Fit Monthly Subscription",
        "subscription_desc": "Unlimited generations and food analysis for 30 days",
        "subscription_": "Subscription",
        "stars_label": "⭐️ Pay with Stars (250 ⭐)",
        "crypto_label": "₿ Pay with Crypto",
        "bank_payment":" 💳 Card Payment (UAH/RUB/USD)",
        "payment_label": "Select a convenient top-up method (1-month AI access):",
        "select_role": "Choose AI assistant mode:",
        "role_coach": "🏋️ Coach",
        "role_psy": "🧠 Psychologist",
        "role_doc": "🏥 Medical Consultant",
        "role_changed": "✅ Mode changed to: ",
        "ask_question": "Now write your question or send voice.",
        "thinking": "⏳ Thinking",
        "insufficient_balance": "❌ Insufficient balance!",
        "analyzing": "🔍 Analyzing photo and description...",
        "ai_error": "⚠️ AI Error: ",
        "ask_bug": "🪲 Describe the problem in one message:",
        "bug_sent": "✅ Sent to developer!",
        "bug_notification": "🚨 BUG from ",
        "referral_title": "🎁 Referral Program",
        "referral_desc": "Invite friends and earn +3 attempts for each person who completes registration!\n\n",
        "referral_count": "👥 Friends invited: `",
        "referral_link": "`\n🔗 Your link:\n`",
        "channel_fitness": "🔥 Fitness Hub",
        "channel_health": "🍏 Health",
        "prompt_nutrition": "📸 Send me a photo of your meal and, if needed, add a text description (e.g., ingredients or weight). I'll calculate the calories!",
        "prompt_workouts": "Create a detailed workout plan for the week",
        "prompt_diet": "Create a detailed nutrition plan for the day",
        "dietitian_prompt": "You are a professional nutritionist. Analyze the food photo considering the user's text. Determine the dish, weight, calories, and macros. Give advice on whether it fits the user's goal.",
        "user_context": "User: ",
        "years_old": " years old, ",
        "kg": "kg, goal: ",
        "user_text": "User message: ",
        "input_placeholder": "You can ask anything here...",
    },
    "ua": {
        "welcome": "👊 Привіт! 👋😊 Ласкаво просимо до Virtus — твого цифрового тренера.\n\n❌ Без шаблонних програм — лише індивідуальний підхід!\n🤖 Наша нейромережа створює ідеальний план. Тут ти можеш консультуватися з тренером, психологом і лікарем.\n🍔 Тут ти зможеш дізнатися скільки калорій у твоєму улюбленому бургері прямо по фото!\n\n🎁 Підпишись на канали спонсорів і отримай 10 безкоштовних генерацій!",
        "check_subs_btn": "✅ ПЕРЕВІРИТИ ПІДПИСКИ",
        "subs_checked": "🎉 Доступ відкритий! Як мені тебе називати?",
        "ask_name": "⚠️ Ім'я не може містити цифри. Введи своє справжнє ім'я:",
        "valid_name": "Як мені тебе називати?",
        "ask_age": "Скільки тобі років? (Введи число)",
        "invalid_age": "⚠️ Будь ласка, введи вік цифрами (наприклад: 25):",
        "ask_weight": "Яка твоя вага (кг)? (наприклад: 75.5)",
        "invalid_weight": "⚠️ Введи вагу числом (наприклад: 80 або 75.5):",
        "ask_goal": "Яка твоя головна мета?",
        "profile_complete": "✅ Профіль налаштовано!",
        "referral_notification": "🎁 Твій друг зареєструвався! +3 спроби.",
        "sub_error": "❌ Помилка! Підпишіться на всі канали.",
        "subs_instruction": "Натисніть кнопку нижче, щоб підписатися. Після цього поверніться та натисніть Перевірити.",
        "subs_redirect": "➡️ ПЕРЕЙТИ В КАНАЛ",
        "subs_wait": "⏳ Зачекайте ще {sec} сек. йде перевірка...",
        "subs_not_all": "❌ Ви відкрили не всі посилання!",
        "web_app_btn": "📊 Мій Прогрес (Web App)",
        "food_analysis": "🔬 Аналіз калорійності їжі",
        "nutrition": "🍎 Харчування",
        "balance": "💳 Баланс",
        "ai_chat": "💬 Чат з ШІ",
        "account": "👤 Акаунт",
        "support": "🆘 Підтримка",
        "referral": "🔗 Реферальна програма",
        "subscription": "💎 Підписка",
        "profile_title": "👤 **Профіль**",
        "profile_not_found": "❌ Профіль не знайдено. Натисни /start",
        "name_label": "Ім'я: ",
        "age_label": "Вік: ",
        "weight_label": "Вага: ",
        "goal_label": "Мета: ",
        "balance_label": "💳 Баланс: ",
        "attempts": " спроб",
        "your_balance": "💰 Твій баланс: ",
        "payment_success": "🎉 Оплата пройшла успішно! Вам нараховано безліміт. Ваш поточний баланс: ",
        "subscription_title": "Місячна підписка Virtus Fit",
        "subscription_desc": "Безлімітні генерації та аналіз їжі на 30 днів",
        "subscription_": "Підписка",
        "stars_label": "⭐️ Оплатити Stars (250 ⭐)",
        "crypto_label": "₿ Оплатити Криптою",
        "bank_payment":"💳 Оплата картою (UAH/RUB/USD)",
        "payment_label": "Оберіть зручний спосіб поповнення балансу (доступ до ШІ на місяць): ",
        "select_role": "Виберіть режим роботи ШІ асистента:",
        "role_coach": "🏋️ Тренер",
        "role_psy": "🧠 Психолог",
        "role_doc": "🏥 Лікар-консультант",
        "role_changed": "✅ Режим змінено на: ",
        "ask_question": "Тепер пиши своє запитання або надішли голос.",
        "thinking": "⏳ Думаю",
        "insufficient_balance": "❌ Недостатньо коштів!",
        "analyzing": "🔍 Аналізую фото та описання...",
        "ai_error": "⚠️ Помилка ШІ: ",
        "ask_bug": "🪲 Опиши проблему одним повідомленням:",
        "bug_sent": "✅ Надіслано розробнику!",
        "bug_notification": "🚨 БАГ від ",
        "referral_title": "🎁 Реферальна програма",
        "referral_desc": "Запрошуй друзів і отримуй +3 спроби за кожного, хто завершить реєстрацію!\n\n",
        "referral_count": "👥 Запрошено друзів: `",
        "referral_link": "`\n🔗 Твоє посилання:\n`",
        "channel_fitness": "🔥 Фітнес Хаб",
        "channel_health": "🍏 Здоров'я",
        "prompt_nutrition": "📸 Надішли мені фото своєї страви і, якщо потрібно, додай описання текстом (наприклад, склад або вагу). Я порахую калорії!",
        "prompt_workouts": "Створи детальний план тренувань на тиждень",
        "prompt_diet": "Створи детальний план харчування на день",
        "dietitian_prompt": "Ти професійний дієтолог. Проаналізуй фото їжі, враховуючи текст користувача. Визнач страву, вагу, калорії та макроси. Дай пораду, чи підходить це цілям користувача.",
        "user_context": "Користувач: ",
        "years_old": " років, ",
        "kg": "кг, мета: ",
        "user_text": "Текст від користувача: ",
        "input_placeholder": "Можеш спитати тут будь-що...",
    },
    "kk": {
        "welcome": "👊 Сәлем! 👋😊 Virtus-қа қош келдіңіз — сіздің цифрлық тренеріңіз.\n\n❌ Шаблондық бағдарламалар жоқ — тек жеке тәсіл!\n🤖 Біздің нейрондық желі мінсіз жоспар құрады. Мұнда сіз жаттықтырушымен, психологпен және дәрігермен кеңесе аласыз. \n🍔 Мұнда сіз өзіңіздің сүйікті бургеріңізде қанша калория бар екенін фотодан біле аласыз!\n\n🎁 Демеушілердің арналарына жазылып, 10 тегін генерация алыңыз!",
        "check_subs_btn": "✅ ЖАЗЫЛУДЫ ТЕКСЕРУ",
        "subs_checked": "🎉 Рұқсат берілді! Сізге қалай вөндеуге болады?",
        "ask_name": "⚠️ Атында сандар болмауы керек. Нақты атыңызды енгізіңіз:",
        "valid_name": "Сізге қалай вөндеуге болады?",
        "ask_age": "Жасыңыз нешеде? (Санмен енгізіңіз)",
        "invalid_age": "⚠️ Жасыңызды санмен енгізіңіз (мысалы: 25):",
        "ask_weight": "Салмағыңыз қандай (кг)? (мысалы: 75.5)",
        "invalid_weight": "⚠️ Салмағыңызды санмен енгізіңіз (мысалы: 80 немесе 75.5):",
        "ask_goal": "Сіздің негізгі мақсатыңыз қандай?",
        "profile_complete": "✅ Профиль бапталды!",
        "referral_notification": "🎁 Досыңыз тіркелді! +3 әрекет.",
        "sub_error": "❌ Қате! Барлық арналарға жазылыңыз.",
        "subs_instruction": "Жазылу үшін төмендегі түймені басыңыз. Содан кейін қайтып келіп, Тексеру түймесін басыңыз.",
        "subs_redirect": "➡️ АРНАҒА ӨТУ",
        "subs_wait": "⏳ Тағы {sec} сек күтіңіз. Тексеру жүріп жатыр...",
        "subs_not_all": "❌ Сіз барлық сілтемелерді ашқан жоқсыз!",
        "web_app_btn": "📊 Менің прогресім (Web App)",
        "food_analysis": "🔬 Тағам калориясын талдау",
        "nutrition": "🍎 Тамақтану",
        "balance": "💳 Теңгерім:",
        "ai_chat": "💬 AI-мен чат",
        "account": "👤 Есептік жазба",
        "support": "🆘 Қолдау",
        "referral": "🔗 Жолдама",
        "subscription": "💎 Жазылым",
        "profile_title": "👤 **Профиль**",
        "profile_not_found": "❌ Профиль табылмады. /start түймесін басыңыз",
        "name_label": "Аты: ",
        "age_label": "Жасы: ",
        "weight_label": "Салмағы: ",
        "goal_label": "Мақсаты: ",
        "balance_label": "💳 Теңгерім: ",
        "attempts": " әрекет.",
        "your_balance": "💰 Сіздің балансыңыз: ",
        "payment_success": "🎉 Төлем сәтті өтті! Шектеусіз рұқсат. Ағымдағы балансыңыз: ",
        "subscription_title": "Virtus Fit айлық жазылымы",
        "subscription_desc": "30 күн бойы шектеусіз генерация және тағам талдауы",
        "subscription_": "Жазылым",
        "stars_label": "⭐️ Stars-пен төлеу (250 ⭐)",
        "crypto_label": "₿ Криптовалютамен төлеу",
        "bank_payment": "💳 Картамен төлеу (UAH/RUB/USD)",
        "payment_label": "Балансты толтырудың ыңғайлы әдісін таңдаңыз (ІІ-ге бір айлық рұқсат):",
        "select_role": "ЖИ ассистентінің жұмыс режимін таңдаңыз:",
        "role_coach": "🏋️ Жаттықтырушы",
        "role_psy": "🧠 Психолог",
        "role_doc": "🏥 Дәрігер-кеңесші",
        "role_changed": "✅ Режим өзгертілді: ",
        "ask_question": "Енді сұрағыңызды жазыңыз немесе дауыстық хабарлама жіберіңіз.",
        "thinking": "⏳ Ойланудамын",
        "insufficient_balance": "❌ Қаражат жеткіліксіз!",
        "analyzing": "🔍 Фото мен сипаттаманы талдаудамын...",
        "ai_error": "⚠️ ЖИ қатесі: ",
        "ask_bug": "🪲 Мәселені бір хабарламамен сипаттаңыз:",
        "bug_sent": "✅ Әзірлеушіге жіберілді!",
        "bug_notification": "🚨 БАГ жіберген: ",
        "referral_title": "🎁 Рефералдық бағдарлама",
        "referral_desc": "Достарыңызды шақырыңыз және тіркелген әрбір адам үшін +3 әрекет алыңыз!\n\n",
        "referral_count": "👥 Шақырылған достар: `",
        "referral_link": "`\n🔗 Сіздің сілтемеңіз:\n`",
        "channel_fitness": "🔥 Фитнес Хаб",
        "channel_health": "🍏 Денсаулық",
        "prompt_nutrition": "📸 Тағамыңыздың суретін жіберіңіз және қажет болса, мәтіндік сипаттама қосыңыз (мысалы, құрамы немесе салмағы). Мен калорияны есептеймін!",
        "prompt_workouts": "Бір аптаға арналған егжей-тегжейлі жаттығу жоспарын жасаңыз",
        "prompt_diet": "Бір күнге арналған егжей-тегжейлі тамақтану жоспарын жасаңыз",
        "dietitian_prompt": "Сіз кәсіби диетологсыз. Пайдаланушы мәтінін ескере отырып, тағам фотосын талдаңыз. Тағамды, салмағын, ккал және АӨК (БЖУ) анықтаңыз. Бұл пайдаланушының мақсатына сәйкес келетіні туралы кеңес беріңіз.",
        "user_context": "Пайдаланушы: ",
        "years_old": " жаста, ",
        "kg": "кг, мақсаты: ",
        "user_text": "Пайдаланушы мәтіні: ",
        "input_placeholder": "Осында кез келген сұрақ қоя аласыз...",
    }
}

def get_text(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["ru"]).get(key, key)
# --- НАСТРОЙКИ ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('models/gemini-3-flash-preview') 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 983710534))
PAYMENT_TOKEN = os.getenv("BOT_TOKEN") # Используем тот же токен
WELCOME_IMAGE_PATH = os.path.join(BASE_DIR, "white.jpg")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
REQUIRED_CHANNELS = []

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ==========================================
# 🛡 АНТИФЛУД ЗАХИСТ (MIDDLEWARE)
# ==========================================
class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, limit=1.5):
        self.limit = limit
        self.users = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        
        # --- НОВИЙ БЛОК: Вимикаємо антифлуд для анкет ---
        state = data.get("state")
        if state:
            current_state = await state.get_state()
            if current_state is not None:
                # Якщо юзер відповідає на питання (має активний стан) - пропускаємо миттєво!
                return await handler(event, data)
        # ------------------------------------------------

        user_id = event.from_user.id
        now = time.time()

        if user_id in self.users:
            if now - self.users[user_id] < self.limit:
                # Якщо пише занадто швидко і це не анкета - блокуємо
                return
        
        self.users[user_id] = now
        return await handler(event, data)

# Підключаємо охоронця до бота (для тексту і для кнопок)
dp.message.middleware(AntiFloodMiddleware(1.5)) # Затримка 1.5 секунди
dp.callback_query.middleware(AntiFloodMiddleware(1.5))
# ==========================================

# --- БАЗА ДАННЫХ ---

# ФУНКЦІЯ ФОНОВОГО ПРОЦЕСОРА
async def process_ai_requests():
    print("ШІ-процесор запущено...")
    while True:
        try:
            res = supabase.table("ai_requests").select("*").eq("status", "pending").execute()
            for req in res.data:
                req_id = req["id"]
                user_prompt = req["prompt"]
                try:
                    print(f"Генерую план для запиту {req_id}...")
                    full_prompt = f"Ти професійний фітнес-тренер та дієтолог. Склади детальний, структурований план. Відповідай мовою запиту користувача. Запит користувача: {user_prompt}"
                    ai_response = model.generate_content(full_prompt)
                    reply_text = ai_response.text
                    supabase.table("ai_requests").update({
                        "status": "completed",
                        "response": reply_text
                    }).eq("id", req_id).execute()
                    print(f"Готово для {req_id}!")
                except Exception as e:
                    print(f"Помилка Gemini: {e}")
                    supabase.table("ai_requests").update({"status": "error"}).eq("id", req_id).execute()
        except Exception as e:
            pass
        await asyncio.sleep(3)

class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_weight = State()
    waiting_for_goal = State()

class Support(StatesGroup):
    waiting_for_bug_report = State()

# --- КЛАВИАТУРЫ ---
def get_sub_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    # ОСЬ ТУТ ЗМІНЮЄМО НАЗВИ КНОПОК:
    builder.row(types.InlineKeyboardButton(text="💎 Lucid Dreams", callback_data="go_link_2"))
    builder.row(types.InlineKeyboardButton(text="🔥 Virtus FIT", callback_data="go_link_3")) 
    
    builder.row(types.InlineKeyboardButton(text=get_text(lang, "check_subs_btn"), callback_data="check_subs"))
    return builder.as_markup()

def get_roles_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=get_text(lang, "role_coach"), callback_data="set_role_coach"), 
                types.InlineKeyboardButton(text=get_text(lang, "role_psy"), callback_data="set_role_psy"))
    builder.row(types.InlineKeyboardButton(text=get_text(lang, "role_doc"), callback_data="set_role_doc"))
    return builder.as_markup()

def get_language_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"),
        types.InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en"),
        types.InlineKeyboardButton(text="🇺🇦 Українська", callback_data="set_lang_uk")
    )
    return builder.as_markup()

# --- ОБРАБОТЧИКИ СТАРТА И РЕГИСТРАЦИИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject, state: FSMContext):
    user_id = message.from_user.id
    args = command.args
    referrer_id = args if args and args.isdigit() else None

    try:
        user_check = supabase.table("users").select("user_id").eq("user_id", user_id).execute()
        is_new_user = len(user_check.data) == 0

        if is_new_user and referrer_id and int(referrer_id) != user_id:
            res = supabase.table("users").select("xp, referrals_count, name").eq("user_id", referrer_id).execute()
            if len(res.data) > 0:
                referrer_data = res.data[0] 
                new_xp = (referrer_data.get("xp") or 0) + 200
                new_count = (referrer_data.get("referrals_count") or 0) + 1
                referrer_name = referrer_data.get("name") or "Атлет"
                
                supabase.table("users").update({
                    "xp": new_xp, 
                    "referrals_count": new_count
                }).eq("user_id", referrer_id).execute()
                
                await state.update_data(invited_by=referrer_name)
    except Exception as e:
        print(f"Помилка БД: {e}")

    await state.update_data(referrer_id=referrer_id)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🇷🇺 RU", callback_data="set_lang_ru"),
                types.InlineKeyboardButton(text="🇺🇦 UA", callback_data="set_lang_ua"))
    builder.row(types.InlineKeyboardButton(text="🇺🇸 EN", callback_data="set_lang_en"),
                types.InlineKeyboardButton(text="🇰🇿 KK", callback_data="set_lang_kk"))
    
    await message.answer("Оберіть мову / Choose language:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("set_lang_"))
async def set_lang_handler(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    data = await state.get_data()
    referrer = data.get("referrer")
    final_ref = referrer if referrer and referrer != user_id else None 
    
    response = supabase.table("users").select("user_id").eq("user_id", user_id).execute()
    if not response.data : 
        supabase.table("users").upsert({"user_id": user_id, "language": lang, "balance": 10, "referred_by": final_ref}).execute()
    else :
        supabase.table("users").upsert({"user_id": user_id, "language": lang}).execute()
    await callback.message.delete()
    try:
        await callback.message.answer_photo(
            photo=FSInputFile(WELCOME_IMAGE_PATH),
            caption=get_text(lang, "welcome"),
            reply_markup=get_sub_keyboard(lang)
        )
    except:
        await callback.message.answer(get_text(lang, "welcome"), reply_markup=get_sub_keyboard(lang))

async def is_user_subscribed(user_id: int) -> bool:
    if not REQUIRED_CHANNELS:
        return True 
    for channel_id in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            continue 
    return True

@dp.callback_query(F.data.startswith("go_link_"))
async def track_and_redirect(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name
    lang = await get_user_language(user_id)
    link_id = callback.data.replace("go_", "") 

    existing = supabase.table("link_clicks").select("id").eq("user_id", user_id).eq("link_id", link_id).execute()

    if not existing.data:
        try:
            supabase.table("link_clicks").insert({
                "user_id": user_id,
                "user_name": user_name,
                "link_id": link_id,
                "language": lang
            }).execute()
        except Exception as e:
            print(f"Помилка запису: {e}")

    await state.update_data({link_id: time.time()})
    
    urls = {
        "link_2": "https://t.me/luciddreams?start=_tgr_B8yYvxE0NDky",
        "link_3": "https://t.me/+_k4a8MQjfUAxYWMy"
    }
    
    markup = InlineKeyboardBuilder()
    markup.row(types.InlineKeyboardButton(text=get_text(lang, "subs_redirect"), url=urls[link_id]))
    await callback.message.answer(get_text(lang, "subs_instruction"), reply_markup=markup.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "check_subs")
async def check_subs(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    data = await state.get_data()
    
    required = ["link_2", "link_3"]
    clicked_all = all(link in data for link in required)
    
    if not clicked_all: 
        return await callback.answer(get_text(lang, "subs_not_all"), show_alert=True)

    last_click = max(data[link] for link in required)
    if time.time() - last_click < 10:
        wait_sec = int(10 - (time.time() - last_click))
        msg = get_text(lang, "subs_wait").format(sec=wait_sec)
        return await callback.answer(msg, show_alert=True)

    await callback.message.answer(get_text(lang, "subs_checked"))
    await state.set_state(Registration.waiting_for_name)
    await callback.answer()

@dp.message(Registration.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)  
    if any(char.isdigit() for char in message.text):
        return await message.answer(get_text(lang, "ask_name"))
    await state.update_data(name=message.text)
    await message.answer(get_text(lang, "ask_age"))
    await state.set_state(Registration.waiting_for_age)

@dp.message(Registration.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)  
    if not message.text.isdigit():
        return await message.answer(get_text(lang, "invalid_age"))
    await state.update_data(age=int(message.text))
    await message.answer(get_text(lang, "ask_weight"))
    await state.set_state(Registration.waiting_for_weight)

@dp.message(Registration.waiting_for_weight)
async def process_weight(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)  
    weight_text = message.text.replace(',', '.')
    try:
        weight = float(weight_text)
        await state.update_data(weight=weight)
        await message.answer(get_text(lang, "ask_goal"))
        await state.set_state(Registration.waiting_for_goal)
    except ValueError:
        await message.answer(get_text(lang, "invalid_weight"))

@dp.message(Registration.waiting_for_goal)
async def process_goal(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = await get_user_language(user_id)

    supabase.table("users").update({
        "name": data['name'],
        "age": data['age'],
        "weight": data['weight'],
        "goal": message.text
    }).eq("user_id", user_id).execute()
    
    user_res = supabase.table("users").select("*").eq("user_id", user_id).single().execute()
    user = user_res.data
    
    if user and user.get('referred_by'):
        ref_id = user['referred_by']
        ref_res = supabase.table("users").select("balance").eq("user_id", ref_id).execute()
        if ref_res.data: 
            current_balance = ref_res.data[0].get('balance', 0)
            supabase.table("users").update({"balance": int(current_balance) + 3}).eq("user_id", ref_id).execute()
            try:
                await bot.send_message(ref_id, get_text(lang, "referral_notification"))
            except: pass
            
    await message.answer(get_text(lang, "profile_complete"), reply_markup=get_main_menu_with_app(lang, get_text, user_id))
    await state.clear()

@dp.message(Support.waiting_for_bug_report)
async def send_bug(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    await bot.send_message(ADMIN_ID, f"{get_text(lang, 'bug_notification')} {message.from_user.id}:\n{message.text}")
    await message.answer(get_text(lang, "bug_sent")); await state.clear()

@dp.callback_query(F.data.startswith("set_role_"))
async def set_role(callback: types.CallbackQuery):
    role = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    supabase.table("users").update({"current_role": role}).eq("user_id", user_id).execute()
    
    role_names = {
        "coach": get_text(lang, "role_coach"),
        "psy": get_text(lang, "role_psy"),
        "doc": get_text(lang, "role_doc")
    }

    await callback.message.answer(f"{get_text(lang, 'role_changed')}{role_names.get(role)}. {get_text(lang, 'ask_question')}")
    await callback.answer()

async def add_balance(user_id: int, amount: int):
    res = supabase.table("users").select("balance").eq("user_id", user_id).execute()
    current_balance = res.data[0].get('balance', 0) if res.data else 0
    new_balance = int(current_balance) + amount
    supabase.table("users").update({"balance": new_balance}).eq("user_id", user_id).execute()
    return new_balance

@dp.message(Command("add"))
async def admin_add_balance(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        args = message.text.split()
        target_id = int(args[1])
        amount = int(args[2])
        await add_balance(target_id, amount)
        await message.answer(f"✅ Начислил {amount} пользователю {target_id}")

@dp.message(Command("broadcast"))
async def admin_broadcast(message: types.Message, command: CommandObject):
    # Проверяем, что команду вызвал именно ты (Админ)
    if message.from_user.id != ADMIN_ID:
        return

    # Текст для рассылки — это то, что ты напишешь после /broadcast
    text_to_send = command.args
    if not text_to_send:
        return await message.answer("⚠️ Использование: /broadcast Текст вашего сообщения")

    await message.answer("⏳ Начинаю рассылку... Это может занять некоторое время.")

    # Достаем ВСЕХ пользователей из Supabase
    res = supabase.table("users").select("user_id").execute()
    users = res.data
    
    success_count = 0
    blocked_count = 0

    for u in users:
        try:
            await bot.send_message(chat_id=u['user_id'], text=text_to_send, parse_mode="HTML")
            success_count += 1
            # Обязательная задержка! Telegram банит, если слать больше 30 сообщений в секунду
            await asyncio.sleep(0.1) 
        except Exception as e:
            # Если пользователь заблокировал бота
            blocked_count += 1

    await message.answer(f"✅ **Рассылка завершена!**\n\nУспешно отправлено: {success_count}\nЗаблокировали бота: {blocked_count}", parse_mode="Markdown")

@dp.message(Command("stats"))
async def get_click_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    res = supabase.table("link_clicks").select("link_id, user_name").execute()
    if not res.data:
        return await message.answer("📊 База даних переходів порожня.")

    stats = {"link_2": 0, "link_3": 0}
    all_users = {"link_2": set(), "link_3": set()} 

    for row in res.data:
        lid = row['link_id']
        name = row.get('user_name') or "Без імені"
        
        if lid in stats:
            stats[lid] += 1
            all_users[lid].add(name) 

    report = "📊 **ПОВНИЙ ЗВІТ ПЕРЕХОДІВ (ЗА ВЕСЬ ЧАС):**\n\n"
    
    def get_all_names(link_id):
        names = sorted(list(all_users[link_id])) 
        return ", ".join(names) if names else "немає переходів"
  
    report += f"💰 **Крипта (link_2):** `{stats['link_2']}` кліків\n"
    report += f"└👤 Юзери: _{get_all_names('link_2')}_\n\n"
    
    report += f"💻 **Чатыч (link_3):** `{stats['link_3']}` кліків\n"
    report += f"└👤 Юзери: _{get_all_names('link_3')}_\n\n"
    
    report += f"📈 **Загальна кількість кліків:** `{len(res.data)}`"

    if len(report) > 4096:
        report = report[:4000] + "...\n\n⚠️ *Звіт занадто довгий для одного повідомлення*"

    await message.answer(report, parse_mode="Markdown")

@dp.message(F.text)
async def handle_text(message: types.Message, state: FSMContext):
    if await state.get_state() is not None:
        return 

    user_id = message.from_user.id
    text = message.text
    lang = await get_user_language(user_id)

    # 1. ОБРОБКА СИСТЕМНИХ КНОПОК
    if text == get_text(lang, "account"):
        res = supabase.table("users").select("name, age, weight, goal, balance").eq("user_id", user_id).execute()
        if res.data:
            u = res.data[0]
            ans = (f"{get_text(lang, 'profile_title')}\n{get_text(lang, 'name_label')}{u.get('name')}\n"
                   f"{get_text(lang, 'age_label')}{u.get('age')}\n{get_text(lang, 'weight_label')}{u.get('weight')} kg\n"
                   f"{get_text(lang, 'goal_label')}{u.get('goal')}\n{get_text(lang, 'balance_label')}{u.get('balance')}")
            await message.answer(ans)
        return 

    elif text == get_text(lang, "balance"):
        res = supabase.table("users").select("balance").eq("user_id", user_id).single().execute()
        balance = res.data.get("balance", 0) if res.data else 0
        await message.answer(f"{get_text(lang, 'your_balance')}{balance}")
        return 

    elif text == get_text(lang, "ai_chat"):
        await message.answer(get_text(lang, "select_role"), reply_markup=get_roles_keyboard(lang))
        return

    elif text == get_text(lang, "support"):
        await message.answer(get_text(lang, "ask_bug"))
        await state.set_state(Support.waiting_for_bug_report)
        return

    elif text == get_text(lang, "referral"):
        res = supabase.table("users").select("user_id", count="exact").eq("referred_by", user_id).execute()
        link = await create_start_link(bot, str(user_id), encode=True)
        count = res.count if res.count is not None else 0
        await message.answer(f"{get_text(lang, 'referral_title')}\n\n{get_text(lang, 'referral_desc')}"
                             f"{get_text(lang, 'referral_count')}{count}\n{get_text(lang, 'referral_link')}{link}")
        return

    elif text == get_text(lang, "subscription"):
        builder = InlineKeyboardBuilder()
        tribute_url = "https://t.me/tribute/app?startapp=priw" 
        builder.row(types.InlineKeyboardButton(text="💳 Карта (UAH/USD/EUR/RUB)", url=tribute_url))
        builder.row(types.InlineKeyboardButton(text="₿ Оплатить Криптой (USDT)", callback_data="buy_crypto_1000"))
        builder.row(types.InlineKeyboardButton(text="⭐️ Оплатить Stars (250 ⭐)", callback_data="pay_stars_250"))
        await message.answer("Выберите способ получения Безлимита 👑 на месяц:", reply_markup=builder.as_markup())
        return

    elif text == get_text(lang, "food_analysis"):
        await message.answer(get_text(lang, "prompt_nutrition"))
        return

    # 2. ПЕРЕВІРКА ПІДПИСКИ І БАЛАНСУ ПЕРЕД ШІ
    if not await is_user_subscribed(user_id):
         return await message.answer(get_text(lang, "sub_error"), reply_markup=get_sub_keyboard(lang))

    res = supabase.table("users").select("*").eq("user_id", user_id).execute()
    user = res.data[0]
    if user.get('balance', 0) <= 0:
        return await message.answer(get_text(lang, "insufficient_balance"))

    msg = await message.answer(get_text(lang, "thinking")) 
    
    lang_map = {"ru": "Russian", "ua": "Ukrainian", "uk": "Ukrainian", "en": "English", "kk": "Kazakh"}
    target_lang = lang_map.get(lang, "Russian")

    query_text = get_text(lang, "prompt_diet") if text == get_text(lang, "nutrition") else text

    # 3. ЄДИНИЙ РОЗУМНИЙ ЗАПИТ ДО ШІ (Визначаємо і намір, і відповідь)
    prompt = f"""You are an AI assistant in a fitness app. 
    User info: {user.get('age')} years old, {user.get('weight')}kg. Target language: {target_lang}.
    Analyze the user's text: "{query_text}"
    
    CRITICAL INSTRUCTION (Intent Recognition):
    1. If the text is JUST a food item, a dish, ingredients, or a meal description with/without portions (e.g., "30 пельменей с мясом", "гречка 100 грамм", "яблоко", "я съел суп") -> This is a FOOD LOG.
       Output ONLY JSON:
       {{"intent": "food", "calories": 1050, "proteins": 45, "fats": 51, "carbs": 102, "food_name": "Name in {target_lang}"}}
       
    2. If the text is a QUESTION, a COMPLAINT, a REQUEST FOR ADVICE, or a general conversation (e.g., "почему я не худею?", "я на стрессе скинул вес", "как тренироваться?") -> This is CHAT.
       Output ONLY JSON:
       {{"intent": "chat", "reply": "Your detailed expert response in {target_lang}."}}
       
    Output MUST be valid JSON only. Do not add markdown or text outside the JSON.
    """

    try:
        t = {
            "en": {"added": "added!", "cal": "Calories", "prot": "Proteins", "fat": "Fats", "carb": "Carbs", "err": "Failed to recognize."},
            "ru": {"added": "добавлено!", "cal": "Калории", "prot": "Белки", "fat": "Жиры", "carb": "Углеводы", "err": "Не удалось распознать."},
            "ua": {"added": "додано!", "cal": "Калорії", "prot": "Білки", "fat": "Жири", "carb": "Вуглеводи", "err": "Не вдалося розпізнати."},
            "kk": {"added": "қосылды!", "cal": "Калориялар", "prot": "Ақуыздар", "fat": "Майлар", "carb": "Көмірсулар", "err": "Тану мүмкін болмады."}
        }.get(lang, {"added": "додано!", "cal": "Калорії", "prot": "Білки", "fat": "Жири", "carb": "Вуглеводи", "err": "Помилка."})

        # Викликаємо ШІ з примусовим форматом JSON
        response = await asyncio.wait_for(
            model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            ), 
            timeout=30.0
        )
        
        result = json.loads(response.text)
        
        # ВІДНІМАННЯ БАЛАНСУ
        new_bal = user['balance'] if user['balance'] > 9000 else user['balance'] - 1
        supabase.table("users").update({"balance": new_bal}).eq("user_id", user_id).execute()

        if result.get("intent") == "food":
            # Якщо це їжа - записуємо в БД
            supabase.table("nutrition_logs").insert({
                "user_id": user_id, 
                "calories": int(result.get("calories", 0)),
                "proteins": int(result.get("proteins", 0)), 
                "fats": int(result.get("fats", 0)),
                "carbs": int(result.get("carbs", 0)), 
                "food_name": str(result.get("food_name", "Food"))
            }).execute()
            
            final_reply = f"✅ <b>{result.get('food_name')}</b> {t['added']}\n\n🔥 {t['cal']}: {result.get('calories')} kcal\n🥩 {t['prot']}: {result.get('proteins')} g\n🧈 {t['fat']}: {result.get('fats')} g\n🍞 {t['carb']}: {result.get('carbs')} g"
            await msg.edit_text(final_reply, parse_mode="HTML")
            
        else:
            # Якщо це розмова - відправляємо відповідь експерта
            chat_reply = result.get("reply", "...")
            await msg.edit_text(chat_reply)

    except asyncio.TimeoutError:
        err_msg = "⏳ AI is overloaded. Try again." if lang == "en" else "⏳ ШІ відповідає задовго. Спробуйте ще раз."
        await msg.edit_text(err_msg)
    except Exception as e:
        print(f"Error in handle_text: {e}")
        await msg.edit_text(f"{get_text(lang, 'ai_error')} {str(e)}")

@dp.message(F.photo)
async def analyze_food_with_text(message: types.Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    t = {
        "en": {"added": "added!", "cal": "Calories", "prot": "Proteins", "fat": "Fats", "carb": "Carbs", "err_parse": "❌ Failed to recognize the food.", "err_time": "⏳ AI timeout."},
        "ru": {"added": "добавлено!", "cal": "Калории", "prot": "Белки", "fat": "Жиры", "carb": "Углеводы", "err_parse": "❌ Не удалось распознать еду.", "err_time": "⏳ ИИ думает слишком долго."},
        "ua": {"added": "додано!", "cal": "Калорії", "prot": "Білки", "fat": "Жири", "carb": "Вуглеводи", "err_parse": "❌ Не вдалося розпізнати страву.", "err_time": "⏳ ШІ відповідає занадто довго."},
        "kk": {"added": "қосылды!", "cal": "Калориялар", "prot": "Ақуыздар", "fat": "Майлар", "carb": "Көмірсулар", "err_parse": "❌ Тамақты тану мүмкін болмады.", "err_time": "⏳ ЖИ тым ұзақ жауап беруде."}
    }.get(lang, {"added": "додано!", "cal": "Калорії", "prot": "Білки", "fat": "Жири", "carb": "Вуглеводи", "err_parse": "❌ Не вдалося розпізнати страву.", "err_time": "⏳ ШІ відповідає занадто довго."})

    res = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if not res.data or res.data[0].get('balance', 0) <= 0:
        return await message.answer(get_text(lang, "insufficient_balance")) 
    
    user = res.data[0]
    status_msg = await message.answer("⏳..." if lang == "en" else "⏳ Розпізнаю фотографію...") 

    try:
        # 1. ШВИДКЕ ЗАВАНТАЖЕННЯ: Беремо фото прямо з пам'яті (без збереження на диск)
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        img = Image.open(downloaded_file) # Використовуємо PIL.Image

        user_text = message.caption if message.caption else ""
        ctx = f"Age: {user.get('age')}, Weight: {user.get('weight')}kg, Goal: {user.get('goal')}"
        lang_map = {"ru": "Russian", "ua": "Ukrainian", "uk": "Ukrainian", "en": "English", "kk": "Kazakh"}
        target_lang = lang_map.get(lang, "Ukrainian")
        
        # 2. ПРОМПТ ДЛЯ ЧИСТОГО JSON
        prompt = (
            f"Analyze this meal. User text: {user_text}. Context: {ctx}. "
            f"Estimate calories, proteins, fats, carbs. "
            f"CRITICAL RULE: Output ONLY a valid JSON object. "
            f'Format EXACTLY like this: {{"calories": 100, "proteins": 10, "fats": 5, "carbs": 20, "food_name": "Name in {target_lang}"}}'
        )
        
        # 3. ГЕНЕРАЦІЯ (з примусовим форматом JSON, що виключає помилки парсингу)
        response = await asyncio.wait_for(
            model.generate_content_async(
                [prompt, img], 
                generation_config={"response_mime_type": "application/json"}
            ), 
            timeout=25.0 # Зменшили таймаут, бо тепер працює блискавично
        )
        
        # Одразу беремо готовий словник, без костилів з find('{')
        nutrients = json.loads(response.text)
        
        # Запис у БД
        supabase.table("nutrition_logs").insert({
            "user_id": user_id,
            "calories": int(nutrients.get("calories", 0)),
            "proteins": int(nutrients.get("proteins", 0)),
            "fats": int(nutrients.get("fats", 0)),
            "carbs": int(nutrients.get("carbs", 0)),
            "food_name": str(nutrients.get("food_name", "Food"))
        }).execute()

        # Віднімання балансу
        new_bal = user['balance'] if user['balance'] > 9000 else user['balance'] - 1
        supabase.table("users").update({"balance": new_bal}).eq("user_id", user_id).execute()

        final_reply = (
            f"✅ <b>{nutrients.get('food_name')}</b> {t['added']}\n\n"
            f"🔥 {t['cal']}: {nutrients.get('calories')} kcal\n"
            f"🥩 {t['prot']}: {nutrients.get('proteins')} g\n"
            f"🧈 {t['fat']}: {nutrients.get('fats')} g\n"
            f"🍞 {t['carb']}: {nutrients.get('carbs')} g"
        )
        await status_msg.edit_text(final_reply, parse_mode="HTML")

    except asyncio.TimeoutError:
        await status_msg.edit_text(t['err_time'])
    except Exception as e:
        print(f"Error in photo analyzing: {e}")
        await status_msg.edit_text(t['err_parse'])

@dp.message(F.voice)
async def handle_ai(message: types.Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id) 

    res = supabase.table("users").select("*").eq("user_id", user_id).execute()
    
    if not res.data or res.data[0].get('balance', 0) <= 0:
        return await message.answer(get_text(lang, "insufficient_balance"))

    user = res.data[0]
    await message.answer("⏳ Думаю...")
    
    lang_map = {
        "ru": "Russian", "ua": "Ukrainian", "uk": "Ukrainian", "en": "English", "kk": "Kazakh"
    }
    target_lang = lang_map.get(lang, "Russian")
    
    ctx = (
        f"Answer strictly in {target_lang}. "
        f"{get_text(lang, 'user_context')}, {user.get('age')} {get_text(lang, 'years_old')} "
        f"{user.get('weight')} {get_text(lang, 'kg')} {user.get('goal')}"
    )
    
    try:
        f_info = await bot.get_file(message.voice.file_id)
        v_path = f"v_{user_id}.ogg"
        await bot.download_file(f_info.file_path, v_path)
            
        audio_file = genai.upload_file(path=v_path, mime_type="audio/ogg")
        
        response = model.generate_content([audio_file, ctx])
        os.remove(v_path)

        # ВІДНІМАННЯ БАЛАНСУ (З ПЕРЕВІРКОЮ БЕЗЛІМІТУ)
        new_bal = user['balance'] if user['balance'] > 9000 else user['balance'] - 1
        supabase.table("users").update({"balance": new_bal}).eq("user_id", user_id).execute()
        
        await message.answer(response.text)

    except Exception as e:
        await message.answer(f"{get_text(lang, 'ai_error')} {str(e)}")
    finally:
        # Гарантоване видалення голосового файлу
        if os.path.exists(v_path):
            os.remove(v_path)

# ==============================================================
# ЧИСТА, ОНОВЛЕНА ЛОГІКА ОПЛАТИ (БЕЗ ДУБЛІКАТІВ ТА З БЕЗЛІМІТОМ)
# ==============================================================

@dp.callback_query(F.data == "buy_crypto_1000")
async def create_crypto_invoice(callback: types.CallbackQuery):
    invoice = await crypto.create_invoice(asset='USDT', amount=6.0)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💸 Оплатить 6 USDT", url=invoice.bot_invoice_url))
    builder.row(types.InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_crypto_{invoice.invoice_id}"))
    await callback.message.answer(f"Счет создан! Сумма: 6 USDT\nПосле оплаты нажмите кнопку ниже:", reply_markup=builder.as_markup())

 

@dp.callback_query(F.data == "pay_stars_250")
async def send_invoice_stars(callback: types.CallbackQuery):
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Підписка Virtus Fit",
        description="Безлімітні генерації та аналіз їжі",
        payload="add_unlimited_sub",
        provider_token="", 
        currency="XTR", 
        prices=[types.LabeledPrice(label="Безліміт на місяць", amount=250)] 
    )

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def success_payment_handler(message: types.Message):
    user_id = message.from_user.id
    # ОПЛАТА УСПІШНА -> ДАЄМО БЕЗЛІМІТ (9999)
    supabase.table("users").update({
        "balance": 9999,
        "ai_generations": 9999
    }).eq("user_id", user_id).execute()
    
    await message.answer("🎉 Оплата пройшла успішно! Вам активовано Безліміт 👑 на місяць.")


async def main():  
    global crypto
    # Включаем крипто-бота здесь, когда движок уже запущен:
    if CryptoInstance:
        crypto = CryptoInstance(token=os.getenv("CRYPTO_PAY_TOKEN"))
        
    asyncio.create_task(process_ai_requests()) 
    await dp.start_polling(bot)