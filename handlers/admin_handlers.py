from aiogram import Router, F, types
from aiogram.filters import Command
from database import db
from keyboards.admin_keyboards import order_initial_kb, order_next_stage_kb
from config import SUPER_ADMINS, ALL_ADMINS, WORKERS
from translations import STRINGS
import os

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
async def admin_dashboard_callback(callback: types.CallbackQuery):
    text = build_admin_dashboard_text(callback.from_user.id)
    await callback.message.answer(text, parse_mode="Markdown")
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
async def show_analytics_callback(callback: types.CallbackQuery):
    top_products = db.get_top_products()
    top_customers = db.get_top_customers()
    
    text = "📈 **Kengaytirilgan Analitika**\n\n"
    
    text += "🍱 **Eng ko'p sotilgan taomlar:**\n"
    if top_products:
        for items, count in top_products:
            # Simple cleaning for display
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
        
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_menu_manage", F.from_user.id.in_(SUPER_ADMINS))
async def menu_manage_start(callback: types.CallbackQuery):
    from keyboards.admin_keyboards import menu_manage_kb
    await callback.message.answer("🍴 **Menu Boshqaruvi**\n\nBu yerdan taomlar qo'shishingiz yoki mavjudlarini o'zgartirishingiz mumkin.", reply_markup=menu_manage_kb())
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: types.CallbackQuery):
    from keyboards.user_keyboards import main_menu
    lang = db.get_user_lang(callback.from_user.id)
    await callback.message.answer("🏠 Foydalanuvchi menyusiga qaytdingiz.", reply_markup=main_menu(lang, is_admin=True))
    await callback.answer()

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
