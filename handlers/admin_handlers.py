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
import keyboards.admin_keyboards as akb
from utils.publisher import publish_menu
from config import SUPER_ADMINS, ALL_ADMINS, WORKERS
from translations import STRINGS
import os

class AdminStates(StatesGroup):
    # Product States
    adding_product_name = State()   # First after category
    adding_product_price = State()  # Second
    adding_product_image = State()  # Third (last)
    
    editing_price_value = State()
    
    # Promo States
    adding_promo_code = State()
    adding_promo_discount = State()
    
    # Mailing States
    mailing_content = State()
    mailing_preview = State()
    
    # Admin Management States
    adding_admin_id = State()

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
    
    admins = db.get_all_admins()
    total_admins = len(admins)
    super_count = len([a for a in admins if a[1] == 'super_admin'])
    worker_count = total_admins - super_count
    
    admin_data = db.get_admin(user_id)
    role_label = "🌟 Super admin" if admin_data and admin_data[1] == 'super_admin' else "🛠 Admin"

    text = "🖥 **ADMIN DASHBOARD**\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    text += f"👤 **Siz:** {role_label}\n"
    text += f"👥 **Jamoa:** {total_admins} kishi (S: {super_count}, W: {worker_count})\n\n"
    
    text += "📅 **Bugungi natijalar:**\n"
    text += f"🛒 Buyurtmalar: `{d_orders}` ta\n"
    text += f"💰 Tushum: `{d_rev:,}` so'm\n\n"
    
    text += "📊 **Umumiy statistika:**\n"
    text += f"🥡 Jami buyurtmalar: `{t_orders}` ta\n"
    text += f"💵 Jami tushum: `{t_rev:,}` so'm\n\n"
    
    text += f"🔔 **Faol buyurtmalar: {active_count}**\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    
    status_emojis = {
        "pending": "🟡",
        "accepted": "🟢",
        "preparing": "👨‍🍳",
        "delivering": "🚴",
        "completed": "✅",
        "rejected": "❌"
    }
    
    for status, label in STATUS_LABELS:
        emoji = status_emojis.get(status, "🔹")
        text += f"{emoji} {label}: `{counts.get(status, 0)}`\n"

    return text


@router.callback_query(F.data.in_(["admin_dashboard", "admin_dashboard_home"]))
async def admin_dashboard_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    admin = db.get_admin(user_id)
    if not admin or (user_id not in (SUPER_ADMINS + WORKERS)):
        return await callback.answer("Sizda admin huquqi yo'q.", show_alert=True)
        
    is_super = admin[1] == 'super_admin'
    text = build_admin_dashboard_text(user_id)
    await callback.message.edit_text(text, reply_markup=admin_profile_kb(is_super), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "admin_orders")
async def admin_orders_callback(callback: types.CallbackQuery):
    if not db.has_permission(callback.from_user.id, 'orders'):
        return await callback.answer("Sizda buyurtmalarni ko'rish huquqi yo'q.", show_alert=True)
    counts = _get_order_status_counts()
    active_count = sum(counts.get(key, 0) for key, _ in STATUS_LABELS[:4])
    rows = db.cursor.execute(
        "SELECT order_id, total_price, status, created_at FROM orders ORDER BY created_at DESC LIMIT ?",
        (10,),
    ).fetchall()

    text = "🛍 **BUYURTMALAR MONITORINGI**\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    text += f"🔥 Faol: `{active_count}` | ✅ Yakunlangan: `{counts.get('completed', 0)}` | ❌ Rad: `{counts.get('rejected', 0)}`\n\n"
    text += "🕒 **Oxirgi 10 ta buyurtma:**\n"

    if rows:
        status_emojis = {
            "pending": "⏳", "accepted": "✅", "preparing": "🍳",
            "delivering": "🛵", "completed": "🏁", "rejected": "🚫"
        }
        for order_id, total_price, status, created_at in rows:
            emoji = status_emojis.get(status, "🔹")
            status_label = STATUS_LABEL_MAP.get(status, status)
            date_str = _format_datetime(created_at)
            text += f"{emoji} **#{order_id}** | `{total_price:,}` so'm | {date_str}\n"
    else:
        text += "📭 Hozircha buyurtma yo'q.\n"

    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "admin_admins", F.from_user.id.in_(SUPER_ADMINS))
