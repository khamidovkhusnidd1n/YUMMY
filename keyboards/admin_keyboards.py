from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def admin_profile_kb(is_super=False):
    kb = []
    kb.append([InlineKeyboardButton(text="Dashboard", callback_data="admin_dashboard")])
    kb.append([InlineKeyboardButton(text="Buyurtmalar", callback_data="admin_orders")])
    if is_super:
        kb.append([InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")])
        kb.append([InlineKeyboardButton(text="📈 Analitika", callback_data="admin_analytics")])
        kb.append([InlineKeyboardButton(text="🍴 Menu Boshqaruvi", callback_data="admin_menu_manage")])
        kb.append([InlineKeyboardButton(text="📑 Excel Hisobot", callback_data="admin_report")])
        kb.append([InlineKeyboardButton(text="Adminlar", callback_data="admin_admins")])
    else:
        kb.append([InlineKeyboardButton(text="📦 Buyurtmalar (Worker)", callback_data="worker_info")])
    
    kb.append([InlineKeyboardButton(text="🏠 Foydalanuvchi menyusi", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_reply_menu():
    kb = [
        [KeyboardButton(text="🏠 Foydalanuvchi menyusi")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)

def menu_manage_kb():
    kb = [
        [InlineKeyboardButton(text="Taom qo'shish", callback_data="menu_add_product")],
        [InlineKeyboardButton(text="Kategoriyalar", callback_data="menu_view_cats")],
        [InlineKeyboardButton(text="Tugallash", callback_data="menu_finish")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def order_initial_kb(order_id):
    kb = [[
        InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_{order_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{order_id}")
    ]]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def order_next_stage_kb(order_id, current_stage):
    if current_stage == "accepted":
        kb = [[InlineKeyboardButton(text="👨‍🍳 Tayyorlanmoqda", callback_data=f"preparing_{order_id}")]]
    elif current_stage == "preparing":
        kb = [[InlineKeyboardButton(text="🚴 Yetkazilmoqda", callback_data=f"delivering_{order_id}")]]
    elif current_stage == "delivering":
        kb = [[InlineKeyboardButton(text="🏁 Yakunlash", callback_data=f"complete_{order_id}")]]
    else:
        return None
    return InlineKeyboardMarkup(inline_keyboard=kb)
