from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import user_keyboards as kb
from database import db
from config import WORKERS, SUPER_ADMINS
from handlers.admin_handlers import build_admin_dashboard_text
from translations import STRINGS
import json

STR_UZ = STRINGS['uz']
STR_RU = STRINGS['ru']
STR_EN = STRINGS['en']

router = Router()

class OrderState(StatesGroup):
    phone = State()
    method = State()
    confirm = State()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    # Auto-initialize menu if empty (critical for first run)
    if not db.get_all_categories():
        try:
            from init_menu import init_menu
            init_menu()
            print("Menu initialized via /start command")
        except Exception as e:
            print(f"Menu init failed: {e}")
    
    await message.answer("🇺🇿 Iltimos, tilni tanlang:\n🇷🇺 Пожалуйста, выберите язык:\n🇺🇸 Please select a language:", reply_markup=kb.lang_keyboard())

@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    db.set_user_lang(user_id, lang)
    
    is_admin = bool(db.get_admin(user_id))
    s = STRINGS[lang]
    await callback.message.delete()
    await callback.message.answer(s['welcome'].format(name=callback.from_user.full_name), reply_markup=kb.main_menu(lang, is_admin), parse_mode="Markdown")
    await callback.answer()

from keyboards import admin_keyboards as akb

@router.message(F.text == "🛠 Admin Panel")
async def show_admin_menu(message: types.Message):
    user_id = message.from_user.id
    admin = db.get_admin(user_id)
    if admin:
        is_super = admin[1] == 'super_admin'
        await message.answer(
            "Siz hozir Admin menyusidasiz.\n\nBoshqaruv tugmalari pastda paydo bo'ldi.", 
            reply_markup=akb.admin_reply_menu(is_super)
        )

@router.message(F.text == "🏠 Foydalanuvchi menyusi")
async def back_to_user_menu(message: types.Message):
    user_id = message.from_user.id
    lang = db.get_user_lang(user_id)
    is_admin = (user_id in (SUPER_ADMINS + WORKERS)) and bool(db.get_admin(user_id))
    await message.answer("🏠 Foydalanuvchi menyusiga qaytdingiz.", reply_markup=kb.main_menu(lang, is_admin))

@router.message(F.text.in_([STR_UZ['location_btn_menu'], STR_RU['location_btn_menu'], STR_EN['location_btn_menu']]))
async def show_location(message: types.Message):
    lang = db.get_user_lang(message.from_user.id)
    s = STRINGS[lang]
    await message.answer(s['location_info'], parse_mode="Markdown")

@router.message(F.text.in_([STR_UZ['about_btn_menu'], STR_RU['about_btn_menu'], STR_EN['about_btn_menu']]))
async def show_about(message: types.Message):
    lang = db.get_user_lang(message.from_user.id)
    s = STRINGS[lang]
    await message.answer(s['about_info'], parse_mode="Markdown")

@router.message(F.text.in_([STR_UZ['contact_btn_menu'], STR_RU['contact_btn_menu'], STR_EN['contact_btn_menu']]))
async def show_contact(message: types.Message):
    lang = db.get_user_lang(message.from_user.id)
    s = STRINGS[lang]
    await message.answer(s['contact_info'], parse_mode="Markdown")

@router.message(F.text.in_([STR_UZ['feedback_btn_menu'], STR_RU['feedback_btn_menu'], STR_EN['feedback_btn_menu']]))
async def show_feedback(message: types.Message):
    lang = db.get_user_lang(message.from_user.id)
    s = STRINGS[lang]
    await message.answer(s['feedback_info'], parse_mode="Markdown")

@router.message(OrderState.phone, F.contact)
async def get_phone(message: types.Message, state: FSMContext):
    lang = db.get_user_lang(message.from_user.id)
    s = STRINGS[lang]
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(OrderState.method)
    await message.answer(s['method_req'], reply_markup=kb.delivery_method_kb(lang))

@router.message(OrderState.method)
async def get_method(message: types.Message, state: FSMContext):
    lang = db.get_user_lang(message.from_user.id)
    s = STRINGS[lang]
    
    if message.text in [STR_UZ['method_delivery'], STR_RU['method_delivery'], STR_EN['method_delivery']]:
        # Location is already in WebApp payload, so just proceed
        await state.update_data(method='delivery')
        await show_order_summary(message, state)
            
    elif message.text in [STR_UZ['method_takeaway'], STR_RU['method_takeaway'], STR_EN['method_takeaway']]:
        await state.update_data(method='takeaway', location="O'zi olib ketadi", maps_url=None)
        await show_order_summary(message, state)
    else:
        await message.answer(s['method_req'], reply_markup=kb.delivery_method_kb(lang))

