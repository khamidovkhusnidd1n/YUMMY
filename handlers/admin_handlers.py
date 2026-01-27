from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
import asyncio
from keyboards.admin_keyboards import (
    order_initial_kb, order_next_stage_kb, menu_manage_kb, 
    promo_manage_kb, mailing_kb, cancel_kb, category_list_kb, product_list_kb,
    admin_profile_kb, menu_manage_reply_kb
)
from config import SUPER_ADMINS, ALL_ADMINS, WORKERS
from translations import STRINGS
import os

class AdminStates(StatesGroup):
    # Product States
    adding_product_name = State()
    adding_product_price = State()
    adding_product_image = State()
    
    editing_price_value = State()
    
    # Promo States
    adding_promo_code = State()
    adding_promo_discount = State()
    
    # Mailing States
    mailing_content = State()
    mailing_preview = State()

router = Router()

STATUS_LABELS = [
    ("pending", "Kutilmoqda"),
    ("accepted", "Qabul qilingan"),
    ("preparing", "Tayyorlanmoqda"),
    ("delivering", "Yetkazilmoqda"),
    ("completed", "Yakunlangan"),
    ("rejected", "Rad etilgan"),
]
STATUS_LABEL_MAP = {key: label for key, label in STATUS_LABELS}


def _get_order_status_counts():
    rows = db.cursor.execute("SELECT status, COUNT(*) FROM orders GROUP BY status").fetchall()
    return {status: count for status, count in rows}


def _format_datetime(value):
    if not value:
        return "N/A"
    text = str(value)
    return text[:19] if len(text) > 19 else text


def build_admin_dashboard_text(user_id):
    d_orders, d_rev = db.get_daily_stats()
    t_orders, t_rev = db.get_stats()
    counts = _get_order_status_counts()
    active_count = sum(counts.get(key, 0) for key, _ in STATUS_LABELS[:4])
    total_admins = len(set(ALL_ADMINS))
    super_count = len(set(SUPER_ADMINS))
    worker_count = len(set(WORKERS))
    role = "Super admin" if user_id in SUPER_ADMINS else "Admin"

    text = "*Admin Dashboard*\n"
    text += f"Rol: {role}\n"
    text += f"Adminlar: jami {total_admins} (Super: {super_count}, Worker: {worker_count})\n\n"
    text += "Bugun:\n"
    text += f"- Buyurtmalar: {d_orders}\n"
    text += f"- Tushum: {d_rev:,} so'm\n\n"
    text += "Umumiy:\n"
    text += f"- Buyurtmalar: {t_orders}\n"
    text += f"- Tushum: {t_rev:,} so'm\n\n"
    text += f"Faol buyurtmalar: {active_count}\n"
    text += "Holat bo'yicha:\n"
    for status, label in STATUS_LABELS:
        text += f"- {label}: {counts.get(status, 0)}\n"

    return text


@router.callback_query(F.data == "admin_dashboard", F.from_user.id.in_(ALL_ADMINS))
@router.callback_query(F.data == "admin_dashboard_home", F.from_user.id.in_(ALL_ADMINS))
async def admin_dashboard_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_super = user_id in SUPER_ADMINS
    text = build_admin_dashboard_text(user_id)
    await callback.message.edit_text(text, reply_markup=admin_profile_kb(is_super), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "admin_orders", F.from_user.id.in_(ALL_ADMINS))
async def admin_orders_callback(callback: types.CallbackQuery):
    counts = _get_order_status_counts()
    active_count = sum(counts.get(key, 0) for key, _ in STATUS_LABELS[:4])
    rows = db.cursor.execute(
        "SELECT order_id, total_price, status, created_at FROM orders ORDER BY created_at DESC LIMIT ?",
        (10,),
    ).fetchall()

    text = "*Buyurtmalar monitoringi*\n\n"
    text += f"Faol: {active_count}\n"
    text += f"Yakunlangan: {counts.get('completed', 0)}\n"
    text += f"Rad etilgan: {counts.get('rejected', 0)}\n\n"
    text += "Oxirgi 10 ta buyurtma:\n"

    if rows:
        for order_id, total_price, status, created_at in rows:
            status_label = STATUS_LABEL_MAP.get(status, status)
            date_str = _format_datetime(created_at)
            text += f"- ID {order_id} | {total_price:,} so'm | {status_label} | {date_str}\n"
    else:
        text += "Hozircha buyurtma yo'q.\n"

    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "admin_admins", F.from_user.id.in_(SUPER_ADMINS))
