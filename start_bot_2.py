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
from aiogram.types import FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv() # Эта функция заставит Python прочитать твой файл .env

import re

def get_available_exercises_menu():
    """Сканує папку і повертає список доступних sys_id"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    videos_dir = os.path.join(base_dir, "selected_videos")
    
    available_exercises = []
    
    try:
        files = os.listdir(videos_dir)
        for f in files:
            if f.endswith(('.gif', '.mp4')):
                clean_name = os.path.splitext(f)[0]
                clean_name = clean_name.replace('.gif', '').replace('.mp4', '')
                available_exercises.append(clean_name)
    except Exception as e:
        print(f"Помилка читання папки: {e}")
        
    return ", ".join(available_exercises)

def get_clean_sys_id(text_string):
    """Превращает любое название ('3/4 sit-up', 'Bench Press') в идеальный формат ('3_4_sit_up', 'bench_press')"""
    if not text_string:
        return None
    clean = re.sub(r'[^a-zA-Z0-9]', '_', text_string.lower())
    return re.sub(r'_+', '_', clean).strip('_')

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
else:
    crypto = CryptoInstance(token=os.getenv("CRYPTO_PAY_TOKEN"))

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
        "workout_start": "🏃‍♂️ Начать тренировку",
        "workout_choose": "Как будем тренироваться сегодня?",
        "btn_saved_prog": "📁 Мои программы",
        "btn_fast_workout": "⚡ Быстрая от ИИ",
        "loc_home": "🏠 Дома",
        "loc_gym": "🏋️‍♂️ В зале",
        "loc_street": "🌳 На улице",
        "where_train": "Где будем тренироваться?",
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
        "workout_start": "🏃‍♂️ Start Workout",
        "workout_choose": "How are we training today?",
        "btn_saved_prog": "📁 My Programs",
        "btn_fast_workout": "⚡ Fast AI Workout",
        "loc_home": "🏠 At Home",
        "loc_gym": "🏋️‍♂️ In the Gym",
        "loc_street": "🌳 Outdoors",
        "where_train": "Where will we train?",
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
        "workout_start": "🏃‍♂️ Почати тренування",
        "workout_choose": "Як будемо тренуватися сьогодні?",
        "btn_saved_prog": "📁 Мої програми",
        "btn_fast_workout": "⚡ Швидка від ШІ",
        "loc_home": "🏠 Вдома",
        "loc_gym": "🏋️‍♂️ У залі",
        "loc_street": "🌳 На вулиці",
        "where_train": "Де будемо тренуватися?",
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
        "workout_start": "🏃‍♂️ Жаттығуды бастау",
        "workout_choose": "Бүгін қалай жаттығамыз?",
        "btn_saved_prog": "📁 Менің бағдарламаларым",
        "btn_fast_workout": "⚡ ЖИ-ден жылдам",
        "loc_home": "🏠 Үйде",
        "loc_gym": "🏋️‍♂️ Жаттығу залында",
        "loc_street": "🌳 Далада",
        "where_train": "Қайда жаттығамыз?",
    }
}

EXERCISE_GIFS = {
    # === ГРУДЬ (CHEST) ===
    "push_ups": "YOUR_FILE_ID_HERE",
    "bench_press": "YOUR_FILE_ID_HERE",
    "incline_bench_press": "YOUR_FILE_ID_HERE",
    "dumbbell_flyes": "YOUR_FILE_ID_HERE",
    "cable_crossover": "YOUR_FILE_ID_HERE",
    "dips": "YOUR_FILE_ID_HERE", # Отжимания на брусьях
    "machine_chest_press": "YOUR_FILE_ID_HERE",

    # === СПИНА (BACK) ===
    "pull_ups": "YOUR_FILE_ID_HERE", # Подтягивания
    "lat_pulldown": "YOUR_FILE_ID_HERE", # Тяга верхнего блока
    "barbell_row": "YOUR_FILE_ID_HERE", # Тяга штанги в наклоне
    "dumbbell_row": "YOUR_FILE_ID_HERE",
    "seated_cable_row": "YOUR_FILE_ID_HERE", # Тяга нижнего блока
    "t_bar_row": "YOUR_FILE_ID_HERE",
    "deadlift": "YOUR_FILE_ID_HERE", # Становая тяга
    "hyperextension": "YOUR_FILE_ID_HERE",

    # === НОГИ И ЯГОДИЦЫ (LEGS & GLUTES) ===
    "barbell_squat": "YOUR_FILE_ID_HERE",
    "goblet_squat": "YOUR_FILE_ID_HERE",
    "leg_press": "YOUR_FILE_ID_HERE",
    "lunges": "YOUR_FILE_ID_HERE", # Выпады
    "bulgarian_split_squat": "YOUR_FILE_ID_HERE",
    "leg_extension": "YOUR_FILE_ID_HERE", # Разгибание ног
    "leg_curl": "YOUR_FILE_ID_HERE", # Сгибание ног
    "calf_raise": "YOUR_FILE_ID_HERE", # Икры
    "romanian_deadlift": "YOUR_FILE_ID_HERE",
    "hip_thrust": "YOUR_FILE_ID_HERE", # Ягодичный мостик

    # === ПЛЕЧИ (SHOULDERS) ===
    "overhead_press": "YOUR_FILE_ID_HERE", # Армейский жим
    "dumbbell_shoulder_press": "YOUR_FILE_ID_HERE",
    "lateral_raises": "YOUR_FILE_ID_HERE", # Махи в стороны
    "front_raises": "YOUR_FILE_ID_HERE", # Махи перед собой
    "reverse_pec_deck": "YOUR_FILE_ID_HERE", # Обратная бабочка
    "face_pull": "YOUR_FILE_ID_HERE",
    "upright_row": "YOUR_FILE_ID_HERE", # Тяга к подбородку

    # === РУКИ: БИЦЕПС И ТРИЦЕПС (ARMS) ===
    "barbell_bicep_curl": "YOUR_FILE_ID_HERE",
    "dumbbell_bicep_curl": "YOUR_FILE_ID_HERE",
    "hammer_curls": "YOUR_FILE_ID_HERE",
    "preacher_curl": "YOUR_FILE_ID_HERE",
    "tricep_pushdown": "YOUR_FILE_ID_HERE", # Разгибание на блоке
    "overhead_tricep_extension": "YOUR_FILE_ID_HERE",
    "skull_crushers": "YOUR_FILE_ID_HERE", # Французский жим
    "tricep_kickbacks": "YOUR_FILE_ID_HERE",
    "close_grip_bench_press": "YOUR_FILE_ID_HERE",

    # === ПРЕСС И КОР (CORE) ===
    "plank": "YOUR_FILE_ID_HERE",
    "crunches": "YOUR_FILE_ID_HERE", # Скручивания
    "leg_raises": "YOUR_FILE_ID_HERE", # Подъем ног
    "russian_twist": "YOUR_FILE_ID_HERE",
    "bicycle_crunches": "YOUR_FILE_ID_HERE",
    "ab_wheel_rollout": "YOUR_FILE_ID_HERE",
    "mountain_climbers": "YOUR_FILE_ID_HERE",
    "hanging_leg_raises": "YOUR_FILE_ID_HERE",

    # === КАРДИО И РАЗМИНКА (CARDIO & WARMUP) ===
    "jumping_jacks": "YOUR_FILE_ID_HERE",
    "high_knees": "YOUR_FILE_ID_HERE",
    "burpees": "YOUR_FILE_ID_HERE",
    "jump_rope": "YOUR_FILE_ID_HERE",
    "box_jumps": "YOUR_FILE_ID_HERE",
    "kettlebell_swing": "YOUR_FILE_ID_HERE",

    # === АРМРЕСТЛИНГ / СПЕЦИФИКА (ARM WRESTLING / GRIP) ===
    "wrist_curls": "YOUR_FILE_ID_HERE",
    "reverse_wrist_curls": "YOUR_FILE_ID_HERE",
    "farmers_walk": "YOUR_FILE_ID_HERE",
    "pronator_work": "YOUR_FILE_ID_HERE",
    "static_hold": "YOUR_FILE_ID_HERE"
}


def get_text(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["ru"]).get(key, key)

# --- НАСТРОЙКИ ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('models/gemini-3-flash-preview') 
# --- ПАМЯТЬ БОТА (Храним контекст диалогов) ---
USER_HISTORY = {}


# --- НАСТРОЙКИ ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('models/gemini-3-flash-preview')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID")) # Переводим в число, так как ID — это integer
PAYMENT_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")
WELCOME_IMAGE_PATH = os.path.join(BASE_DIR, "black.jpg")

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
                    ai_response = await model.generate_content_async(full_prompt)
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

async def daily_reminder_task():
    print("⏳ Запуск проверки дневных норм...")
    try:
        users = supabase.table("users").select("user_id, language, daily_cal_goal, water_goal").execute().data
    except Exception as e:
        print(f"❌ Ошибка получения пользователей для напоминаний: {e}")
        return
    
    for user in users:
        uid = user.get('user_id')
        lang = user.get('language', 'ru')
        cal_goal = user.get('daily_cal_goal', 2000)
        
        # Получаем данные за сегодня
        today = time.strftime("%Y-%m-%d")
        try:
            logs = supabase.table("nutrition_logs").select("calories").eq("user_id", uid).gte("created_at", today).execute().data
            total_eaten = sum(item.get('calories', 0) for item in logs)
        except:
            total_eaten = 0
        
        # Проверка нормы (менее 80% от цели)
        if total_eaten < cal_goal * 0.8:
            # Словарь сообщений для всех языков
            messages = {
                "ru": "🍎 Вы сегодня недобрали калорий! Не забывайте питаться полноценно.",
                "ua": "🍎 Ви сьогодні недобрали калорій! Не забувайте харчуватися повноцінно.",
                "en": "🍎 You didn't meet your calorie goal today! Don't forget to eat well.",
                "kk": "🍎 Бүгін калория нормасын толтырмадыңыз! Толыққанды тамақтануды ұмытпаңыз."
            }
            
            # Выбираем сообщение, по умолчанию RU
            msg = messages.get(lang, messages["ru"])
            
            try:
                await bot.send_message(uid, msg)
                await asyncio.sleep(0.1) # Пауза между сообщениями, чтобы не получить бан от ТГ
            except Exception as e:
                print(f"⚠️ Не удалось отправить напоминание пользователю {uid}: {e}")

@dp.message(Command("test_remind"))
async def admin_test_remind(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🧪 Запускаю тестовую проверку норм...")
        await daily_reminder_task()
        await message.answer("✅ Проверка завершена.")

class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_weight = State()
    waiting_for_goal = State()

class Support(StatesGroup):
    waiting_for_bug_report = State()

class WorkoutFSM(StatesGroup):
    choosing_type = State()      # Выбор: сохраненная программа или новая
    waiting_location = State()   # Опрос: Дом или Зал?
    waiting_time = State() 
    waiting_difficulty = State()      # Опрос: Сколько минут?
    active_exercise = State()    # Выполнение упражнения
    resting = State()
    waiting_for_save_name = State()
    editing_stats = State()            # Отдых между подходами


class DietFSM(StatesGroup):
    waiting_for_goal = State()
    waiting_for_preferences = State()
    waiting_for_meals = State()

@dp.callback_query(F.data == "workout_fast", WorkoutFSM.choosing_type)
async def fast_workout_start(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id) # Получаем язык юзера из БД
    
    # --- ВОТ ЭТОТ БЛОК, ПРО КОТОРЫЙ ТЫ СПРАШИВАЛ ---
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text=get_text(lang, "loc_home"), callback_data="loc_home"),
        types.InlineKeyboardButton(text=get_text(lang, "loc_gym"), callback_data="loc_gym")
    )
    builder.row(types.InlineKeyboardButton(text=get_text(lang, "loc_street"), callback_data="loc_street"))

    text_ask = get_text(lang, "where_train")
    
    # Редактируем старое сообщение, заменяя его на опросник
    await callback.message.edit_text(text_ask, reply_markup=builder.as_markup())
    
    # Переключаем состояние: теперь бот ждет локацию
    await state.set_state(WorkoutFSM.waiting_location)
    # -----------------------------------------------
    
    await callback.answer() # Убираем "часики" на кнопке в ТГ

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
    referrer_id = None

    # 1. ДЕКОДИРУЕМ РЕФЕРАЛЬНУЮ ССЫЛКУ (расшифровываем буквы обратно в твой ID)
    if args:
        try:
            decoded_args = decode_payload(args)
            if decoded_args.isdigit():
                referrer_id = int(decoded_args)
        except Exception:
            # На случай, если кто-то запустит бота со ссылкой с обычными цифрами
            if args.isdigit():
                referrer_id = int(args)

    try:
        # Проверяем, есть ли юзер в базе
        user_check = supabase.table("users").select("user_id, language").eq("user_id", user_id).execute()
        is_new_user = len(user_check.data) == 0

        # 2. ЕСЛИ ЮЗЕР УЖЕ ЗАРЕГИСТРИРОВАН (случайно нажал на ссылку или просто написал /start)
        if not is_new_user:
            lang = user_check.data[0].get("language", "ru")
            welcome_back = "С возвращением!" if lang == "ru" else "З поверненням!"
            if lang == "en": welcome_back = "Welcome back!"
            if lang == "kk": welcome_back = "Қайта оралуыңызбен!"
            
            # Просто здороваемся и даем ему главное меню, ПРЕРЫВАЯ функцию
            await message.answer(welcome_back, reply_markup=get_main_menu_with_app(lang, get_text, user_id))
            return 

        # 3. ЕСЛИ ЮЗЕР НОВЫЙ И ПРИШЕЛ ПО ССЫЛКЕ - даем бонусы пригласившему
        if is_new_user and referrer_id and referrer_id != user_id:
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
        print(f"Ошибка БД: {e}")

    await state.update_data(referrer_id=referrer_id)

    # 4. ПОКАЗЫВАЕМ ВЫБОР ЯЗЫКА ТОЛЬКО НОВИЧКАМ
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

async def start_workout_mode(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    # Перевіряємо наявність програм у Supabase
    res = supabase.table("saved_programs").select("id").eq("user_id", user_id).execute()
    has_programs = len(res.data) > 0 if res.data else False
    
    builder = InlineKeyboardBuilder()
    if has_programs:
        builder.row(types.InlineKeyboardButton(text=get_text(lang, "btn_saved_prog"), callback_data="workout_saved"))
    
    builder.row(types.InlineKeyboardButton(text=get_text(lang, "btn_fast_workout"), callback_data="workout_fast"))
    
    await message.answer(get_text(lang, "workout_choose"), reply_markup=builder.as_markup())
    await state.set_state(WorkoutFSM.choosing_type)

# === ВРЕМЕННЫЙ ПОМОЩНИК ДЛЯ ПОЛУЧЕНИЯ FILE_ID ===
@dp.message(F.animation | F.video)
async def get_file_id_handler(message: Message):
    # Если ты прислал гифку (анимацию)
    if message.animation:
        file_id = message.animation.file_id
        await message.reply(f"🎯 Вот твой ID для гифки:\n\n`{file_id}`\n\n*(Нажми на текст, чтобы скопировать)*", parse_mode="Markdown")
    
    # Если ты прислал видео
    elif message.video:
        file_id = message.video.file_id
        await message.reply(f"🎥 Вот твой ID для видео:\n\n`{file_id}`\n\n*(Нажми на текст, чтобы скопировать)*", parse_mode="Markdown")
# ==================================================

@dp.message(WorkoutFSM.waiting_for_save_name)
async def workout_save_to_db(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    plan_name = message.text

    # Дістаємо JSON з пам'яті
    data = await state.get_data()
    workout_plan = data.get("workout_plan", [])

    if not workout_plan:
        await state.clear()
        return

    # --- Вираховуємо тотальні калорії та час ---
    total_cals = 0
    total_time_sec = 0
    
    for ex in workout_plan:
        sets = int(str(ex.get('sets', 0)).split()[0] if isinstance(ex.get('sets'), str) else ex.get('sets', 0))
        reps = int(str(ex.get('reps', 0)).split()[0] if isinstance(ex.get('reps'), str) else ex.get('reps', 0))
        rest = int(str(ex.get('rest_sec', 0)).split()[0] if isinstance(ex.get('rest_sec'), str) else ex.get('rest_sec', 0))

        total_cals += (sets * reps * 0.5)
        total_time_sec += sets * ((reps * 3) + rest)

    total_minutes = max(1, total_time_sec // 60)
    plan_content = json.dumps(workout_plan, ensure_ascii=False)

    try:
        # ПОПЫТКА 1: Сохраняем со всеми фишками (калории, время)
        supabase.table("saved_programs").insert({
            "user_id": user_id,
            "title": plan_name,
            "content": plan_content,
            "calories": int(total_cals),
            "duration": int(total_minutes)
        }).execute()
        
    except Exception as e:
        err_msg = str(e).lower()
        # Если Supabase жалуется на отсутствие колонок — включаем план "Б"
        if "calories" in err_msg or "duration" in err_msg or "does not exist" in err_msg:
            print("⚠️ [ВНИМАНИЕ] Колонки calories/duration не найдены в БД. Сохраняю базовую версию.")
            try:
                # ПОПЫТКА 2: Сохраняем по-старому, без новых колонок
                supabase.table("saved_programs").insert({
                    "user_id": user_id,
                    "title": plan_name,
                    "content": plan_content
                }).execute()
            except Exception as fallback_err:
                print(f"❌ Критическая ошибка БД: {fallback_err}")
                await state.clear()
                return await message.answer("❌ Помилка збереження.")
        else:
            print(f"❌ Неизвестная ошибка: {e}")
            await state.clear()
            return await message.answer("❌ Помилка збереження.")

    success_msg = "✅ Програму успішно збережено у 'Мої програми'!" if lang in ["ua", "uk"] else "✅ Программа успешно сохранена!"
    await message.answer(success_msg)
    await state.clear()

# 1. Юзер нажал "Изменить вес/повторы"
@dp.callback_query(F.data == "wo_edit_stats", WorkoutFSM.active_exercise)
async def ask_new_stats(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    if lang == "ru": msg = "✍️ Напишите новые **повторения** и **вес** через пробел.\n*Например, если сделали 10 раз с весом 50 кг, напишите:* `10 50`"
    elif lang == "en": msg = "✍️ Enter new **reps** and **weight** separated by space.\n*E.g., if you did 10 reps with 50 kg, type:* `10 50`"
    elif lang == "kk": msg = "✍️ Жаңа **қайталаулар** мен **салмақты** бос орын арқылы жазыңыз.\n*Мысалы, 50 кг салмақпен 10 рет жасасаңыз, былай жазыңыз:* `10 50`"
    else: msg = "✍️ Напишіть нові **повторення** та **вагу** через пробіл.\n*Наприклад, якщо зробили 10 разів з вагою 50 кг, напишіть:* `10 50`"
    
    # Переводим в режим ожидания текста, но удаляем старое сообщение с гифкой, чтобы не мешалось
    await state.set_state(WorkoutFSM.editing_stats)
    try: await callback.message.delete()
    except: pass
    await bot.send_message(user_id, msg, parse_mode="Markdown")
    await callback.answer()

# 2. Юзер ввел новые цифры (например: "10 50")
@dp.message(WorkoutFSM.editing_stats)
async def apply_new_stats(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    text = message.text.strip()
    
    # Пытаемся вытащить два числа из сообщения
    nums = re.findall(r'\d+', text)
    
    if len(nums) < 1:
        err = "⚠️ Я не нашел цифр. Напишите повторения и вес (например: `10 50`):" if lang == "ru" else "⚠️ Будь ласка, напишіть цифри (наприклад: `10 50`):"
        return await message.answer(err, parse_mode="Markdown")
        
    new_reps = int(nums[0])
    new_weight = int(nums[1]) if len(nums) > 1 else 0 # Если ввели только 1 число, считаем что вес = 0 (свой вес)
    
    # Достаем план тренировки и текущее упражнение
    data = await state.get_data()
    plan = data.get("workout_plan", [])
    ex_idx = data.get("current_ex_index", 0)
    
    # Обновляем данные прямо в плане
    if ex_idx < len(plan):
        plan[ex_idx]['reps'] = new_reps
        plan[ex_idx]['weight_kg'] = new_weight
        await state.update_data(workout_plan=plan)
    
    try: await message.delete()
    except: pass
    
    # Возвращаем пользователя в режим активной тренировки и показываем обновленную карточку
    await state.set_state(WorkoutFSM.active_exercise)
    await send_current_exercise(message, state, user_id, lang)

@dp.callback_query(F.data.startswith("diet_"), DietFSM.waiting_for_goal)
async def diet_goal_chosen(callback: types.CallbackQuery, state: FSMContext):
    goal = callback.data.split("_")[1] # lose, gain, maintain
    await state.update_data(diet_goal=goal)
    lang = await get_user_language(callback.from_user.id)
    
    if lang == "ru": msg = "Есть ли у вас пищевые аллергии или продукты, которые вы терпеть не можете?\n*(Напишите текстом или просто отправьте 'Нет')*"
    elif lang == "en": msg = "Do you have any food allergies or foods you hate?\n*(Type them out or just send 'No')*"
    elif lang == "kk": msg = "Тамаққа аллергияңыз немесе мүлдем ұнатпайтын тағамдарыңыз бар ма?\n*(Мәтінмен жазыңыз немесе 'Жоқ' деп жіберіңіз)*"
    else: msg = "Чи є у вас харчові алергії або продукти, які ви терпіти не можете?\n*(Напишіть текстом або просто відправте 'Ні')*"
    
    await callback.message.edit_text(msg, parse_mode="Markdown")
    await state.set_state(DietFSM.waiting_for_preferences)

@dp.message(DietFSM.waiting_for_preferences)
async def diet_prefs_entered(message: types.Message, state: FSMContext):
    await state.update_data(diet_prefs=message.text)
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="2", callback_data="meals_2"),
        types.InlineKeyboardButton(text="3", callback_data="meals_3"),
        types.InlineKeyboardButton(text="4", callback_data="meals_4"),
        types.InlineKeyboardButton(text="5", callback_data="meals_5")
    )
    
    if lang == "ru": msg = "Сколько приемов пищи в день вам удобно?"
    elif lang == "en": msg = "How many meals a day are comfortable for you?"
    elif lang == "kk": msg = "Күніне қанша рет тамақтанған ыңғайлы?"
    else: msg = "Скільки прийомів їжі на день вам зручно?"
    
    await message.answer(msg, reply_markup=builder.as_markup())
    await state.set_state(DietFSM.waiting_for_meals)

@dp.callback_query(F.data.startswith("meals_"), DietFSM.waiting_for_meals)
async def generate_diet_plan(callback: types.CallbackQuery, state: FSMContext):
    meals = callback.data.split("_")[1]
    data = await state.get_data()
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    wait_msg = "⏳ Составляю идеальный рацион..." if lang in ["ru", "kk"] else "⏳ Складаю ідеальний раціон..."
    await callback.message.edit_text(wait_msg)
    
    # Достаем возраст, вес и общую цель из БД
    res = supabase.table("users").select("age, weight, goal, balance").eq("user_id", user_id).execute()
    user = res.data[0] if res.data else {"age": 25, "weight": 70, "goal": "Фитнес", "balance": 10}
    
    # Мапим техническую цель в понятный текст для ИИ
    goal_map = {
        "lose": "Похудение (дефицит калорий)", 
        "gain": "Набор мышечной массы (профицит)", 
        "maintain": "Поддержание веса (баланс)"
    }
    target_goal = goal_map.get(data.get('diet_goal'), "Здоровое питание")
    
    lang_map = {"ru": "Russian", "ua": "Ukrainian", "uk": "Ukrainian", "en": "English", "kk": "Kazakh"}
    ai_lang = lang_map.get(lang, "Russian")
    
    # Формируем ультимативный промпт
    prompt = f"""
    Ты - профессиональный диетолог. Составь подробный рацион питания на 1 день.
    
    ДАННЫЕ КЛИЕНТА:
    - Возраст: {user.get('age')} лет
    - Вес: {user.get('weight')} кг
    - Глобальная цель: {user.get('goal')}
    - Текущая задача рациона: {target_goal}
    - Исключить продукты/Аллергии: {data.get('diet_prefs')}
    - Количество приемов пищи: {meals}
    
    ТВОЯ ЗАДАЧА:
    1. Распиши меню с точными граммовками.
    2. Укажи КБЖУ (Калории, Белки, Жиры, Углеводы) для каждого приема пищи.
    3. В конце напиши ИТОГОВЫЕ КБЖУ за весь день.
    4. Отвечай строго на языке: {ai_lang}.
    5. Сделай текст красиво отформатированным, используй маркдаун и уместные эмодзи.
    """
    
    try:
        response = await model.generate_content_async(prompt)
        
        # Списываем баланс генераций
        new_bal = user.get('balance', 1) - 1
        if new_bal < 0: new_bal = 0
        supabase.table("users").update({"balance": new_bal}).eq("user_id", user_id).execute()
        
        # Отправляем готовый рацион
        await callback.message.edit_text(response.text, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Ошибка генерации рациона: {e}")
        err_msg = "❌ Ошибка генерации." if lang in ["ru", "kk"] else "❌ Помилка генерації."
        await callback.message.edit_text(err_msg)
        
    await state.clear()

@dp.message(F.text)
async def handle_text(message: types.Message, state: FSMContext):
    if await state.get_state() is not None:
        return 

    user_id = message.from_user.id
    text = message.text
    lang = await get_user_language(user_id)
    # Визначаємо мову для відповіді
    lang_map = {"ru": "Russian", "ua": "Ukrainian", "uk": "Ukrainian", "en": "English"}
    target_lang = lang_map.get(lang, "English")

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
    
    elif text == get_text(lang, "subscription"):
        builder = InlineKeyboardBuilder()
        tribute_url = "https://t.me/tribute/app?startapp=priw" 
        builder.row(types.InlineKeyboardButton(text="💳 Карта (UAH/USD/EUR/RUB)", url=tribute_url))
        builder.row(types.InlineKeyboardButton(text="₿ Оплатить Криптой (USDT)", callback_data="buy_crypto_1000"))
        builder.row(types.InlineKeyboardButton(text="⭐️ Оплатить Stars (250 ⭐)", callback_data="pay_stars_250"))
        await message.answer("Выберите способ получения Безлимита 👑 на месяц:", reply_markup=builder.as_markup())
        return

    elif text == get_text(lang, "workout_start"):
        # Проверяем, есть ли у юзера сохраненные программы в БД
        res = supabase.table("saved_programs").select("id").eq("user_id", user_id).execute()
        has_programs = len(res.data) > 0 if res.data else False
        
        builder = InlineKeyboardBuilder()
        
        # Если есть программы, показываем кнопку "Мои программы"
        if has_programs:
            builder.row(types.InlineKeyboardButton(text=get_text(lang, "btn_saved_prog"), callback_data="workout_saved"))
        
        # Кнопка быстрой тренировки есть всегда
        builder.row(types.InlineKeyboardButton(text=get_text(lang, "btn_fast_workout"), callback_data="workout_fast"))
        
        await message.answer(get_text(lang, "workout_choose"), reply_markup=builder.as_markup())
        await state.set_state(WorkoutFSM.choosing_type) # Переводим юзера в состояние выбора тренировки
        return

    elif text == get_text(lang, "food_analysis"):
        await message.answer(get_text(lang, "prompt_nutrition"))
        return

    elif text == get_text(lang, "food_analysis"):
        await message.answer(get_text(lang, "prompt_nutrition"))
        return
    
    elif text == get_text(lang, "nutrition"):
        builder = InlineKeyboardBuilder()
        if lang == "ru":
            builder.row(types.InlineKeyboardButton(text="⚖️ Похудение", callback_data="diet_lose"))
            builder.row(types.InlineKeyboardButton(text="💪 Набор массы", callback_data="diet_gain"))
            builder.row(types.InlineKeyboardButton(text="🍏 Поддержание", callback_data="diet_maintain"))
            msg = "Какая у нас главная цель по питанию?"
        elif lang == "en":
            builder.row(types.InlineKeyboardButton(text="⚖️ Weight Loss", callback_data="diet_lose"))
            builder.row(types.InlineKeyboardButton(text="💪 Muscle Gain", callback_data="diet_gain"))
            builder.row(types.InlineKeyboardButton(text="🍏 Maintenance", callback_data="diet_maintain"))
            msg = "What is our main nutrition goal?"
        elif lang == "kk":
            builder.row(types.InlineKeyboardButton(text="⚖️ Салмақ тастау", callback_data="diet_lose"))
            builder.row(types.InlineKeyboardButton(text="💪 Бұлшықет қосу", callback_data="diet_gain"))
            builder.row(types.InlineKeyboardButton(text="🍏 Қалыпты ұстау", callback_data="diet_maintain"))
            msg = "Тамақтанудағы негізгі мақсатымыз қандай?"
        else:
            builder.row(types.InlineKeyboardButton(text="⚖️ Схуднення", callback_data="diet_lose"))
            builder.row(types.InlineKeyboardButton(text="💪 Набір маси", callback_data="diet_gain"))
            builder.row(types.InlineKeyboardButton(text="🍏 Підтримка", callback_data="diet_maintain"))
            msg = "Яка у нас головна ціль по харчуванню?"

        await message.answer(msg, reply_markup=builder.as_markup())
        await state.set_state(DietFSM.waiting_for_goal)
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

    # === ДОСТАЕМ ПАМЯТЬ ЮЗЕРА ===
    history_list = USER_HISTORY.get(user_id, [])
    history_text = "\n".join(history_list) if history_list else "No previous history."

    # 3. ЄДИНИЙ РОЗУМНИЙ ЗАПИТ ДО ШІ (Визначаємо і намір, і відповідь)
    prompt = f"""You are an AI assistant in a fitness app. 
    User info: {user.get('age')} years old, {user.get('weight')}kg. 
    CRITICAL: Respond strictly in {target_lang}.

    Recent conversation history:
    {history_text}

    Analyze the CURRENT user's text: "{query_text}"

    CRITICAL INSTRUCTION (Intent Recognition):
    1. If the text is JUST a food item, a dish, ingredients, or a meal description with/without portions (e.g., "30 пельменей с мясом", "гречка 100 грамм", "яблоко", "я съел суп") -> This is a FOOD LOG.
    Output ONLY JSON:
    {{"intent": "food", "calories": 1050, "proteins": 45, "fats": 51, "carbs": 102, "food_name": "Name in {target_lang}"}}
   
    2. If the text is a QUESTION, a COMPLAINT, a REQUEST FOR ADVICE, or a general conversation -> This is CHAT.
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
            
            # === ЗАПИСЫВАЕМ В ПАМЯТЬ ===
            history_list.append(f"User: {query_text}")
            history_list.append(f"AI: {chat_reply}")
            USER_HISTORY[user_id] = history_list[-6:] # Помним только последние 3 пары вопросов-ответов
            
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

    lang_map = {"ru": "Russian", "ua": "Ukrainian", "uk": "Ukrainian", "en": "English", "kk": "Kazakh"}
    target_lang = lang_map.get(lang, "English")
    
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
            f"Respond strictly in {target_lang}. "  # <--- Додана строга інструкція мови
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
    
    history_list = USER_HISTORY.get(user_id, [])
    history_text = "\n".join(history_list) if history_list else "No previous history."
    
    ctx = (
        f"Answer strictly in {target_lang}. "
        f"{get_text(lang, 'user_context')}, {user.get('age')} {get_text(lang, 'years_old')} "
        f"{user.get('weight')} {get_text(lang, 'kg')} {user.get('goal')}\n\n"
        f"Recent conversation history:\n{history_text}"
    )
    
    try:
        f_info = await bot.get_file(message.voice.file_id)
        v_path = f"v_{user_id}.ogg"
        await bot.download_file(f_info.file_path, v_path)
            
        audio_file = genai.upload_file(path=v_path, mime_type="audio/ogg")
        
        response = await model.generate_content_async([audio_file, ctx])
        os.remove(v_path)

        # ВІДНІМАННЯ БАЛАНСУ (З ПЕРЕВІРКОЮ БЕЗЛІМІТУ)
        new_bal = user['balance'] if user['balance'] > 9000 else user['balance'] - 1
        supabase.table("users").update({"balance": new_bal}).eq("user_id", user_id).execute()
        
        # === ЗАПИСЫВАЕМ ГОЛОС В ПАМЯТЬ ===
        history_list.append(f"User: [Voice Message]")
        history_list.append(f"AI: {response.text}")
        USER_HISTORY[user_id] = history_list[-6:]
        
        await message.answer(response.text)

    except Exception as e:
        await message.answer(f"{get_text(lang, 'ai_error')} {str(e)}")
    finally:
        # Гарантоване видалення голосового файлу
        if os.path.exists(v_path):
            os.remove(v_path)

