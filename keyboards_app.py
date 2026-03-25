from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.web_app_info import WebAppInfo

def get_main_menu_with_app(lang: str, get_text_func, user_id):
    # 1. Дістаємо перекладений текст для кнопки Web App (ВИПРАВЛЕНО НА get_text_func)
    web_app_text = get_text_func(lang, "web_app_btn")
    
    # 2. Формуємо клавіатуру
    builder = ReplyKeyboardBuilder()
    
    # Велика кнопка Web App на всю ширину зверху
    builder.row(KeyboardButton(
        text=web_app_text, 
        # Не забудь перевірити, чи правильне тут посилання на твій GitHub!
        web_app=WebAppInfo(url=f"https://dima584.github.io/virtus-fit-app/?user_id={user_id}") 
    ))

    builder.row(
        types.KeyboardButton(text=get_text_func(lang, "food_analysis")), 
        types.KeyboardButton(text=get_text_func(lang, "nutrition"))
    )
    # Ряд 3
    builder.row(
        types.KeyboardButton(text=get_text_func(lang, "balance")), 
        types.KeyboardButton(text=get_text_func(lang, "ai_chat"))
    )
    # Ряд 4
    builder.row(
        types.KeyboardButton(text=get_text_func(lang, "account")), 
        types.KeyboardButton(text=get_text_func(lang, "support"))
    )
    # Ряд 5
    builder.row(
        types.KeyboardButton(text=get_text_func(lang, "referral")), 
        types.KeyboardButton(text=get_text_func(lang, "subscription"))
    )
    
    # Отримуємо переклад для поля вводу
    placeholder_text = get_text_func(lang, "input_placeholder")
    
    # Повертаємо клавіатуру з новим текстом у полі вводу
    return builder.as_markup(
        resize_keyboard=True, 
        input_field_placeholder=placeholder_text
    )