async def admin_admins_callback(callback: types.CallbackQuery):
    total_admins = len(set(ALL_ADMINS))
    super_count = len(set(SUPER_ADMINS))
    worker_count = len(set(WORKERS))

    text = "*Adminlar*\n\n"
    text += f"Jami: {total_admins}\n"
    text += f"Super adminlar: {super_count}\n"
    text += f"Workerlar: {worker_count}\n\n"
    text += "Adminlarni o'zgartirish uchun .env faylida SUPER_ADMINS va WORKERS ni yangilang."

    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()


@router.message(Command("stats"), F.from_user.id.in_(SUPER_ADMINS))
@router.callback_query(F.data == "admin_stats", F.from_user.id.in_(SUPER_ADMINS))
async def show_stats_callback(event: types.Message | types.CallbackQuery):
    message = event if isinstance(event, types.Message) else event.message
    lang = db.get_user_lang(event.from_user.id)
    s = STRINGS[lang]
    d_orders, d_rev = db.get_daily_stats()
    t_orders, t_rev = db.get_stats()
    
    text = f"{s['stats_title']}\n\n"
    text += f"{s['stats_today'].format(orders=d_orders, rev=d_rev)}\n\n"
    text += f"{s['stats_total'].format(orders=t_orders, rev=t_rev)}"
    
    if isinstance(event, types.CallbackQuery):
        await event.message.answer(text, parse_mode="Markdown")
        await event.answer()
    else:
        await message.answer(text, parse_mode="Markdown")

@router.callback_query(F.data == "admin_analytics", F.from_user.id.in_(SUPER_ADMINS))
async def show_analytics_callback(event: types.CallbackQuery | types.Message):
    message = event if isinstance(event, types.Message) else event.message
    top_products = db.get_top_products()
    top_customers = db.get_top_customers()
    
    text = "📈 **Kengaytirilgan Analitika**\n\n"
    
    text += "🍱 **Eng ko'p sotilgan taomlar:**\n"
    if top_products:
        for items, count in top_products:
            clean_items = items.replace("- ", "").replace("\n", ", ")
            text += f"- {clean_items}: {count} ta\n"
    else:
        text += "Ma'lumot mavjud emas.\n"
        
    text += "\n👑 **Top Mijozlar:**\n"
    if top_customers:
        for name, phone, spent in top_customers:
            text += f"- {name} ({phone}): {spent:,} so'm\n"
    else:
        text += "Ma'lumot mavjud emas.\n"
        
    await message.answer(text, parse_mode="Markdown")
    if isinstance(event, types.CallbackQuery):
        await event.answer()

@router.callback_query(F.data == "admin_menu_manage", F.from_user.id.in_(SUPER_ADMINS))
async def admin_menu_manage_callback(callback: types.CallbackQuery):
    await callback.message.edit_text("🍴 **Menu Boshqaruvi**\n\nBu yerdan taomlar qo'shishingiz, narxlarni o'zgartirishingiz yoki taomlarni o'chirishingiz mumkin.", reply_markup=menu_manage_kb())
    await callback.message.answer("Menu boshqaruvi tugmalari pastga qo'shildi.", reply_markup=menu_manage_reply_kb())
    await callback.answer()