async def admin_admins_callback(callback: types.CallbackQuery):
    # Open admin management menu instead of just showing info
    await callback.message.edit_text("👥 **Adminlar Boshqaruvi**", reply_markup=akb.admin_management_kb(), parse_mode="Markdown")
    await callback.answer()


@router.message(Command("fix"), F.from_user.id.in_(SUPER_ADMINS))
async def fix_database_command(message: types.Message):
    """Force manual menu database initialization"""
    msg = await message.answer("🔄 Bazani qayta tiklash boshlandi...")
    try:
        # First try hardcoded initializer (most reliable)
        from init_menu import init_menu
        init_menu()
        await msg.edit_text("✅ Baza muvaffaqiyatli tiklandi! 16 ta kategoriya qo'shildi.\n\nEndi menu bo'limini tekshirib ko'ring.")
    except Exception as e:
        await msg.edit_text(f"❌ Xatolik: {e}\n\nIltimos, dasturchi bilan bog'laning.")

@router.message(Command("stats"))
@router.callback_query(F.data == "admin_stats")
async def show_stats_callback(event: types.Message | types.CallbackQuery):
    if not db.has_permission(event.from_user.id, 'stats'):
        if isinstance(event, types.CallbackQuery):
            await event.answer("Sizda statistikani ko'rish huquqi yo'q.", show_alert=True)
        return
    message = event if isinstance(event, types.Message) else event.message
    lang = db.get_user_lang(event.from_user.id)
    s = STRINGS[lang]
    d_orders, d_rev = db.get_daily_stats()
    t_orders, t_rev = db.get_stats()
    
    text = f"📉 **{s['stats_title']}**\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    text += f"📅 **Bugun:**\n"
    text += f"🛒 Buyurtmalar: `{d_orders}` ta\n"
    text += f"💰 Tushum: `{d_rev:,}` so'm\n\n"
    text += f"🌍 **Umumiy:**\n"
    text += f"🥡 Buyurtmalar: `{t_orders}` ta\n"
    text += f"💵 Tushum: `{t_rev:,}` so'm"
    
    if isinstance(event, types.CallbackQuery):
        await event.message.answer(text, parse_mode="Markdown")
        await event.answer()
    else:
        await message.answer(text, parse_mode="Markdown")

@router.callback_query(F.data == "admin_analytics")
async def show_analytics_callback(event: types.CallbackQuery | types.Message):
    if not db.has_permission(event.from_user.id, 'stats'):
        if isinstance(event, types.CallbackQuery):
            await event.answer("Sizda analitikani ko'rish huquqi yo'q.", show_alert=True)
        return
    top_products = db.get_top_products()
    top_customers = db.get_top_customers()
    peak_hours = db.get_peak_hours()
    
    text = "📈 **KENGAYTIRILGAN ANALITIKA**\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    
    text += "🍱 **Ommabop Taomlar (Top 5):**\n"
    if top_products:
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for idx, (items, count) in enumerate(top_products[:5]):
            medal = medals[idx] if idx < len(medals) else "🔹"
            clean_items = items.replace("- ", "").replace("\n", ", ")
            text += f"{medal} {clean_items}: `{count}` ta\n"
    else:
        text += "➖ Ma'lumot mavjud emas.\n"
        
    text += "\n🕒 **Eng gavjum vaqtlar (Peak Hours):**\n"
    if peak_hours:
        for hour, count in peak_hours:
            text += f"⏰ {hour} — `{count}` ta buyurtma\n"
    else:
        text += "➖ Ma'lumot mavjud emas.\n"

    text += "\n👑 **Top Mijozlar (Sodiqlik):**\n"
    if top_customers:
        for idx, (name, phone, spent) in enumerate(top_customers[:5]):
            text += f"👤 {name}: `{spent:,}` so'm\n"
    else:
        text += "➖ Ma'lumot mavjud emas.\n"
        
    await message.answer(text, parse_mode="Markdown")
    if isinstance(event, types.CallbackQuery):
        await event.answer()