async def show_order_summary(message: types.Message, state: FSMContext):
    """Show order confirmation summary"""
    user_id = message.from_user.id
    lang = db.get_user_lang(user_id)
    s = STRINGS[lang]
    data = await state.get_data()
    
    discount_percent = data.get('discount_percent', 0)

    items_json = db.get_cart(user_id)
    if not items_json:
        await message.answer("Xatolik: Savat bo'sh.")
        await state.clear()
        return
        
    items = json.loads(items_json)
    subtotal = sum(i['price'] * i['quantity'] for i in items)
    items_str = "\n".join([f"- {i['name']} x {i['quantity']}" for i in items])
    
    discount_amount = int(subtotal * (discount_percent / 100))
    total = subtotal - discount_amount
    
    await state.update_data(total_price=total, items_str=items_str, discount_amount=discount_amount)

    method_text = s['method_delivery'] if data.get('method') == 'delivery' else s['method_takeaway']
    
    confirm_text = s['confirm_summary'].format(
        items=items_str, 
        method=method_text,
        location=data.get('location', 'N/A'), 
        total=total
    )
    
    if discount_percent > 0:
        confirm_text += f"\n🎟 **Promo:** {data.get('promo_code')} (-{discount_percent}%)"

    await state.set_state(OrderState.confirm)
    await message.answer(confirm_text, reply_markup=kb.order_confirm_kb(lang), parse_mode="Markdown")

@router.message(OrderState.confirm)
async def process_confirm(message: types.Message, state: FSMContext):
    lang = db.get_user_lang(message.from_user.id)
    s = STRINGS[lang]
    
    if message.text == s['confirm_btn']:
        data = await state.get_data()
        user_id = message.from_user.id
        user_name = message.from_user.full_name
        user_username = f"@{message.from_user.username}" if message.from_user.username else "Noma'lum"
        
        # Determine location string
        final_location = data.get('location') or "Manzil kiritilmagan"
        
        order_id = db.create_order(
            user_id=user_id,
            items=data['items_str'],
            total_price=data['total_price'],
            promo_code=data.get('promo_code_from_app'),
            discount_amount=data.get('discount_amount', 0),
            method=data.get('method'),
            location=final_location
        )
        db.add_user(user_id, user_name, user_username, data.get('phone', 'N/A'))

        # Notify User & Return to Main Menu immediately
        is_admin = bool(db.get_admin(user_id))
        
        # Clear state FIRST
        await state.clear()
        
        await message.answer(
            s['order_received'].format(id=order_id), 
            reply_markup=kb.main_menu(lang, is_admin)
        )
        
        # Notify Admin (Worker)
        admin_msg = f"🆕 Yangi buyurtma #{order_id}!\n\n"
        admin_msg += f"👤 Mijoz: {user_name}\n"
        admin_msg += f"🆔 Nickname: [{user_username}](tg://user?id={user_id})\n"
        admin_msg += f"📞 Tel: {data.get('phone', 'N/A')}\n"
        
        if data.get('promo_code_from_app'):
            admin_msg += f"🎟 Promo: {data['promo_code_from_app']}\n"

        method_str = "🛵 Kuryer orqali" if data.get('method') == 'delivery' else "🏃 O'zi boradi (Self-pickup)"
        admin_msg += f"🛒 Usul: {method_str}\n"
        
        location_display = final_location
        if data.get('maps_url'):
            location_display = f"[{final_location}]({data['maps_url']})"
            
        admin_msg += f"📍 Manzil: {location_display}\n\n"
        admin_msg += f"🧾 Taomlar:\n{data['items_str']}\n\n"
        admin_msg += f"💰 Jami: {data['total_price']:,} so'm"

        from keyboards.admin_keyboards import order_initial_kb
        for worker_id in WORKERS:
            try:
                await message.bot.send_message(worker_id, admin_msg, reply_markup=order_initial_kb(order_id), parse_mode="Markdown")
            except:
                pass

        db.clear_cart(user_id)
        
    elif message.text == s['cancel_btn']:
        await state.clear()
        is_admin = bool(db.get_admin(message.from_user.id))
        await message.answer(s['order_cancelled'], reply_markup=kb.main_menu(lang, is_admin))

@router.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def web_app_data_handler(message: types.Message, state: FSMContext):
    data = json.loads(message.web_app_data.data)
    user_id = message.from_user.id
    lang = db.get_user_lang(user_id)
    s = STRINGS[lang]
    
    if data.get('type') == 'order':
        items = data.get('items', [])
        db.update_cart(user_id, json.dumps(items))
        
        promo_code = data.get('promo_code', '').strip().upper()
        discount_percent = 0
        
        # Validate promo code from database
        if promo_code:
            promo = db.get_promo_code(promo_code)
            if promo:
                discount_percent = promo[2]  # discount percentage from DB
        
        await state.update_data(
            promo_code_from_app=promo_code if promo_code else None,
            promo_code=promo_code if promo_code else None,
            discount_percent=discount_percent
        )
        
        # Save address and coordinates from WebApp
        location_str = data.get('address', '')
        coords = data.get('coords')
        maps_url = None
        
        if coords:
            lat, lng = coords.get('lat'), coords.get('lng')
            maps_url = f"https://www.google.com/maps?q={lat},{lng}"
            
        await state.update_data(
            location=location_str,
            maps_url=maps_url
        )

        await state.set_state(OrderState.phone)
        await message.answer(s['phone_req'], reply_markup=kb.phone_keyboard(lang))
