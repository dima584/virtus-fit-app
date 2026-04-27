from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.web_app_info import WebAppInfo

def get_main_menu_with_app(lang: str, get_text_func, user_id):
    # 1. Достаем переведенный текст для кнопки Web App
    web_app_text = get_text_func(lang, "web_app_btn")
    
    # 2. Формируем клавиатуру
    builder = ReplyKeyboardBuilder()
    
    # Ряд 1: Большая кнопка Web App на всю ширину сверху
    builder.row(KeyboardButton(
        text=web_app_text, 
        web_app=WebAppInfo(url=f"https://dima584.github.io/virtus-fit-app/?user_id={user_id}") 
    ))

    # Ряд 2: НОВАЯ КНОПКА ТРЕНИРОВКИ (тоже на всю ширину для акцента)
    builder.row(
        types.KeyboardButton(text=get_text_func(lang, "workout_start"))
    )

    # Ряд 3
    builder.row(
        types.KeyboardButton(text=get_text_func(lang, "food_analysis")), 
        types.KeyboardButton(text=get_text_func(lang, "nutrition"))
    )
    
    # Ряд 4
    builder.row(
        types.KeyboardButton(text=get_text_func(lang, "balance")), 
        types.KeyboardButton(text=get_text_func(lang, "ai_chat"))
    )
    
    # Ряд 5
    builder.row(
        types.KeyboardButton(text=get_text_func(lang, "account")), 
        types.KeyboardButton(text=get_text_func(lang, "support"))
    )
    
    # Ряд 6
    builder.row(
        types.KeyboardButton(text=get_text_func(lang, "referral")), 
        types.KeyboardButton(text=get_text_func(lang, "subscription"))
    )
    
    # Получаем перевод для поля ввода
    placeholder_text = get_text_func(lang, "input_placeholder")
    
    # Возвращаем клавиатуру
    return builder.as_markup(
        resize_keyboard=True, 
        input_field_placeholder=placeholder_text
    )
