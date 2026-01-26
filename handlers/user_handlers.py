from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import user_keyboards as kb
from database import db
from config import WORKERS, SUPER_ADMINS
from translations import STRINGS
STR_UZ = STRINGS['uz']
STR_RU = STRINGS['ru']
STR_EN = STRINGS['en']

router = Router()

class OrderState(StatesGroup):
    phone = State()
    method = State()
    location = State()
    confirm = State()

# Temporary basket storage
user_basket = {}

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("🇺🇿 Iltimos, tilni tanlang:\n🇷🇺 Пожалуйста, выберите язык:\n🇺🇸 Please select a language:", reply_markup=kb.lang_keyboard())

@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    db.set_user_lang(user_id, lang)
    
    is_admin = user_id in (SUPER_ADMINS + WORKERS)
    s = STRINGS[lang]
    await callback.message.edit_text(s['welcome'].format(name=callback.from_user.full_name))
    await callback.message.answer(".", reply_markup=kb.main_menu(lang, is_admin))
    await callback.answer()

from keyboards import admin_keyboards as akb

@router.message(F.text == "🛠 Admin Panel")
async def show_admin_menu(message: types.Message):
    user_id = message.from_user.id
    if user_id in (SUPER_ADMINS + WORKERS):
        is_super = user_id in SUPER_ADMINS
        # Update the reply keyboard first to clean up the UI
        await message.answer("🏠 Siz hozir Admin menyusidasiz.", reply_markup=akb.admin_reply_menu())
        # Then send the actual dashboard
        await message.answer("⚒ Boshqaruv elementlari:", reply_markup=akb.admin_profile_kb(is_super=is_super))

@router.message(F.text == "🏠 Foydalanuvchi menyusi")
async def back_to_user_menu(message: types.Message):
    lang = db.get_user_lang(message.from_user.id)
    await message.answer("🏠 Foydalanuvchi menyusiga qaytdingiz.", reply_markup=kb.main_menu(lang, is_admin=True))

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

@router.callback_query(F.data == "confirm_order")
async def confirm_order(callback: types.CallbackQuery, state: FSMContext):
    lang = db.get_user_lang(callback.from_user.id)
    s = STRINGS[lang]
    await state.set_state(OrderState.phone)
    await callback.message.answer(s['phone_req'], reply_markup=kb.phone_keyboard(lang))
    await callback.answer()

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
    user_id = message.from_user.id
    
    if message.text in [STR_UZ['method_delivery'], STR_RU['method_delivery'], STR_EN['method_delivery']]:
        await state.update_data(method='delivery')
        await state.set_state(OrderState.location)
        await message.answer(s['location_req'], reply_markup=kb.location_keyboard(lang))
    elif message.text in [STR_UZ['method_takeaway'], STR_RU['method_takeaway'], STR_EN['method_takeaway']]:
        await state.update_data(method='takeaway', location="O'zi olib ketadi", maps_url=None)
        
        # Calculate summary immediately for takeaway
        items = user_basket.get(user_id, [])
        if not items:
            await message.answer("Error: Basket is empty.")
            await state.clear()
            return
            
        total_price = sum(i['price'] * i['quantity'] for i in items)
        items_str = "\n".join([f"- {i['name']} x {i['quantity']}" for i in items])
        
        await state.update_data(total_price=total_price, items_str=items_str)
        
        method_text = s['method_takeaway'] + " " + s['takeaway_label']
        confirm_text = s['confirm_summary'].format(
            items=items_str, 
            method=method_text,
            location="N/A", 
            total=total_price
        )
        
        await state.set_state(OrderState.confirm)
        await message.answer(confirm_text, reply_markup=kb.order_confirm_kb(lang), parse_mode="Markdown")
    else:
        await message.answer(s['method_req'], reply_markup=kb.delivery_method_kb(lang))