# === ЭТАП 2: АДАПТИВНЫЙ ОПРОСНИК ДЛЯ ТРЕНИРОВКИ ===

import os

def get_available_exercises_menu():
    """Сканирует папку и возвращает список доступных sys_id в виде строки"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    videos_dir = os.path.join(base_dir, "renamed_videos") # Убедись, что тут правильное имя папки
    
    available_exercises = []
    
    try:
        files = os.listdir(videos_dir)
        for f in files:
            # Берем только медиафайлы
            if f.endswith(('.gif', '.mp4')):
                # Отрезаем расширение (bench_press.gif -> bench_press)
                clean_name = os.path.splitext(f)[0]
                # Убираем двойные расширения, если они есть (bench_press.gif.gif -> bench_press)
                clean_name = clean_name.replace('.gif', '').replace('.mp4', '')
                available_exercises.append(clean_name)
                
    except Exception as e:
        print(f"Ошибка чтения папки: {e}")
        
    # Возвращаем список через запятую: "bench_press, barbell_squat, pull_ups..."
    return ", ".join(available_exercises)

@dp.callback_query(F.data == "workout_fast", WorkoutFSM.choosing_type)
async def fast_workout_start(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Спрашиваем локацию
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🏠 Дома" if lang == "ru" else "🏠 Вдома", callback_data="loc_home"),
        types.InlineKeyboardButton(text="🏋️‍♂️ В зале" if lang == "ru" else "🏋️‍♂️ У залі", callback_data="loc_gym")
    )
    builder.row(types.InlineKeyboardButton(text="🌳 На улице" if lang == "ru" else "🌳 На вулиці", callback_data="loc_street"))
    
    text_ask = "Где будем тренироваться?" if lang == "ru" else "Де будемо тренуватися?"
    await callback.message.edit_text(text_ask, reply_markup=builder.as_markup())
    await state.set_state(WorkoutFSM.waiting_location)

@dp.callback_query(F.data.startswith("loc_"), WorkoutFSM.waiting_location)
async def workout_location_chosen(callback: types.CallbackQuery, state: FSMContext):
    location = callback.data.split("_")[1] # Получим: home, gym или street
    await state.update_data(workout_location=location) # Запоминаем выбор в оперативную память
    
    lang = await get_user_language(callback.from_user.id)

    # === БАГАТОМОВНИЙ ВИБІР ЧАСУ ===
    if lang == "ru":
        btn_15, btn_30, btn_60 = "15 мин", "30 мин", "60+ мин"
        text_ask = "Сколько времени у нас есть?"
    elif lang == "en":
        btn_15, btn_30, btn_60 = "15 min", "30 min", "60+ min"
        text_ask = "How much time do we have?"
    elif lang == "kk":
        btn_15, btn_30, btn_60 = "15 мин", "30 мин", "60+ мин"
        text_ask = "Қанша уақытымыз бар?"
    else:
        btn_15, btn_30, btn_60 = "15 хв", "30 хв", "60+ хв"
        text_ask = "Скільки часу у нас є?"
    
    # Спрашиваем время
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text=btn_15, callback_data="time_15"),
        types.InlineKeyboardButton(text=btn_30, callback_data="time_30"),
        types.InlineKeyboardButton(text=btn_60, callback_data="time_60")
    )
    
    await callback.message.edit_text(text_ask, reply_markup=builder.as_markup())
    await state.set_state(WorkoutFSM.waiting_time)


import json

@dp.callback_query(F.data.startswith("time_"), WorkoutFSM.waiting_time)
async def workout_time_chosen(callback: types.CallbackQuery, state: FSMContext):
    time_val = callback.data.split("_")[1]
    await state.update_data(workout_time=time_val)
    
    lang = await get_user_language(callback.from_user.id)

    # === БАГАТОМОВНИЙ ВИБІР СКЛАДНОСТІ ===
    if lang == "ru":
        btn_easy, btn_med, btn_hard = "🟢 Легко", "🟡 Средне", "🔴 Тяжело"
        text_ask = "Выберите сложность:"
    elif lang == "en":
        btn_easy, btn_med, btn_hard = "🟢 Easy", "🟡 Medium", "🔴 Hard"
        text_ask = "Choose difficulty:"
    elif lang == "kk":
        btn_easy, btn_med, btn_hard = "🟢 Оңай", "🟡 Орташа", "🔴 Қиын"
        text_ask = "Қиындықты таңдаңыз:"
    else:
        btn_easy, btn_med, btn_hard = "🟢 Легко", "🟡 Середньо", "🔴 Важко"
        text_ask = "Оберіть складність:"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text=btn_easy, callback_data="diff_easy"),
        types.InlineKeyboardButton(text=btn_med, callback_data="diff_medium"),
        types.InlineKeyboardButton(text=btn_hard, callback_data="diff_hard")
    )
    
    await callback.message.edit_text(text_ask, reply_markup=builder.as_markup())
    await state.set_state(WorkoutFSM.waiting_difficulty)


@dp.callback_query(F.data.startswith("diff_"), WorkoutFSM.waiting_difficulty)
async def generate_fast_workout(callback: types.CallbackQuery, state: FSMContext):
    difficulty = callback.data.split("_")[1]
    data = await state.get_data()
    time_val = data.get("workout_time")
    location = data.get("workout_location")
    
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Получаем вес пользователя из БД для расчетов
    res = supabase.table("users").select("weight").eq("user_id", user_id).execute()
    user_weight = res.data[0].get("weight", 80) if res.data else 80

    if lang == "ru": msg_wait = "⏳ Генерирую программу..."
    elif lang == "en": msg_wait = "⏳ Generating program..."
    elif lang == "kk": msg_wait = "⏳ Бағдарлама жасалуда..."
    else: msg_wait = "⏳ Генерую програму..."
    
    await callback.message.edit_text(msg_wait)
    
    lang_map = {"ru": "Russian", "ua": "Ukrainian", "uk": "Ukrainian", "en": "English", "kk": "Kazakh"}
    target_lang = lang_map.get(lang, "Ukrainian")
    
    loc_text = {"home": "дома", "gym": "в тренажерном зале", "street": "на улице"}.get(location, "дома")
    
    # === 1. ВИКЛИКАЄМО НАШУ ФУНКЦІЮ ДЛЯ СКАНУВАННЯ ПАПКИ ===
    exercises_menu = get_available_exercises_menu()
    
    # === 2. РОЗУМНИЙ ПРОМПТ З ЖОРСТКИМ ОБМЕЖЕННЯМ ===
    prompt = f"""
    Ти - професійний фітнес-тренер. 
    Склади тренування для користувача (вага {user_weight} кг).
    Умови: 
    - Локація: {loc_text}
    - Час: {time_val} хвилин
    - Складність: {difficulty}
    
    ДУЖЕ ВАЖЛИВЕ ПРАВИЛО:
    Ти ПОВИНЕН використовувати для поля 'sys_id' вправи ТІЛЬКИ З ЦЬОГО СПИСКУ:
    [{exercises_menu}]
    
    СУВОРО ЗАБОРОНЕНО придумувати свої власні назви для sys_id. Бери їх виключно зі списку вище.
    Поле 'name' переклади на {target_lang}.

    Format EXACTLY like this JSON array:
    [
        {{
            "sys_id": "одне_зі_слів_зі_списку_вище", 
            "name": "Назва мовою {target_lang}", 
            "sets": 3, 
            "reps": 12, 
            "rest_sec": 60, 
            "weight_kg": 50,
            "muscle": "Група м'язів"
        }}
    ]
    """
    
    try:
        response = await model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json"})
        workout_plan = json.loads(response.text)
        
        await state.update_data(workout_plan=workout_plan, current_ex_index=0, current_set=1)
        await state.set_state(WorkoutFSM.active_exercise)
        await send_current_exercise(callback.message, state, user_id, lang)
        
    except Exception as e:
        print(f"Помилка генерації тренування: {e}")
        err_msg = "❌ Ошибка генерации." if lang == "ru" else "❌ Помилка генерації."
        await callback.message.edit_text(err_msg)
        await state.clear()


async def run_rest_timer(message: types.Message, state: FSMContext, user_id: int, lang: str, rest_time: int, builder: InlineKeyboardBuilder, base_text: str):
    step = 5  # Обновляем каждые 5 секунд
    
    for remaining in range(rest_time, 0, -step):
        await asyncio.sleep(step)
        
        # Проверяем, в состоянии ли отдыха юзер (возможно, он уже нажал "Пропустить")
        current_state = await state.get_state()
        if current_state != WorkoutFSM.resting.state:
            return # Тихо убиваем таймер, если юзер пошел дальше
            
        # Мультиязычный текст таймера
        if lang == "ru": time_text = f"\n\n⏳ Осталось: <b>{remaining} сек</b>"
        elif lang == "en": time_text = f"\n\n⏳ Remaining: <b>{remaining} sec</b>"
        elif lang == "kk": time_text = f"\n\n⏳ Қалғаны: <b>{remaining} сек</b>"
        else: time_text = f"\n\n⏳ Залишилось: <b>{remaining} сек</b>"
        
        try:
            await message.edit_text(base_text + time_text, reply_markup=builder.as_markup(), parse_mode="HTML")
        except Exception:
            pass # Игнорируем мелкие ошибки Telegram API при редактировании

    # Если цикл закончился (время вышло) и юзер всё еще отдыхает -> авто-продолжение
    current_state = await state.get_state()
    if current_state == WorkoutFSM.resting.state:
        await state.set_state(WorkoutFSM.active_exercise)
        await send_current_exercise(message, state, user_id, lang)

# === ЕТАП 3: ЯДРО ТРЕНУВАННЯ (FSM) ===

MEDIA_STORAGE_CHANNEL = -1003875495804
async def get_exercise_gif(sys_id: str):
    """
    Шукає гіфку: пам'ять -> Supabase -> Диск.
    Якщо вантажить з диска — зберігає в канал та Supabase.
    """
    if not sys_id:
        return None

    # 1. Перевірка в кеші (словник EXERCISE_GIFS у пам'яті)
    if sys_id in EXERCISE_GIFS:
        return EXERCISE_GIFS[sys_id]

    # 2. Перевірка в Supabase
    try:
        response = supabase.table("exercise_media").select("file_id").eq("sys_id", sys_id).execute()
        if response.data:
            f_id = response.data[0]['file_id']
            EXERCISE_GIFS[sys_id] = f_id # Кешуємо
            return f_id
    except Exception as e:
        print(f"Помилка пошуку в БД для {sys_id}: {e}")

    # 3. Якщо в базі немає — шукаємо фізичний файл у папці
    # Перевіряємо обидва розширення
    for ext in ['.gif', '.mp4']:
        file_path = f"./renamed_videos/{sys_id}{ext}"
        if os.path.exists(file_path):
            try:
                # Відправляємо файл у сховище
                msg = await bot.send_animation(
                    chat_id=MEDIA_STORAGE_CHANNEL, 
                    animation=FSInputFile(file_path)
                )
                new_file_id = msg.animation.file_id
                
                # Зберігаємо в Supabase для наступних разів
                supabase.table("exercise_media").insert({
                    "sys_id": sys_id, 
                    "file_id": new_file_id
                }).execute()
                
                # Кешуємо в пам'ять
                EXERCISE_GIFS[sys_id] = new_file_id
                return new_file_id
            except Exception as e:
                print(f"❌ Помилка завантаження файлу {sys_id}: {e}")
    
    return None

async def background_gif_uploader(message: types.Message, sys_id: str, text: str, builder: InlineKeyboardBuilder, user_id: int):
    print(f"\n⏳ [ФОН] Начинаю искать гифку для: '{sys_id}'")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    videos_dir = os.path.join(base_dir, "renamed_videos")
    
    try:
        # Бот физически читает все файлы, которые реально лежат в папке
        all_files = os.listdir(videos_dir)
    except Exception as e:
        print(f"❌ [ФОН] Не могу открыть папку {videos_dir}. Ошибка: {e}")
        return

    # Ищем первый попавшийся файл, который начинается с нашего sys_id
    target_file = None
    for f in all_files:
        if f.startswith(sys_id):
            target_file = f
            break
            
    if target_file:
        file_path = os.path.join(videos_dir, target_file)
        print(f"✅ [ФОН] Нашел реальный файл на диске: {target_file}")
        
        try:
            # Загружаем в канал
            storage_msg = await bot.send_animation(
                chat_id=MEDIA_STORAGE_CHANNEL, 
                animation=FSInputFile(file_path)
            )
            new_file_id = storage_msg.animation.file_id
            print(f"✅ [ФОН] Успешно загружено. Сохраняю в БД...")
            
            # Сохраняем в Supabase
            supabase.table("exercise_media").insert({
                "sys_id": sys_id, 
                "file_id": new_file_id
            }).execute()
            
            # Сохраняем в наш словарь-кэш, чтобы больше не искать
            EXERCISE_GIFS[sys_id] = new_file_id 
            
            # Отправляем пользователю
            try: await message.delete()
            except: pass
            
            await bot.send_animation(
                chat_id=user_id, 
                animation=new_file_id, 
                caption=text, 
                reply_markup=builder.as_markup(), 
                parse_mode="HTML"
            )
            print(f"🎉 [ФОН] Гифка успешно отправлена юзеру!")
            
        except Exception as e:
            print(f"❌ [ФОН] Ошибка загрузки или БД: {e}")
    else:
        print(f"⚠️ [ФОН] Файл, начинающийся на '{sys_id}', НЕ НАЙДЕН среди {len(all_files)} файлов в папке!")

async def send_current_exercise(message: types.Message, state: FSMContext, user_id: int, lang: str):
    data = await state.get_data()
    plan = data.get("workout_plan", [])
    ex_idx = data.get("current_ex_index", 0)
    curr_set = data.get("current_set", 1)
    
    if ex_idx >= len(plan):
        await finish_workout(message, state, user_id, lang)
        return

    ex = plan[ex_idx]
    weight_kg = ex.get('weight_kg', 0)
    
    # === МАГИЯ СОВПАДЕНИЙ ===
    # Если ИИ прислал кривой sys_id или вообще его забыл, берем name!
    raw_name = ex.get('sys_id') or ex.get('name', 'unknown')
    sys_id = get_clean_sys_id(raw_name) # Очищаем!
    
    print(f"\n▶️ [DEBUG] Сет: {curr_set} | Оригинал: '{raw_name}' -> Шукаємо файл: '{sys_id}'")
    # =======================

    # 1. МИТТЄВА ГЕНЕРАЦІЯ ТЕКСТУ (без змін)
    if lang == "ru":
        name = ex.get('name', 'Без названия')
        text = f"🏋️‍♂️ <b>Упражнение {ex_idx + 1}/{len(plan)}: {name}</b>\n\n"
        text += f"🎯 Подход: <b>{curr_set} из {ex.get('sets', 1)}</b>\n"
        text += f"🔄 Повторения: <b>{ex.get('reps', 1)}</b>\n"
        if weight_kg > 0: text += f"⚖️ Вес снаряда: <b>{weight_kg} кг</b>\n"
        btn_done = f"✅ Выполнено ({ex.get('rest_sec', 60)}с)"
        btn_skip = "⏭ Пропустить"
        btn_stop = "🛑 Завершить"
        btn_edit = "✏️ Изменить вес/повторы"
    elif lang == "en":
        name = ex.get('name', 'Unnamed')
        text = f"🏋️‍♂️ <b>Exercise {ex_idx + 1}/{len(plan)}: {name}</b>\n\n"
        text += f"🎯 Set: <b>{curr_set} of {ex.get('sets', 1)}</b>\n"
        text += f"🔄 Reps: <b>{ex.get('reps', 1)}</b>\n"
        if weight_kg > 0: text += f"⚖️ Weight: <b>{weight_kg} kg</b>\n"
        btn_done = f"✅ Done ({ex.get('rest_sec', 60)}s)"
        btn_skip = "⏭ Skip"
        btn_stop = "🛑 Stop"
        btn_edit = "✏️ Edit weight/reps"
    elif lang == "kk":
        name = ex.get('name', 'Атаусыз')
        text = f"🏋️‍♂️ <b>Жаттығу {ex_idx + 1}/{len(plan)}: {name}</b>\n\n"
        text += f"🎯 Тәсіл: <b>{curr_set} / {ex.get('sets', 1)}</b>\n"
        text += f"🔄 Қайталау: <b>{ex.get('reps', 1)}</b>\n"
        if weight_kg > 0: text += f"⚖️ Салмақ: <b>{weight_kg} кг</b>\n"
        btn_done = f"✅ Орындалды ({ex.get('rest_sec', 60)}с)"
        btn_skip = "⏭ Өткізіп жіберу"
        btn_stop = "🛑 Аяқтау"
        btn_edit = "✏️ Салмақ/қайталауды өзгерту"
    else: # "ua"
        name = ex.get('name', 'Без назви')
        text = f"🏋️‍♂️ <b>Вправа {ex_idx + 1}/{len(plan)}: {name}</b>\n\n"
        text += f"🎯 Підхід: <b>{curr_set} з {ex.get('sets', 1)}</b>\n"
        text += f"🔄 Повторення: <b>{ex.get('reps', 1)}</b>\n"
        if weight_kg > 0: text += f"⚖️ Вага снаряда: <b>{weight_kg} кг</b>\n"
        btn_done = f"✅ Виконано ({ex.get('rest_sec', 60)}с)"
        btn_skip = "⏭ Пропустити"
        btn_stop = "🛑 Завершити"
        btn_edit = "✏️ Змінити вагу/повтори"

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=btn_done, callback_data="wo_set_done"))
    builder.row(types.InlineKeyboardButton(text=btn_edit, callback_data="wo_edit_stats"))

    builder.row(
        types.InlineKeyboardButton(text=btn_skip, callback_data="wo_skip_ex"),
        types.InlineKeyboardButton(text=btn_stop, callback_data="wo_stop")
    )

    # 2. ШВИДКА ПЕРЕВІРКА В БАЗІ / КЕШІ (без завантаження з диска!)
    gif_id = None
    if curr_set == 1 and sys_id:
        if sys_id in EXERCISE_GIFS:
            gif_id = EXERCISE_GIFS[sys_id]
        else:
             # ТІЛЬКИ швидкий запит до БД, без завантаження файлу
            try:
                response = supabase.table("exercise_media").select("file_id").eq("sys_id", sys_id).execute()
                if response.data:
                    gif_id = response.data[0]['file_id']
                    EXERCISE_GIFS[sys_id] = gif_id
            except Exception:
                pass

    # 3. МИТТЄВА ВІДПРАВКА ПОВІДОМЛЕННЯ
    try:
        if curr_set == 1 and gif_id:
             # Якщо гіфка вже є (кеш або БД) - шлемо миттєво з анімацією
            try: await message.delete()
            except: pass
            sent_msg = await bot.send_animation(chat_id=user_id, animation=gif_id, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
             # Якщо гіфки ще немає (або це 2+ сет) - МИТТЄВО оновлюємо текст!
            sent_msg = await message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            
            # А ТЕПЕР ЗАПУСКАЄМО ЗАВАНТАЖЕННЯ ГІФКИ У ФОНІ!
            if curr_set == 1 and sys_id and not gif_id:
                asyncio.create_task(background_gif_uploader(sent_msg, sys_id, text, builder, user_id))
            
    except Exception:
        try: await message.delete()
        except: pass
        sent_msg = await bot.send_message(user_id, text, reply_markup=builder.as_markup(), parse_mode="HTML")
        
        # Запуск фонового завантаження і тут (якщо повідомлення було видалене)
        if curr_set == 1 and sys_id and not gif_id:
            asyncio.create_task(background_gif_uploader(sent_msg, sys_id, text, builder, user_id))


@dp.callback_query(F.data == "wo_set_done", WorkoutFSM.active_exercise)
async def workout_set_done(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer() # 🛑 Миттєво зупиняємо "завантаження" кнопки, щоб уникнути подвійного кліку
    
    # 🛑 Одразу блокуємо повторні кліки, змінюючи стан!
    await state.set_state(WorkoutFSM.resting)
    
    data = await state.get_data()
    plan = data.get("workout_plan", [])
    ex_idx = data.get("current_ex_index", 0)
    curr_set = data.get("current_set", 1)
    
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)

    if ex_idx >= len(plan):
        await finish_workout(callback.message, state, user_id, lang)
        return

    ex = plan[ex_idx]
    
    # Оновлюємо лічильники
    if curr_set >= ex.get('sets', 1):
        await state.update_data(current_ex_index=ex_idx + 1, current_set=1)
        if lang == "ru": rest_text = f"🎉 Упражнение завершено!\n\n⏱ Отдохни {ex.get('rest_sec', 60)} сек перед следующим."
        elif lang == "en": rest_text = f"🎉 Exercise completed!\n\n⏱ Rest {ex.get('rest_sec', 60)} sec before the next one."
        elif lang == "kk": rest_text = f"🎉 Жаттығу аяқталды!\n\n⏱ Келесі жаттығу алдында {ex.get('rest_sec', 60)} сек демалыңыз."
        else: rest_text = f"🎉 Вправу завершено!\n\n⏱ Відпочинь {ex.get('rest_sec', 60)} сек перед наступною."
    else:
        await state.update_data(current_set=curr_set + 1)
        if lang == "ru": rest_text = f"Отличная работа! 👏\n\n⏱ Отдых {ex.get('rest_sec', 60)} секунд."
        elif lang == "en": rest_text = f"Great job! 👏\n\n⏱ Rest {ex.get('rest_sec', 60)} seconds."
        elif lang == "kk": rest_text = f"Керемет жұмыс! 👏\n\n⏱ Демалыс {ex.get('rest_sec', 60)} секунд."
        else: rest_text = f"Чудова робота! 👏\n\n⏱ Відпочинок {ex.get('rest_sec', 60)} секунд."

    if lang == "ru": btn_skip = "⏭ Пропустить отдых"
    elif lang == "en": btn_skip = "⏭ Skip rest"
    elif lang == "kk": btn_skip = "⏭ Демалысты өткізіп жіберу"
    else: btn_skip = "⏭ Пропустити відпочинок"

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=btn_skip, callback_data="wo_skip_rest"))
    
    # 🛑 ВИПРАВЛЕННЯ ДУБЛЮВАННЯ: Намагаємося змінити поточне повідомлення замість видалення
    try:
        sent_msg = await callback.message.edit_text(rest_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    except Exception:
        # Якщо це була GIF-ка, edit_text видасть помилку. Тоді жорстко видаляємо і надсилаємо текст.
        try: await callback.message.delete()
        except: pass
        sent_msg = await callback.message.answer(rest_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    
    rest_sec = ex.get('rest_sec', 60)
    asyncio.create_task(run_rest_timer(sent_msg, state, user_id, lang, rest_sec, builder, rest_text))


@dp.callback_query(F.data == "wo_skip_rest", WorkoutFSM.resting)
async def workout_skip_rest(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WorkoutFSM.active_exercise)
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    await send_current_exercise(callback.message, state, user_id, lang)
    await callback.answer()


@dp.callback_query(F.data == "wo_skip_ex", WorkoutFSM.active_exercise)
async def workout_skip_ex(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    ex_idx = data.get("current_ex_index", 0)
    await state.update_data(current_ex_index=ex_idx + 1, current_set=1)
    
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    await send_current_exercise(callback.message, state, user_id, lang)
    await callback.answer()


@dp.callback_query(F.data == "wo_stop")
async def workout_stop(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    await finish_workout(callback.message, state, user_id, lang, forced=True)
    await callback.answer()


# === ЕТАП 4: ФІНАЛІЗАЦІЯ ТА СИНХРОНІЗАЦІЯ З WEB APP ===

import re

async def finish_workout(message: types.Message, state: FSMContext, user_id: int, lang: str, forced=False):
    data = await state.get_data()
    plan = data.get("workout_plan", [])
    ex_idx = data.get("current_ex_index", 0)
    
    completed_plan = plan[:ex_idx] if forced else plan
    
    def safe_int(val):
        if isinstance(val, int) or isinstance(val, float): return int(val)
        nums = re.findall(r'\d+', str(val))
        return int(nums[0]) if nums else 0

    total_cals = 0
    for ex in completed_plan:
        sets = safe_int(ex.get('sets', 0))
        reps = safe_int(ex.get('reps', 0))
        weight = safe_int(ex.get('weight_kg', 0))
        cals = sets * reps * 0.5 
        total_cals += cals
        
        supabase.table("workouts_strength").insert({
            "user_id": user_id,
            "exercise_name": f"🤖 {ex.get('name', 'Упражнение')}",
            "sets": sets,
            "reps": reps,
            "weight_kg": weight,
            "muscle_group": ex.get('muscle', 'core'),
            "calories_burned": int(cals)
        }).execute()
    
    # Начисляем XP
    res = supabase.table("users").select("xp").eq("user_id", user_id).execute()
    if res.data:
        current_xp = res.data[0].get("xp", 0)
        supabase.table("users").update({"xp": current_xp + 100}).eq("user_id", user_id).execute()

    # === ФОРМИРУЕМ ТЕКСТ И КНОПКИ ===
    if lang == "ru":
        text = f"🎉 <b>Тренировка завершена!</b>\nСожжено: ~{int(total_cals)} ккал." if not forced else f"🛑 <b>Тренировка прервана</b>\nСохранено ~{int(total_cals)} ккал."
        btn_save = "💾 Сохранить программу"
        btn_close = "🏠 Закрыть"
    elif lang == "en":
        text = f"🎉 <b>Workout completed!</b>\nBurned: ~{int(total_cals)} kcal." if not forced else f"🛑 <b>Workout aborted</b>\nSaved ~{int(total_cals)} kcal."
        btn_save = "💾 Save program"
        btn_close = "🏠 Close"
    elif lang == "kk":
        text = f"🎉 <b>Жаттығу аяқталды!</b>\nЖағылды: ~{int(total_cals)} ккал." if not forced else f"🛑 <b>Жаттығу тоқтатылды</b>\nСақталды ~{int(total_cals)} ккал."
        btn_save = "💾 Бағдарламаны сақтау"
        btn_close = "🏠 Жабу"
    else:
        text = f"🎉 <b>Тренування завершено!</b>\nСпалено: ~{int(total_cals)} ккал." if not forced else f"🛑 <b>Тренування перервано</b>\nЗбережено ~{int(total_cals)} ккал."
        btn_save = "💾 Зберегти програму"
        btn_close = "🏠 Закрити"
        
    builder = InlineKeyboardBuilder()
    
    # Предлагаем сохранить только если юзер не нажал "Завершить" принудительно
    if not forced:
        builder.row(types.InlineKeyboardButton(text=btn_save, callback_data="wo_ask_save_name"))
        
    builder.row(types.InlineKeyboardButton(text=btn_close, callback_data="wo_close_clear"))

    try: await message.delete()
    except: pass
    
    await bot.send_message(user_id, text, reply_markup=builder.as_markup(), parse_mode="HTML")
    
    # Если тренировка прервана жестко, чистим память сразу, иначе оставляем висеть для сохранения
    if forced:
        await state.clear()


# 1. Если юзер нажал "Закрыть" - просто чистим память
@dp.callback_query(F.data == "wo_close_clear")
async def workout_close_clear(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try: await callback.message.delete()
    except: pass
    await callback.answer()

# 2. Если юзер нажал "Сохранить" - просим ввести имя
@dp.callback_query(F.data == "wo_ask_save_name")
async def workout_ask_save_name(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    if lang == "ru": msg = "📝 Введите название для этой тренировки\n(например: <i>Грудь и спина от ИИ</i>):"
    elif lang == "en": msg = "📝 Enter a name for this workout\n(e.g., <i>AI Chest & Back</i>):"
    elif lang == "kk": msg = "📝 Бұл жаттығуға атау енгізіңіз\n(мысалы: <i>ЖИ кеуде және арқа</i>):"
    else: msg = "📝 Введіть назву для цього тренування\n(наприклад: <i>Груди та спина від ШІ</i>):"

    await callback.message.edit_text(msg, parse_mode="HTML")
    await state.set_state(WorkoutFSM.waiting_for_save_name)

# 3. Юзер ввел имя - сохраняем JSON в базу



@dp.callback_query(F.data == "workout_saved", WorkoutFSM.choosing_type)
async def list_saved_programs(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Завантажуємо програми користувача з БД
    res = supabase.table("saved_programs").select("id", "title").eq("user_id", user_id).execute()
    
    if not res.data:
        msg = "У вас ще немає збережених програм." if lang != "en" else "You don't have any saved programs yet."
        await callback.answer(msg, show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for prog in res.data:
        builder.row(types.InlineKeyboardButton(text=f"📋 {prog['title']}", callback_data=f"run_prog_{prog['id']}"))
    
    back_text = "🔙 Назад" if lang != "en" else "🔙 Back"
    builder.row(types.InlineKeyboardButton(text=back_text, callback_data="workout_start_menu")) # Повернення в меню вибору
    
    title_text = "Оберіть програму:" if lang != "en" else "Choose a program:"
    await callback.message.edit_text(title_text, reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("run_prog_"), WorkoutFSM.choosing_type)
async def start_saved_program(callback: types.CallbackQuery, state: FSMContext):
    prog_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Дістаємо текст програми
    res = supabase.table("saved_programs").select("*").eq("id", prog_id).single().execute()
    if not res.data: return

    program_data = res.data
    # ТУТ ВАЖЛИВО: Оскільки в БД текст, ми просимо Gemini швидко перетворити його на JSON для движка
    wait_msg = "⏱ Завантаження програми..." if lang != "en" else "⏱ Loading program..."
    await callback.message.edit_text(wait_msg)
    
    prompt = f"Convert this workout text into a JSON array of exercises with 'name', 'sets', 'reps', 'rest_sec', 'muscle'. Text: {program_data['content']}"
    
    try:
        response = await model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json"})
        workout_plan = json.loads(response.text)
        
        await state.update_data(workout_plan=workout_plan, current_ex_index=0, current_set=1)
        await state.set_state(WorkoutFSM.active_exercise)
        await send_current_exercise(callback.message, state, user_id, lang)
    except Exception as e:
        print(f"Error parsing saved program: {e}")
        await callback.message.answer("Помилка завантаження. Спробуйте іншу програму.")

@dp.callback_query(F.data == "workout_start_menu")
async def back_to_workout_menu(callback: types.CallbackQuery, state: FSMContext):
    await start_workout_mode(callback.message, state)

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

@dp.callback_query(F.data.startswith("check_crypto_"))
async def check_crypto_payment(callback: types.CallbackQuery):
    invoice_id = int(callback.data.split("_")[-1])
    invoices = await crypto.get_invoices(invoice_ids=invoice_id)
    
    inv_list = invoices if isinstance(invoices, list) else getattr(invoices, 'items', [invoices])
    
    if inv_list and any(inv.status == 'paid' for inv in inv_list):
        # ОПЛАТА УСПІШНА -> ДАЄМО БЕЗЛІМІТ (9999)
        supabase.table("users").update({
            "balance": 9999,
            "ai_generations": 9999
        }).eq("user_id", callback.from_user.id).execute()
        
        await callback.message.answer("🎉 Оплата USDT отримана! Вам активовано Безліміт 👑 на місяць.")
        await callback.answer()
    else:
        await callback.answer("❌ Оплата ще не надійшла.", show_alert=True)

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
    
    asyncio.create_task(process_ai_requests()) 
    await dp.start_polling(bot)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily_reminder_task, 'cron', hour=21, minute=0) # Каждый день в 21:00
    scheduler.start()

    asyncio.create_task(process_ai_requests())
    await dp.start_polling(bot)

if __name__ == "__main__": asyncio.run(main())
