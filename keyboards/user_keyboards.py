from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardRemove
from translations import STRINGS
from database import db
import json
import base64

def lang_keyboard():
    kb = [
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def main_menu(lang='uz', is_admin=False):
    s = STRINGS[lang]
    
    # Fetch active promo codes from DB to sync with WebApp
    active_promos = db.get_all_promo_codes()
    promo_map = {p[1].upper(): {"discount": p[2], "active": bool(p[3])} for p in active_promos if p[3]}
    promo_data = base64.b64encode(json.dumps(promo_map).encode()).decode()
    
    url = f"https://khamidovkhusnidd1n.github.io/Yummy/?lang={lang}&p={promo_data}&v=20260128_1258"
    
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
    """Users enter location manually - no location button"""
    return ReplyKeyboardRemove()
def order_confirm_kb(lang='uz'):
    s = STRINGS[lang]
    kb = [
        [KeyboardButton(text=s['confirm_btn'])],
        [KeyboardButton(text=s['cancel_btn'])]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def main_menu_button_kb(lang='uz'):
    s = STRINGS[lang]
    kb = [[KeyboardButton(text=s['main_menu_btn'])]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)