@router.callback_query(F.data == "admin_menu_manage")
async def admin_menu_manage_callback(callback: types.CallbackQuery):
    if not db.has_permission(callback.from_user.id, 'menu'):
        return await callback.answer("Sizda menuni boshqarish huquqi yo'q.", show_alert=True)
    
    text = "🍴 **Menu Boshqaruvi**\n\n"
    text += "Bu yerdan taomlarni boshqarishingiz mumkin.\n"
    text += "💡 Agar kategoriyalar ko'rinmasa, **🔄 JS -> DB Sync** tugmasini bosing."
    
    await callback.message.edit_text(text, reply_markup=akb.menu_manage_kb(), parse_mode="Markdown")
    await callback.message.answer("Menu boshqaruvi tugmalari pastga qo'shildi.", reply_markup=akb.menu_manage_reply_kb())
    await callback.answer()

@router.callback_query(F.data == "admin_sync_js")
async def admin_sync_js_callback(callback: types.CallbackQuery):
    if not db.has_permission(callback.from_user.id, 'menu'):
        return await callback.answer("Ruxsat yo'q.", show_alert=True)
    
    await callback.message.answer("🔄 Sinxronizatsiya boshlandi...")
    try:
        from utils.sync_from_js import import_menu_from_js
        import_menu_from_js()
        await callback.message.answer("✅ Menu muvaffaqiyatli sinxronizatsiya qilindi! Endi kategoriyalar chiqishi kerak.")
    except Exception as e:
        await callback.message.answer(f"❌ Xatolik yuz berdi: {e}")
    await callback.answer()

@router.callback_query(F.data == "admin_promo_manage")
@router.message(F.text == "🎟 Promolar")
async def admin_promo_manage_callback(event: types.CallbackQuery | types.Message):
    # All admins can view promo panel, but only super admin can add/delete
    admin = db.get_admin(event.from_user.id)
    if not admin:
        if isinstance(event, types.CallbackQuery):
            await event.answer("Sizda admin huquqi yo'q.", show_alert=True)
        return
    
    is_super = admin[1] == 'super_admin'
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text("🎟 **Promo Kodlar Boshqaruvi**", reply_markup=promo_manage_kb(is_super_admin=is_super))
        await event.answer()
    else:
        await event.answer("🎟 **Promo Kodlar Boshqaruvi**", reply_markup=promo_manage_kb(is_super_admin=is_super))

@router.callback_query(F.data == "admin_mailing")
@router.message(F.text == "📢 Mailing")
async def admin_mailing_callback(callback_event: types.CallbackQuery | types.Message):
    if not db.has_permission(callback_event.from_user.id, 'mailing'):
        if isinstance(callback_event, types.CallbackQuery):
            await callback_event.answer("Sizda xabar yuborish huquqi yo'q.", show_alert=True)
        return
    if isinstance(callback_event, types.CallbackQuery):
        await callback_event.message.edit_text("📢 **Mailing (Xabar yuborish)**", reply_markup=mailing_kb())
        await callback_event.answer()
    else:
        await callback_event.answer("📢 **Mailing (Xabar yuborish)**", reply_markup=mailing_kb())

@router.message(F.text == "📉 Statistika")
async def admin_stats_msg(message: types.Message):
    await show_stats_callback(message)

@router.message(F.text == "📊 Dashboard")
async def admin_dashboard_msg(message: types.Message):
    user_id = message.from_user.id
    admin = db.get_admin(user_id)
    if not admin or (user_id not in (SUPER_ADMINS + WORKERS)):
        return await message.answer("Sizda admin huquqi yo'q.")
    
    is_super = admin[1] == 'super_admin'
    text = build_admin_dashboard_text(message.from_user.id)
    await message.answer(text, reply_markup=akb.admin_reply_menu(is_super), parse_mode="Markdown")

@router.message(F.text == "📑 Hisobot (Excel)")
async def admin_report_msg(message: types.Message):
    if not db.has_permission(message.from_user.id, 'stats'):
        return await message.answer("Sizda hisobotlarni ko'rish huquqi yo'q.")
    await get_report_callback(message)