@router.callback_query(F.data == "admin_promo_manage", F.from_user.id.in_(SUPER_ADMINS))
@router.message(F.text == "🎟 Promolar", F.from_user.id.in_(SUPER_ADMINS))
async def admin_promo_manage_callback(event: types.CallbackQuery | types.Message):
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text("🎟 **Promo Kodlar Boshqaruvi**", reply_markup=promo_manage_kb())
        await event.answer()
    else:
        await event.answer("🎟 **Promo Kodlar Boshqaruvi**", reply_markup=promo_manage_kb())

@router.callback_query(F.data == "admin_mailing", F.from_user.id.in_(SUPER_ADMINS))
@router.message(F.text == "📢 Mailing", F.from_user.id.in_(SUPER_ADMINS))
async def admin_mailing_callback(callback_event: types.CallbackQuery | types.Message):
    if isinstance(callback_event, types.CallbackQuery):
        await callback_event.message.edit_text("📢 **Mailing (Xabar yuborish)**", reply_markup=mailing_kb())
        await callback_event.answer()
    else:
        await callback_event.answer("📢 **Mailing (Xabar yuborish)**", reply_markup=mailing_kb())

# --- Text-based shortcuts for admin reply keyboard buttons ---

@router.message(F.text == "📊 Statistika", F.from_user.id.in_(SUPER_ADMINS))
async def admin_stats_msg(message: types.Message):
    await show_stats_callback(message)

@router.message(F.text == "📈 Analitika", F.from_user.id.in_(SUPER_ADMINS))
async def admin_analytics_msg(message: types.Message):
    await show_analytics_callback(FakeCallback(message))

@router.message(F.text == "📄 Excel Hisobot", F.from_user.id.in_(SUPER_ADMINS))
async def admin_report_msg(message: types.Message):
    await get_report_callback(message)

@router.message(F.text == "🛍 Buyurtmalar", F.from_user.id.in_(ALL_ADMINS))
async def admin_orders_msg(message: types.Message):
    class FakeCallback:
        def __init__(self, msg): self.message = msg; self.from_user = msg.from_user
        async def answer(self): pass
    await admin_orders_callback(FakeCallback(message))

@router.message(F.text == "🍴 Menu Boshqaruvi", F.from_user.id.in_(SUPER_ADMINS))
async def admin_menu_manage_msg(message: types.Message):
    await message.answer("🍴 **Menu Boshqaruvi**\n\nBu yerdan taomlar qo'shishingiz, narxlarni o'zgartirishingiz yoki taomlarni o'chirishingiz mumkin.", reply_markup=menu_manage_kb())
    await message.answer("Menu boshqaruvi tugmalari pastga qo'shildi.", reply_markup=menu_manage_reply_kb())

@router.message(F.text == "➕ Yangi taom qo'shish", F.from_user.id.in_(SUPER_ADMINS))
async def admin_add_prod_text(message: types.Message):
    await admin_add_prod_start(message)

@router.message(F.text == "✏️ Narxlarni tahrirlash", F.from_user.id.in_(SUPER_ADMINS))
async def admin_edit_price_text(message: types.Message):
    await admin_edit_price_start(message)

@router.message(F.text == "🗑 Taomni o'chirish", F.from_user.id.in_(SUPER_ADMINS))
async def admin_del_prod_text(message: types.Message):
    await admin_del_prod_start(message)

@router.message(F.text == "🔙 Asosiy panel", F.from_user.id.in_(ALL_ADMINS))
async def admin_back_home_msg(message: types.Message):
    user_id = message.from_user.id
    is_super = user_id in SUPER_ADMINS
    from keyboards.admin_keyboards import admin_reply_menu
    await message.answer("Asosiy panelga qaytdingiz.", reply_markup=admin_reply_menu(is_super))
    await admin_dashboard_msg(message)

# --- Product Management Handlers ---

@router.callback_query(F.data == "admin_add_prod", F.from_user.id.in_(SUPER_ADMINS))
async def admin_add_prod_start(callback: types.CallbackQuery):
    cats = db.get_all_categories()
    await callback.message.edit_text("Kategoriyani tanlang:", reply_markup=category_list_kb(cats))
    await callback.answer()

