from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from translations import STRINGS

def lang_keyboard():
    kb = [
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def main_menu(lang='uz', is_admin=False):
    s = STRINGS[lang]
    url = f"https://khamidovkhusnidd1n.github.io/Yummy/?lang={lang}"
    
    kb = [
        [KeyboardButton(text=s['main_menu_btn'], web_app=WebAppInfo(url=url))],
        [KeyboardButton(text=s['location_btn_menu']), KeyboardButton(text=s['about_btn_menu'])],
        [KeyboardButton(text=s['contact_btn_menu']), KeyboardButton(text=s['feedback_btn_menu'])]
    ]
    
    if is_admin:
        kb.append([KeyboardButton(text="🛠 Admin Panel")])
        
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def phone_keyboard(lang='uz'):
    s = STRINGS[lang]
    kb = [[KeyboardButton(text=s['phone_btn'], request_contact=True)]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def delivery_method_kb(lang='uz'):
    s = STRINGS[lang]
    kb = [
        [KeyboardButton(text=s['method_delivery'])],
        [KeyboardButton(text=s['method_takeaway'])]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def location_keyboard(lang='uz'):
    s = STRINGS[lang]
    kb = [[KeyboardButton(text=s['location_btn'], request_location=True)]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def order_confirm_kb(lang='uz'):
# ... existing code ...

def promo_skip_kb(lang='uz'):
    s = STRINGS[lang]
    kb = [[InlineKeyboardButton(text=s.get('skip_btn', 'Skip ➡️'), callback_data="skip_promo")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)