@router.message(F.text == "👥 Adminlar Boshqaruvi")
async def admin_admins_msg(message: types.Message):
    if not db.has_permission(message.from_user.id, 'manage_admins'):
        return await message.answer("Sizda bu bo'limga kirish huquqi yo'q.")
    await message.answer("👥 Adminlar Boshqaruvi", reply_markup=akb.admin_management_kb())

@router.callback_query(F.data == "am_home")
async def am_home(callback: types.CallbackQuery):
    await callback.message.edit_text("👥 **Adminlar Boshqaruvi**", reply_markup=akb.admin_management_kb())
    await callback.answer()

@router.callback_query(F.data == "am_list")
async def am_list(callback: types.CallbackQuery):
    admins = db.get_all_admins()
    await callback.message.edit_text("📜 **Mavjud adminlar ro'yxati:**", reply_markup=akb.admin_list_kb(admins))
    await callback.answer()

@router.callback_query(F.data == "am_add")
async def am_add_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("➕ Yangi admin qo'shish uchun uning **Telegram ID** raqamini yozing:", reply_markup=akb.cancel_kb())
    await state.set_state(AdminStates.adding_admin_id)
    await callback.answer()

@router.message(AdminStates.adding_admin_id)
async def am_save_new(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Iltimos, faqat raqamlardan iborat ID ni kiriting!")
    
    target_id = int(message.text)
    
    # Check if user exists in database (registered with bot)
    existing_user = db.get_user(target_id)
    
    if not existing_user:
        # User not registered - show warning but still allow adding
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Baribir qo'shish", callback_data=f"am_force_add_{target_id}")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="am_home")]
        ])
        await message.answer(
            f"⚠️ **Ogohlantirish!**\n\n"
            f"ID `{target_id}` egasi hali botdan ro'yxatdan o'tmagan.\n\n"
            f"Bu shaxs admin bo'lishi uchun avval botga /start buyrug'ini berishi kerak.\n\n"
            f"Baribir qo'shmoqchimisiz?",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        await state.clear()
        return
    
    # User exists - add as admin
    db.add_admin(target_id, role='admin', permissions='orders')
    user_name = existing_user[1] if existing_user else "Noma'lum"
    await message.answer(
        f"✅ Admin qo'shildi!\n\n"
        f"👤 Ism: {user_name}\n"
        f"🆔 ID: {target_id}\n\n"
        f"Endi uning huquqlarini sozlashingiz mumkin.", 
        reply_markup=akb.admin_view_kb(target_id, 'admin')
    )
    await state.clear()

@router.callback_query(F.data.startswith("am_force_add_"))
async def am_force_add(callback: types.CallbackQuery):
    """Force add admin even if not registered"""
    target_id = int(callback.data.split("_")[3])
    db.add_admin(target_id, role='admin', permissions='orders')
    await callback.message.edit_text(
        f"✅ Admin qo'shildi (ID: {target_id}).\n\n"
        f"⚠️ Bu shaxs admin paneliga kirish uchun avval botga /start buyrug'ini berishi kerak.",
        reply_markup=akb.admin_view_kb(target_id, 'admin')
    )
    await callback.answer()

@router.callback_query(F.data.startswith("am_view_"))
async def am_view(callback: types.CallbackQuery):
    target_id = int(callback.data.split("_")[2])
    admin = db.get_admin(target_id)
    if not admin:
        return await callback.answer("Admin topilmadi.", show_alert=True)
    
    perms = admin[2] if admin[2] else "Yo'q"
    text = f"👤 **Admin Ma'lumotlari**\n\n🆔 ID: {admin[0]}\n🎭 Rol: {admin[1]}\n🔐 Huquqlar: {perms}"
    await callback.message.edit_text(text, reply_markup=akb.admin_view_kb(target_id, admin[1]))
    await callback.answer()

@router.callback_query(F.data.startswith("am_edit_role_"))
async def am_edit_role(callback: types.CallbackQuery):
    target_id = int(callback.data.split("_")[3])
    await callback.message.edit_text("🎭 Yangi rolni tanlang:", reply_markup=akb.admin_role_kb(target_id))
    await callback.answer()

@router.callback_query(F.data.startswith("am_setrole_"))
async def am_set_role(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    target_id = int(parts[2])
    new_role = parts[3] + "_" + parts[4] if len(parts) > 4 else parts[3]
    
    db.update_admin_role(target_id, new_role)
    await callback.answer(f"Rol '{new_role}' qilib belgilandi.", show_alert=True)
    await am_view(callback)

@router.callback_query(F.data.startswith("am_edit_perms_"))
async def am_edit_perms(callback: types.CallbackQuery):
    target_id = int(callback.data.split("_")[3])
    admin = db.get_admin(target_id)
    await callback.message.edit_text("🔐 Admin huquqlarini belgilang:", reply_markup=akb.admin_permissions_kb(target_id, admin[2]))
    await callback.answer()

@router.callback_query(F.data.startswith("am_togperm_"))
async def am_toggle_perm(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    target_id = int(parts[2])
    perm = parts[3]
    
    admin = db.get_admin(target_id)
    current_list = admin[2].split(',') if admin[2] else []
    
    if perm in current_list:
        current_list.remove(perm)
    else:
        current_list.append(perm)
    
    new_perms = ",".join([p for p in current_list if p])
    db.update_admin_permissions(target_id, new_perms)
    await callback.message.edit_reply_markup(reply_markup=akb.admin_permissions_kb(target_id, new_perms))
    await callback.answer()

@router.callback_query(F.data.startswith("am_del_"))
async def am_delete(callback: types.CallbackQuery):
    target_id = int(callback.data.split("_")[2])
    
    if target_id == callback.from_user.id:
        return await callback.answer("O'zingizni o'chirib bo'lmaydi!", show_alert=True)
    
    db.remove_admin(target_id)
    await callback.answer("Admin muvaffaqiyatli o'chirildi. Endi u admin panelga kira olmaydi.", show_alert=True)
    
    # Notify and update keyboard of the removed user
    try:
        from keyboards.user_keyboards import main_menu
        lang = db.get_user_lang(target_id)
        # is_admin is False now because they are removed
        await callback.bot.send_message(
            target_id, 
            "Siz adminlikdan chetlashtirildingiz.", 
            reply_markup=main_menu(lang, is_admin=False)
        )
    except:
        pass
        
    await am_list(callback)

@router.message(F.text == "🛍 Buyurtmalar")
async def admin_orders_msg(message: types.Message):
    if not db.has_permission(message.from_user.id, 'orders'):
        return await message.answer("Sizda buyurtmalarni ko'rish huquqi yo'q.")
    class FakeCallback:
        def __init__(self, msg): self.message = msg; self.from_user = msg.from_user
        async def answer(self): pass
    await admin_orders_callback(FakeCallback(message))

@router.message(F.text == "🍽 Menu Boshqaruvi")
async def admin_menu_manage_msg(message: types.Message, state: FSMContext):
    # Clear any previous state to prevent conflicts
    await state.clear()
    
    if not db.has_permission(message.from_user.id, 'menu'):
        return await message.answer("Sizda menuni boshqarish huquqi yo'q.")
    
    text = "🍴 **Menu Boshqaruvi**\n\n"
    text += "Bu yerdan taomlarni boshqarishingiz mumkin.\n"
    text += "💡 Agar kategoriyalar ko'rinmasa, quyidagi **🔄 JS -> DB Sync** tugmasini bosing yoki /fix buyrug'ini yuboring."
    
    await message.answer(text, reply_markup=akb.menu_manage_kb(), parse_mode="Markdown")
    await message.answer("Tugmalar pastda ham paydo bo'ldi.", reply_markup=akb.menu_manage_reply_kb())

@router.message(F.text == "➕ Yangi taom qo'shish")
@router.message(F.text == "✏️ Narxlarni tahrirlash")
@router.message(F.text == "🗑 Taomni o'chirish")
@router.message(F.text == "🚀 Saytga chiqarish (Update)")
async def admin_menu_text_access(message: types.Message):
    if not db.has_permission(message.from_user.id, 'menu'):
        return await message.answer("Sizda bu bo'limga ruxsat yo'q.")
    
    text = message.text
    cats = db.get_all_categories()
    if "Yangi taom" in text:
        await message.answer("Kategoriyani tanlang:", reply_markup=category_list_kb(cats))
    elif "Narxlarni" in text:
        await message.answer("Kategoriyani tanlang (narxni o'zgartirish uchun):", reply_markup=category_list_kb(cats))
    elif "Taomni o'chirish" in text:
        await message.answer("Kategoriyani tanlang (o'chirish uchun):", reply_markup=category_list_kb(cats))
    elif "Saytga chiqarish" in text:
        msg = await message.answer("🚀 Sayt yangilanmoqda, iltimos kuting...")
        success = publish_menu()
        if success:
            await msg.edit_text("✅ Sayt muvaffaqiyatli yangilandi! O'zgarishlar 1-2 daqiqada GitHub Pages-da ko'rinadi.")
        else:
            await msg.edit_text("❌ Yangilashda xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")

@router.message(F.text == "🔙 Asosiy panel")
async def admin_back_home_msg(message: types.Message):
    admin = db.get_admin(message.from_user.id)
    if not admin: return
    
    is_super = admin[1] == 'super_admin'
    from keyboards.admin_keyboards import admin_reply_menu
    await message.answer("Asosiy panelga qaytdingiz.", reply_markup=admin_reply_menu(is_super))
    await admin_dashboard_msg(message)

# --- Product Management Handlers ---

@router.callback_query(F.data == "admin_add_prod")
async def admin_add_prod_start(callback: types.CallbackQuery):
    if not db.has_permission(callback.from_user.id, 'menu'):
        return await callback.answer("Ruxsat yo'q.", show_alert=True)
    cats = db.get_all_categories()
    await callback.message.edit_text("Kategoriyani tanlang:", reply_markup=category_list_kb(cats))
    await callback.answer()

@router.callback_query(F.data == "admin_edit_price")
async def admin_edit_price_start(callback: types.CallbackQuery):
    if not db.has_permission(callback.from_user.id, 'menu'):
        return await callback.answer("Ruxsat yo'q.", show_alert=True)
    cats = db.get_all_categories()
    await callback.message.edit_text("Kategoriyani tanlang (narxni o'zgartirish uchun):", reply_markup=category_list_kb(cats))
    await callback.answer()

@router.callback_query(F.data == "admin_del_prod")
async def admin_del_prod_start(callback: types.CallbackQuery):
    if not db.has_permission(callback.from_user.id, 'menu'):
        return await callback.answer("Ruxsat yo'q.", show_alert=True)
    cats = db.get_all_categories()
    await callback.message.edit_text("Kategoriyani tanlang (o'chirish uchun):", reply_markup=category_list_kb(cats))
    await callback.answer()

@router.callback_query(F.data == "admin_publish_web")
async def admin_publish_web_callback(callback: types.CallbackQuery):
    if not db.has_permission(callback.from_user.id, 'menu'):
        return await callback.answer("Ruxsat yo'q.", show_alert=True)
    
    await callback.message.answer("🚀 Sayt yangilanmoqda, iltimos kuting...")
    await callback.answer("Yangilash boshlandi...")
    
    success = publish_menu()
    if success:
        await callback.message.answer("✅ Sayt muvaffaqiyatli yangilandi! O'zgarishlar 1-2 daqiqada GitHub Pages-da ko'rinadi.")
    else:
        await callback.message.answer("❌ Yangilashda xatolik yuz berdi.")

@router.message(AdminStates.adding_product_name)
async def admin_add_prod_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("💰 Taom narxini kiriting (faqat raqamda):", reply_markup=cancel_kb())
    await state.set_state(AdminStates.adding_product_price)

@router.message(AdminStates.adding_product_price)
async def admin_add_prod_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Iltimos, faqat raqam kiriting!")
    await state.update_data(price=int(message.text))
    await message.answer("📷 Taom rasmini yuboring:", reply_markup=cancel_kb())
    await state.set_state(AdminStates.adding_product_image)

@router.message(AdminStates.adding_product_image)
async def admin_add_prod_image(message: types.Message, state: FSMContext):
    import os
    import uuid
    
    data = await state.get_data()
    
    if message.photo:
        # Save the photo to images folder
        photo = message.photo[-1]  # Get highest resolution
        file_id = photo.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        
        # Generate unique filename
        ext = file_path.split('.')[-1] if '.' in file_path else 'jpg'
        new_filename = f"product_{uuid.uuid4().hex[:8]}.{ext}"
        save_path = f"images/products/{new_filename}"
        
        # Create directory if not exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Download and save
        await message.bot.download_file(file_path, save_path)
        image_path = f"images/products/{new_filename}"
    elif message.text:
        image_path = message.text
    else:
        return await message.answer("Iltimos, rasm yuboring!")
    
    # Add product to database
    db.add_product(data['cat_id'], data['name'], data['price'], image_path)
    
    # Auto-sync to WebApp (GitHub)
    from utils.publisher import publish_menu
    publish_menu()
    
    # Send confirmation
    from keyboards.admin_keyboards import menu_manage_reply_kb
    await message.answer(
        f"✅ Taom muvaffaqiyatli qo'shildi va saytga yuklandi!\n\n📝 Nom: {data['name']}\n💰 Narx: {data['price']:,} so'm\n\n"
        f"🌐 O'zgarishlar 1-2 daqiqada ko'rinadi.",
        reply_markup=menu_manage_reply_kb()
    )
    await state.clear()
 

# --- Cancel Handler ---
@router.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    admin = db.get_admin(callback.from_user.id)
    is_super = admin[1] == 'super_admin' if admin else False
    await callback.message.edit_text("Amal bekor qilindi.", reply_markup=admin_profile_kb(is_super))
    await callback.answer()

# --- Product Edit Handler ---
# Reuse admin_cat_selected but with a state check for edit/delete
@router.callback_query(F.data.startswith("admin_cat_"))
async def admin_cat_selected_for_action(callback: types.CallbackQuery, state: FSMContext):
    if not db.has_permission(callback.from_user.id, 'menu'):
        return await callback.answer("Ruxsat yo'q.", show_alert=True)
    cat_id = int(callback.data.split("_")[2])
    text = callback.message.text
    
    products = db.get_products_by_category(cat_id)
    if "narxni" in text:
        await callback.message.edit_text("Narxni o'zgartirish uchun taomni tanlang:", reply_markup=product_list_kb(products, "admin_edit_sel_"))
    elif "o'chirish" in text:
        await callback.message.edit_text("O'chirish uchun taomni tanlang:", reply_markup=product_list_kb(products, "admin_del_sel_"))
    else:
        # Addition flow: Category selected, ask for NAME
        await state.update_data(cat_id=cat_id)
        await callback.message.answer("📝 Taom nomini kiriting:", reply_markup=cancel_kb())
        await state.set_state(AdminStates.adding_product_name)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_edit_sel_"))
async def admin_edit_price_selected(callback: types.CallbackQuery, state: FSMContext):
    if not db.has_permission(callback.from_user.id, 'menu'):
        return await callback.answer("Ruxsat yo'q.", show_alert=True)
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
    
    # Sync WebApp
    from utils.publisher import publish_menu
    publish_menu()

    await message.answer(f"✅ Narx o'zgartirildi: {message.text} so'm", reply_markup=admin_profile_kb(True))
    await state.clear()

@router.callback_query(F.data.startswith("admin_del_sel_"))
async def admin_del_prod_selected(callback: types.CallbackQuery):
    if not db.has_permission(callback.from_user.id, 'menu'):
        return await callback.answer("Ruxsat yo'q.", show_alert=True)
    prod_id = int(callback.data.split("_")[3])
    db.delete_product(prod_id)
    
    # Sync WebApp
    from utils.publisher import publish_menu
    publish_menu()

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
@router.callback_query(F.data == "admin_add_promo")
async def admin_add_promo_start(callback: types.CallbackQuery, state: FSMContext):
    # Only Super Admin can add promo codes
    admin = db.get_admin(callback.from_user.id)
    if not admin or admin[1] != 'super_admin':
        return await callback.answer("❌ Faqat super admin promo kodi qo'sha oladi!", show_alert=True)
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

@router.callback_query(F.data == "admin_list_promo")
async def admin_list_promo(callback: types.CallbackQuery):
    # All admins can view promo codes
    admin = db.get_admin(callback.from_user.id)
    if not admin:
        return await callback.answer("❌ Admin huquqi yo'q!", show_alert=True)
    
    is_super = admin[1] == 'super_admin'
    promos = db.get_all_promo_codes()
    text = "📜 **Mavjud promo kodlar:**\n\n"
    kb = []
    if promos:
        for p_id, code, disc, active, expiry in promos:
            text += f"- {code}: {disc}% ({'Faol' if active else 'No-faol'})\n"
            # Delete button only for super admin
            if is_super:
                kb.append([InlineKeyboardButton(text=f"❌ {code} ni o'chirish", callback_data=f"admin_pdel_{p_id}")])
    else:
        text += "Hozircha promo kodlar yo'q."
    
    if not is_super:
        text += "\n\n💡 _Promo kodlarni qo'shish/o'chirish uchun super admin bo'lishingiz kerak._"
    
    kb.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_promo_manage")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_pdel_"))
async def admin_promo_delete(callback: types.CallbackQuery):
    # Only Super Admin can delete promo codes
    admin = db.get_admin(callback.from_user.id)
    if not admin or admin[1] != 'super_admin':
        return await callback.answer("❌ Faqat super admin promo kodini o'chira oladi!", show_alert=True)
    p_id = int(callback.data.split("_")[2])
    db.delete_promo_code(p_id)
    await callback.message.answer("✅ Promo kod o'chirildi.")
    await admin_list_promo(callback)

# --- Mailing Handlers ---
@router.callback_query(F.data == "admin_send_mail")
async def admin_send_mail_start(callback: types.CallbackQuery, state: FSMContext):
    if not db.has_permission(callback.from_user.id, 'mailing'):
        return await callback.answer("Ruxsat yo'q.", show_alert=True)
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

@router.callback_query(F.data == "admin_mail_confirm", AdminStates.mailing_preview)
async def admin_mail_confirm(callback: types.CallbackQuery, state: FSMContext):
    if not db.has_permission(callback.from_user.id, 'mailing'):
        return await callback.answer("Ruxsat yo'q.", show_alert=True)
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
    user_id = callback.from_user.id
    lang = db.get_user_lang(user_id)
    is_admin = (user_id in (SUPER_ADMINS + WORKERS)) and bool(db.get_admin(user_id))
    await callback.message.answer("🏠 Foydalanuvchi menyusiga qaytdingiz.", reply_markup=main_menu(lang, is_admin))
    await callback.answer()

# ... (rest of existing worker order handlers) ...

async def generate_excel_report():
    import pandas as pd
    orders = db.get_all_orders()
    columns = [
        'ID', 'User ID', 'Mijoz Ismi', 'Username', 'Tel', 
        'Mahsulotlar', 'Jami Summa', 'Promo Kod', 'Chegirma', 
        'Usul', 'Manzil/Location', 'Holat', 'Sana'
    ]
    df = pd.DataFrame(orders, columns=columns)
    file_path = "yummy_report.xlsx"
    df.to_excel(file_path, index=False)
    return file_path

@router.message(Command("report"))
@router.callback_query(F.data == "admin_report")
@router.callback_query(F.data == "admin_report")
async def get_report_callback(event: types.Message | types.CallbackQuery):
    if not db.has_permission(event.from_user.id, 'stats'):
        if isinstance(event, types.CallbackQuery):
            await event.answer("Ruxsat yo'q.", show_alert=True)
        return
    message = event if isinstance(event, types.Message) else event.message
    try:
        file_path = await generate_excel_report()
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

    from keyboards.user_keyboards import main_menu
    is_admin = (user_id in (SUPER_ADMINS + WORKERS)) and bool(db.get_admin(user_id))
    await callback.message.edit_text(callback.message.text + "\n\n❌ Rejected")
    await callback.bot.send_message(user_id, s['order_cancelled'], reply_markup=main_menu(lang, is_admin), parse_mode="Markdown")
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

    from keyboards.user_keyboards import main_menu
    is_admin = (user_id in (SUPER_ADMINS + WORKERS)) and bool(db.get_admin(user_id))
    await callback.message.edit_text(callback.message.text + "\n\n🏁 Completed")
    await callback.bot.send_message(user_id, s['sms_completed'].format(id=order_id), reply_markup=main_menu(lang, is_admin), parse_mode="Markdown")
    await callback.answer()