@router.callback_query(F.data == "admin_edit_price", F.from_user.id.in_(SUPER_ADMINS))
async def admin_edit_price_start(callback: types.CallbackQuery):
    cats = db.get_all_categories()
    await callback.message.edit_text("Kategoriyani tanlang (narxni o'zgartirish uchun):", reply_markup=category_list_kb(cats))
    await callback.answer()

@router.message(AdminStates.adding_product_name)
async def admin_add_prod_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Taom narxini kiriting (faqat raqamda):", reply_markup=cancel_kb())
    await state.set_state(AdminStates.adding_product_price)

@router.message(AdminStates.adding_product_price)
async def admin_add_prod_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Iltimos, faqat raqam kiriting!")
    await state.update_data(price=int(message.text))
    await message.answer("Taom rasmini yuboring (yoki Unsplash/local path matnini):", reply_markup=cancel_kb())
    await state.set_state(AdminStates.adding_product_image)

@router.message(AdminStates.adding_product_image)
async def admin_add_prod_image(message: types.Message, state: FSMContext):
    data = await state.get_data()
    image = message.text if message.text else "images/burger.png" # Default if not text
    if message.photo:
        # For simplicity, we'll ask for a path, but normally we'd save the image
        # Here we'll just use a placeholder or the file_id if we wanted to support it robustly
        image = "images/burger.png" # Minimal implementation
    
    db.add_product(data['cat_id'], data['name'], data['price'], image)
    await message.answer(f"✅ Taom qo'shildi: {data['name']}", reply_markup=admin_profile_kb(True))
    await state.clear()

# --- Cancel Handler ---
@router.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Amal bekor qilindi.", reply_markup=admin_profile_kb(True))
    await callback.answer()

# --- Product Edit Handler ---
# Reuse admin_cat_selected but with a state check for edit/delete
@router.callback_query(F.data.startswith("admin_cat_"), F.from_user.id.in_(SUPER_ADMINS))
async def admin_cat_selected_for_action(callback: types.CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[2])
    text = callback.message.text
    
    products = db.get_products_by_category(cat_id)
    if "narxni" in text:
        await callback.message.edit_text("Narxni o'zgartirish uchun taomni tanlang:", reply_markup=product_list_kb(products, "admin_edit_sel_"))
    elif "o'chirish" in text:
        await callback.message.edit_text("O'chirish uchun taomni tanlang:", reply_markup=product_list_kb(products, "admin_del_sel_"))
    else:
        # Addition flow (default)
        await state.update_data(cat_id=cat_id)
        await callback.message.answer("Taom nomini kiriting:", reply_markup=cancel_kb())
        await state.set_state(AdminStates.adding_product_name)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_edit_sel_"), F.from_user.id.in_(SUPER_ADMINS))
async def admin_edit_price_selected(callback: types.CallbackQuery, state: FSMContext):
    prod_id = int(callback.data.split("_")[3])
    await state.update_data(prod_id=prod_id)
    await callback.message.answer("Yangi narxni kiriting (faqat raqam):", reply_markup=cancel_kb())
    await state.set_state(AdminStates.editing_price_value)
    await callback.answer()