@router.message(OrderState.location)
async def get_location(message: types.Message, state: FSMContext):
    lang = db.get_user_lang(message.from_user.id)
    s = STRINGS[lang]
    user_id = message.from_user.id
    items = user_basket.get(user_id, [])
    
    if not items:
        await message.answer("Error: Basket is empty.")
        await state.clear()
        return

    if message.location:
        location_str = f"📍 ({message.location.latitude}, {message.location.longitude})"
        maps_url = f"https://www.google.com/maps?q={message.location.latitude},{message.location.longitude}"
    else:
        location_str = message.text
        maps_url = message.text

    total_price = sum(i['price'] * i['quantity'] for i in items)
    
    user_data = await state.get_data()
    method = user_data.get('method', 'delivery')
    
    if method == 'delivery':
        # total_price += 0 # Delivery is free for now
        method_text = s['method_delivery'] + " " + s['delivery_fee_label']
    else:
        method_text = s['method_takeaway'] + " " + s['takeaway_label']
    
    items_str = "\n".join([f"- {i['name']} x {i['quantity']}" for i in items])
    await state.update_data(location=location_str, maps_url=maps_url, total_price=total_price, items_str=items_str)

    confirm_text = s['confirm_summary'].format(
        items=items_str, 
        method=method_text,
        location=location_str, 
        total=total_price
    )

    await state.set_state(OrderState.confirm)
    await message.answer(confirm_text, reply_markup=kb.order_confirm_kb(lang), parse_mode="Markdown")

@router.callback_query(OrderState.confirm, F.data == "user_confirm")
async def finalize_order(callback: types.CallbackQuery, state: FSMContext):
    lang = db.get_user_lang(callback.from_user.id)
    s = STRINGS[lang]
    data = await state.get_data()
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name
    user_username = f"@{callback.from_user.username}" if callback.from_user.username else "Noma'lum"
    
    order_id = db.create_order(user_id, data['items_str'], data['total_price'], data['location'])
    db.add_user(user_id, user_name, data['phone'])

    await callback.message.edit_text(s['order_received'].format(id=order_id))
    
    # Notify Admin (Worker)
    admin_msg = f"🆕 Yangi buyurtma #{order_id}!\n\n"
    admin_msg += f"👤 Mijoz: {user_name}\n"
    admin_msg += f"🆔 Nickname: [{user_username}](tg://user?id={user_id})\n"
    admin_msg += f"📞 Tel: {data['phone']}\n"
    
    method_str = "🛵 Kuryer orqali" if data.get('method') == 'delivery' else "🏃 O'zi boradi (Self-pickup)"
    admin_msg += f"🛒 Usul: {method_str}\n"
    
    admin_msg += f"📍 Manzil: {data['maps_url'] if data.get('maps_url') else 'N/A (O\'zim boraman)'}\n\n"
    admin_msg += f"🧾 Taomlar:\n{data['items_str']}\n\n"
    admin_msg += f"💰 Jami: {data['total_price']:,} so'm"

    from keyboards.admin_keyboards import order_initial_kb
    for worker_id in WORKERS:
        try:
            await callback.bot.send_message(worker_id, admin_msg, reply_markup=order_initial_kb(order_id), parse_mode="Markdown")
        except:
            pass

    user_basket[user_id] = []
    await state.clear()
    await callback.answer()

@router.callback_query(OrderState.confirm, F.data == "user_cancel")
async def cancel_order(callback: types.CallbackQuery, state: FSMContext):
    lang = db.get_user_lang(callback.from_user.id)
    s = STRINGS[lang]
    await state.clear()
    await callback.message.edit_text(s['order_cancelled'])
    await callback.message.answer(".", reply_markup=kb.main_menu(lang))
    await callback.answer()

@router.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def web_app_data_handler(message: types.Message, state: FSMContext):
    import json
    data = json.loads(message.web_app_data.data)
    lang = db.get_user_lang(message.from_user.id)
    s = STRINGS[lang]
    
    if data.get('type') == 'order':
        user_basket[message.from_user.id] = data.get('items', [])
        await state.set_state(OrderState.phone)
        await message.answer(s['phone_req'], reply_markup=kb.phone_keyboard(lang))
