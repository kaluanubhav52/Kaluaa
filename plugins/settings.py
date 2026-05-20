
#Codeflix_Botz
#rohit_1888 on Tg

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from database import db # Aapka updated async database class link
from config import ADMINS # Ya jo bhi aapki admin list variable hai config me

# ----------------- LAYER 1: MAIN MENU KEYBOARD ----------------- #
async def get_main_menu_keyboard():
    settings = await db.get_bot_settings()
    
    # 1. Start Photo Button Logic
    if settings.get("start_photo"):
        photo_text = "❌ Remove Start Photo"
        photo_callback = "cb_toggle:start_photo"
    else:
        photo_text = "🖼️ Add Start Photo"
        photo_callback = "cb_toggle:start_photo" # Photo validation step
        
    # 2. Verification Button Logic
    v_status = "✅ ON" if settings.get("verification") else "❌ OFF"
    v_text = f"🛡️ Verification: {v_status}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(photo_text, callback_data=photo_callback)],
        [InlineKeyboardButton(v_text, callback_data="cb_toggle:verification")],
        [InlineKeyboardButton(f"🕒 Time: {settings.get('token_time', '24 Hours')}", callback_data="cb_cycle:token_time")],
        # Multi-layer Entry Button 👇
        [InlineKeyboardButton("👑 Manage Plans & Premium 👑", callback_data="layer:plans")],
        [InlineKeyboardButton("⚙️ Close Panel ⚙️", callback_data="cb_action:close")]
    ])
    return keyboard


# ----------------- LAYER 2: PLANS SUB-MENU KEYBOARD ----------------- #
async def get_plans_menu_keyboard():
    settings = await db.get_bot_settings()
    
    p_status = "✅ ON" if settings.get("premium_mode") else "❌ OFF"
    p_text = f"⭐ Premium Mode: {p_status}"
    
    current_plan = settings.get("active_plan_type", "Free")
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(p_text, callback_data="cb_toggle:premium_mode")],
        [
            InlineKeyboardButton(f"🔹 Free {'🟢' if current_plan == 'Free' else ''}", callback_data="set_plan:Free"),
            InlineKeyboardButton(f"🔶 VIP {'🟢' if current_plan == 'VIP' else ''}", callback_data="set_plan:VIP")
        ],
        [InlineKeyboardButton(f"👑 Premium Pack {'🟢' if current_plan == 'Premium' else ''}", callback_data="set_plan:Premium")],
        # Back Button to Layer 1 👇
        [InlineKeyboardButton("🔙 Back to Main Settings", callback_data="layer:main")]
    ])
    return keyboard


# -------------------- COMMAND HANDLER -------------------- #
@Client.on_message(filters.command("settings") & filters.private)
async def open_settings_panel(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Security check: Only admins can manage global panel
    # Aap isse filters.user(ADMINS) se bhi handle kar sakte hain command layer par
    if not await db.admin_exist(user_id):
        return await message.reply_text("❌ This panel is restricted for Authorized Admins only.")

    text = (
        "╔════════════════════╗\n"
        "║       ⚙️ **BOT SETTINGS MANAGER** ⚙️      ║\n"
        "╚════════════════════╝\n\n"
        "Welcome to the central control node. Modify operational logic live:"
    )
    reply_markup = await get_main_menu_keyboard()
    await message.reply_text(text, reply_markup=reply_markup)


# -------------------- CALLBACK MANAGER -------------------- #
@Client.on_callback_query(filters.regex(r"^(layer:|cb_toggle:|cb_cycle:|cb_action:|set_plan:)"))
async def core_settings_callback(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    # Secure callback check
    if not await db.admin_exist(user_id):
        return await callback_query.answer("⚠️ Unauthorized access denied.", show_alert=True)
        
    settings = await db.get_bot_settings()

    # --- 1. LAYER / SCREEN SWITCHING ---
    if data == "layer:main":
        text = "⚙️ **Main Core Config Panel:**"
        reply_markup = await get_main_menu_keyboard()
        await callback_query.message.edit_text(text, reply_markup=reply_markup)
        return
        
    elif data == "layer:plans":
        text = "👑 **Plan & Tier Sub-Structure Menu:**\n\nConfigure premium gates or switch active deployment plans."
        reply_markup = await get_plans_menu_keyboard()
        await callback_query.message.edit_text(text, reply_markup=reply_markup)
        return

    # --- 2. CORE ACTION & TOGGLES ---
    elif data.startswith("cb_toggle:"):
        key = data.split(":")[1]
        
        # Specially handling photos since it's mixed with validation
        if key == "start_photo":
            if settings.get("start_photo"):
                await db.update_bot_setting("start_photo", None)
                await callback_query.answer("🗑️ Start Photo template dropped completely.", show_alert=True)
            else:
                # Agar aapko custom photo flow chalana ho toh force reply handle laga sakte ho.
                # Abhi hum direct state toggle kar rahe hain with a default simulation trigger:
                await db.update_bot_setting("start_photo", "AgACAgQAAxkBA...") 
                await callback_query.answer("🖼️ Mock Start Photo asset set successfully!", show_alert=True)
        else:
            # For general booleans (Verification, Premium Mode)
            current_status = settings.get(key, False)
            await db.update_bot_setting(key, not current_status)
            await callback_query.answer(f"🔄 '{key.upper()}' Status Toggled Successfully.")

    elif data.startswith("cb_cycle:"):
        # Cycle through custom verification token expiration windows
        times = ["1 Hour", "12 Hours", "24 Hours", "48 Hours"]
        curr_time = settings.get("token_time", "24 Hours")
        next_idx = (times.index(curr_time) + 1) % len(times) if curr_time in times else 2
        
        await db.update_bot_setting("token_time", times[next_idx])
        await callback_query.answer(f"🕒 Verification Expiry Token window shifted: {times[next_idx]}")
        
    elif data.startswith("set_plan:"):
        target_plan = data.split(":")[1]
        await db.update_bot_setting("active_plan_type", target_plan)
        await callback_query.answer(f"👑 Global Plan Matrix re-routed to: {target_plan}")

    elif data == "cb_action:close":
        await callback_query.message.delete()
        return

    # --- 3. DYNAMIC UI RE-RENDERING PIPELINE ---
    # Refresh check to make sure the same screen rendering remains active
    if "layer:plans" in callback_query.message.reply_markup.inline_keyboard[-1][0].callback_data or "set_plan:" in data or "premium_mode" in data:
        text = "👑 **Plan & Tier Sub-Structure Menu:**\n\nConfigure premium gates or switch active deployment plans."
        reply_markup = await get_plans_menu_keyboard()
    else:
        text = "⚙️ **Main Core Config Panel:**"
        reply_markup = await get_main_menu_keyboard()
        
    try:
        await callback_query.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        pass # To prevent flood if content is identical