@router.message(AdminStates.editing_price_value)
async def admin_edit_price_save(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Iltimos, faqat raqam kiriting!")
    data = await state.get_data()
    db.update_product_price(data['prod_id'], int(message.text))
    await message.answer(f"✅ Narx o'zgartirildi: {message.text} so'm", reply_markup=admin_profile_kb(True))
    await state.clear()

@router.callback_query(F.data.startswith("admin_del_sel_"), F.from_user.id.in_(SUPER_ADMINS))
async def admin_del_prod_selected(callback: types.CallbackQuery):
    prod_id = int(callback.data.split("_")[3])
    db.delete_product(prod_id)
    await callback.message.answer("✅ Taom o'chirildi.")
    await admin_menu_manage_callback(callback)
    await callback.answer()

# --- Product Delete Handler ---
@router.callback_query(F.data == "admin_del_prod", F.from_user.id.in_(SUPER_ADMINS))
async def admin_del_prod_start(callback: types.CallbackQuery):
    cats = db.get_all_categories()
    # I'll use a fixed prefix for category selection in different flows
    await callback.message.edit_text("Kategoriyani tanlang (o'chirish uchun):", reply_markup=category_list_kb(cats))
    await callback.answer()

# --- Promo Code Handlers ---
@router.callback_query(F.data == "admin_add_promo", F.from_user.id.in_(SUPER_ADMINS))
async def admin_add_promo_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Yangi promo kodni kiriting (masalan: YUMMY2024):", reply_markup=cancel_kb())
    await state.set_state(AdminStates.adding_promo_code)
    await callback.answer()

@router.message(AdminStates.adding_promo_code)
async def admin_add_promo_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text.upper())
    await message.answer("Chegirma foizini kiriting (faqat raqam, masalan: 10):", reply_markup=cancel_kb())
    await state.set_state(AdminStates.adding_promo_discount)

@router.message(AdminStates.adding_promo_discount)
async def admin_add_promo_discount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Iltimos, faqat raqam kiriting!")
    data = await state.get_data()
    db.create_promo_code(data['code'], int(message.text))
    await message.answer(f"✅ Promo kod qo'shildi: {data['code']} ({message.text}%)", reply_markup=admin_profile_kb(True))
    await state.clear()

@router.callback_query(F.data == "admin_list_promo", F.from_user.id.in_(SUPER_ADMINS))
async def admin_list_promo(callback: types.CallbackQuery):
    promos = db.get_all_promo_codes()
    text = "📜 **Mavjud promo kodlar:**\n\n"
    kb = []
    if promos:
        for p_id, code, disc, active, expiry in promos:
            text += f"- {code}: {disc}% ({'Faol' if active else 'No-faol'})\n"
            kb.append([InlineKeyboardButton(text=f"❌ {code} ni o'chirish", callback_data=f"admin_pdel_{p_id}")])
    else:
        text += "Hozircha promo kodlar yo'q."
    
    kb.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_promo_manage")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_pdel_"), F.from_user.id.in_(SUPER_ADMINS))
async def admin_promo_delete(callback: types.CallbackQuery):
    p_id = int(callback.data.split("_")[2])
    db.delete_promo_code(p_id)
    await callback.message.answer("✅ Promo kod o'chirildi.")
    await admin_list_promo(callback)

# --- Mailing Handlers ---
@router.callback_query(F.data == "admin_send_mail", F.from_user.id.in_(SUPER_ADMINS))
async def admin_send_mail_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Yubormoqchi bo'lgan xabaringizni yozing (matn, rasm yoki video):", reply_markup=cancel_kb())
    await state.set_state(AdminStates.mailing_content)
    await callback.answer()

