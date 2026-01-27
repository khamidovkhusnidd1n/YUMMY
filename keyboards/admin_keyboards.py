from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def admin_profile_kb(is_super=False):
    kb = []
    kb.append([
        InlineKeyboardButton(text="📊 Dashboard", callback_data="admin_dashboard"),
        InlineKeyboardButton(text="🛍 Buyurtmalar", callback_data="admin_orders")
    ])
    
    if is_super:
        kb.append([InlineKeyboardButton(text="🍽 Menu Boshqaruvi", callback_data="admin_menu_manage")])
        kb.append([
            InlineKeyboardButton(text="🎟 Promolar", callback_data="admin_promo_manage"),
            InlineKeyboardButton(text="📢 Mailing", callback_data="admin_mailing")
        ])
        kb.append([
            InlineKeyboardButton(text="📉 Statistika", callback_data="admin_stats"),
            InlineKeyboardButton(text="📑 Hisobot (Excel)", callback_data="admin_report")
        ])
        kb.append([InlineKeyboardButton(text="👥 Adminlar Boshqaruvi", callback_data="admin_admins")])
    else:
        kb.append([InlineKeyboardButton(text="📦 Buyurtmalar (Worker)", callback_data="worker_info")])
    
    kb.append([InlineKeyboardButton(text="🏠 Foydalanuvchi menyusi", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_reply_menu(is_super=False):
    kb = []
    kb.append([KeyboardButton(text="📊 Dashboard"), KeyboardButton(text="🛍 Buyurtmalar")])
    if is_super:
        kb.append([KeyboardButton(text="🍽 Menu Boshqaruvi")])
        kb.append([KeyboardButton(text="🎟 Promolar"), KeyboardButton(text="📢 Mailing")])
    kb.append([KeyboardButton(text="🏠 Foydalanuvchi menyusi")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def menu_manage_kb():
    kb = [
        [InlineKeyboardButton(text="➕ Yangi taom qo'shish", callback_data="admin_add_prod")],
        [InlineKeyboardButton(text="✏️ Narxlarni tahrirlash", callback_data="admin_edit_price")],
        [InlineKeyboardButton(text="🗑 Taomni o'chirish", callback_data="admin_del_prod")],
        [InlineKeyboardButton(text="🔙 Asosiy panel", callback_data="admin_dashboard_home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def menu_manage_reply_kb():
    kb = [
        [KeyboardButton(text="➕ Yangi taom qo'shish")],
        [KeyboardButton(text="✏️ Narxlarni tahrirlash"), KeyboardButton(text="🗑 Taomni o'chirish")],
        [KeyboardButton(text="🔙 Asosiy panel")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def promo_manage_kb():
    kb = [
        [InlineKeyboardButton(text="➕ Promo qo'shish", callback_data="admin_add_promo")],
        [InlineKeyboardButton(text="📜 Promolar ro'yxati", callback_data="admin_list_promo")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_dashboard")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def mailing_kb():
    kb = [
        [InlineKeyboardButton(text="📝 Xabar yuborish", callback_data="admin_send_mail")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_dashboard")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def cancel_kb():
    kb = [[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def category_list_kb(categories):
    kb = []
    for cat in categories:
        kb.append([InlineKeyboardButton(text=cat[1], callback_data=f"admin_cat_{cat[0]}")])
    kb.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def product_list_kb(products, action_prefix="admin_pselect_"):
    kb = []
    for prod in products:
        kb.append([InlineKeyboardButton(text=f"{prod[2]} ({prod[3]} so'm)", callback_data=f"{action_prefix}{prod[0]}")])
    kb.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_menu_manage")])
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