@router.message(AdminStates.mailing_content)
async def admin_mailing_content(message: types.Message, state: FSMContext):
    # Store message for preview
    await state.update_data(msg_id=message.message_id, chat_id=message.chat.id)
    kb = [
        [InlineKeyboardButton(text="✅ Tasdiqlash va yuborish", callback_data="admin_mail_confirm")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_cancel")]
    ]
    await message.answer("Xabarni barcha foydalanuvchilarga yuborishni tasdiqlaysizmi?", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(AdminStates.mailing_preview)

@router.callback_query(F.data == "admin_mail_confirm", F.from_user.id.in_(SUPER_ADMINS), AdminStates.mailing_preview)
async def admin_mail_confirm(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    users = db.get_all_users()
    count = 0
    await callback.message.edit_text(f"🚀 Xabar yuborish boshlandi ({len(users)} users)...")
    
    for user in users:
        try:
            await callback.bot.copy_message(chat_id=user[0], from_chat_id=data['chat_id'], message_id=data['msg_id'])
            count += 1
            if count % 10 == 0:
                await asyncio.sleep(0.5) # Rate limiting
        except Exception:
            pass
    
    await callback.message.answer(f"✅ Xabar {count} ta foydalanuvchiga yuborildi.")
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: types.CallbackQuery):
    from keyboards.user_keyboards import main_menu
    lang = db.get_user_lang(callback.from_user.id)
    await callback.message.answer("🏠 Foydalanuvchi menyusiga qaytdingiz.", reply_markup=main_menu(lang, is_admin=True))
    await callback.answer()

# ... (rest of existing worker order handlers) ...

@router.message(Command("report"), F.from_user.id.in_(SUPER_ADMINS))
@router.callback_query(F.data == "admin_report", F.from_user.id.in_(SUPER_ADMINS))
async def get_report_callback(event: types.Message | types.CallbackQuery):
    message = event if isinstance(event, types.Message) else event.message
    try:
        import pandas as pd
        orders = db.get_all_orders()
        df = pd.DataFrame(orders, columns=['ID', 'User ID', 'Items', 'Total Price', 'Status', 'Location', 'Date'])
        
        file_path = "yummy_report.xlsx"
        df.to_excel(file_path, index=False)
        
        await message.answer_document(types.FSInputFile(file_path), caption="📊 Barcha buyurtmalar bo'yicha hisobot (Excel)")
        os.remove(file_path)
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")
    
    if isinstance(event, types.CallbackQuery):
        await event.answer()

@router.callback_query(F.data == "worker_info")
async def worker_info_callback(callback: types.CallbackQuery):
    await callback.message.answer("📦 Siz yangi buyurtmalarni ushbu bot orqali qabul qilishingiz va ularning holatini boshqarishingiz mumkin.\n\nYangi buyurtma tushganda sizga bildirishnoma keladi.")
    await callback.answer()

@router.callback_query(F.data.startswith("accept_"))
async def accept_order(callback: types.CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    db.update_order_status(order_id, "accepted")
    order = db.get_order(order_id)
    user_id = order[1]
    
    lang = db.get_user_lang(user_id)
    s = STRINGS[lang]

    await callback.message.edit_text(callback.message.text + "\n\n✅ Accepted", reply_markup=order_next_stage_kb(order_id, "accepted"))
    await callback.bot.send_message(user_id, s['sms_accepted'].format(id=order_id), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("reject_"))
async def reject_order(callback: types.CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    db.update_order_status(order_id, "rejected")
    order = db.get_order(order_id)
    user_id = order[1]
    
    lang = db.get_user_lang(user_id)
    s = STRINGS[lang]

    await callback.message.edit_text(callback.message.text + "\n\n❌ Rejected")
    await callback.bot.send_message(user_id, s['order_cancelled'], parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("preparing_"))
async def preparing_order(callback: types.CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    db.update_order_status(order_id, "preparing")
    order = db.get_order(order_id)
    user_id = order[1]
    
    lang = db.get_user_lang(user_id)
    s = STRINGS[lang]

    await callback.message.edit_text(callback.message.text + "\n\n👨‍🍳 Preparing", reply_markup=order_next_stage_kb(order_id, "preparing"))
    await callback.bot.send_message(user_id, s['sms_preparing'].format(id=order_id), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("delivering_"))
async def delivering_order(callback: types.CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    db.update_order_status(order_id, "delivering")
    order = db.get_order(order_id)
    user_id = order[1]
    
    lang = db.get_user_lang(user_id)
    s = STRINGS[lang]

    await callback.message.edit_text(callback.message.text + "\n\n🚴 Delivering", reply_markup=order_next_stage_kb(order_id, "delivering"))
    await callback.bot.send_message(user_id, s['sms_delivering'].format(id=order_id), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("complete_"))
async def complete_order(callback: types.CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    db.update_order_status(order_id, "completed")
    order = db.get_order(order_id)
    user_id = order[1]
    
    lang = db.get_user_lang(user_id)
    s = STRINGS[lang]

    await callback.message.edit_text(callback.message.text + "\n\n🏁 Completed")
    await callback.bot.send_message(user_id, s['sms_completed'].format(id=order_id), parse_mode="Markdown")
    await callback.answer()
