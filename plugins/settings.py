#Codeflix_Botz
#AC FILE SHARING BOT

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from database import db

# ══════════════════════════════════════════════════
#              DYNAMIC KEYBOARDS GENERATOR          
# ══════════════════════════════════════════════════

async def get_main_panel():
    """LAYER 1: Main Config Dashboard"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 PREMIUM PLAN", callback_data="layer:premium")],
        [InlineKeyboardButton("🔗 LINK SHORTNER", callback_data="layer:shortner")],
        [InlineKeyboardButton("🛡️ TOKEN VERIFICATION", callback_data="layer:token")], # Direct Verification par le jayega
        [InlineKeyboardButton("📝 CUSTOM CAPTION", callback_data="layer:caption")],
        [InlineKeyboardButton("📢 CUSTOM FORCE SUBSCRIBE", callback_data="layer:fsub")],
        [InlineKeyboardButton("🖼️ CUSTOM THUMBNAIL", callback_data="layer:thumbnail")],
        [InlineKeyboardButton("🔘 CUSTOM BUTTON", callback_data="layer:cbutton")],
        [InlineKeyboardButton("🗑️ AUTO DELETE", callback_data="layer:autodel")],
        [InlineKeyboardButton("🔒 PROTECT CONTENT", callback_data="layer:protect")],
        [InlineKeyboardButton("📥 STREAM AND DOWNLOAD", callback_data="layer:stream")],
        [InlineKeyboardButton("❌ CLOSE PANEL ❌", callback_data="action:close")]
    ])
    return keyboard


async def get_first_verify_panel():
    """LAYER 2: First Token Verification Details (No 2nd/3rd Layer)"""
    settings = await db.get_bot_settings()
    status_emoji = "✅" if settings.get("first_verify", False) else "❌"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 FIRST VERIFY SHORTNER", callback_data="action:set_shortner")],
        [InlineKeyboardButton("📖 FIRST VERIFY TUTORIAL", callback_data="action:set_tutorial")],
        [InlineKeyboardButton(f"🕒 FIRST VERIFY TIME: {settings.get('first_verify_time', '24 Hours')}", callback_data="cycle:vtime")],
        [InlineKeyboardButton("📊 TOTAL USER VERIFIED TODAY", callback_data="action:stats")],
        [InlineKeyboardButton(f"⚙️ FIRST VERIFY - {status_emoji}", callback_data="toggle:first_verify")],
        [InlineKeyboardButton("🔙 BACK", callback_data="layer:main")] # Direct Main Menu par wapas layega
    ])
    return keyboard


async def get_premium_panel():
    """LAYER 2: Premium Sub-Menu"""
    settings = await db.get_bot_settings()
    p_status = "✅ ON" if settings.get("premium_mode", False) else "❌ OFF"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 PREMIUM PLAN MESSAGE", callback_data="action:prem_msg")],
        [InlineKeyboardButton("➕ ADD PREMIUM USER ➕", callback_data="action:add_prem")],
        [InlineKeyboardButton("➖ REMOVE PREMIUM USER ➖", callback_data="action:rem_prem")],
        [InlineKeyboardButton("👥 PREMIUM USERS LIST", callback_data="action:list_prem")],
        [InlineKeyboardButton(f"👑 PREMIUM IS ON - {p_status}", callback_data="toggle:premium_mode")],
        [InlineKeyboardButton("🔙 BACK", callback_data="layer:main")]
    ])
    return keyboard

# ══════════════════════════════════════════════════
#                   CORE COMMAND HANDLER            
# ══════════════════════════════════════════════════

@Client.on_message(filters.command("settings") & filters.private)
async def open_settings_hub(client: Client, message: Message):
    if not await db.admin_exist(message.from_user.id):
        return
        
    text = (
        "⚙️ **SETTINGS:**\n\n"
        "CUSTOMIZE YOUR SETTINGS AS PER YOUR NEED."
    )
    await message.reply_text(text, reply_markup=await get_main_panel())

# ══════════════════════════════════════════════════
#                 CALLBACK GRAPH DISPATCHER         
# ══════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^(layer:|toggle:|cycle:|action:)"))
async def process_settings_graph(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if not await db.admin_exist(user_id):
        return await callback_query.answer("⚠️ Access Denied.", show_alert=True)
        
    settings = await db.get_bot_settings()

    # --- 1. LAYER NAVIGATION ---
    if data == "layer:main":
        text = "⚙️ **SETTINGS:**\n\nCUSTOMIZE YOUR SETTINGS AS PER YOUR NEED."
        return await callback_query.message.edit_text(text, reply_markup=await get_main_panel())
        
    elif data == "layer:token":
        # Direct First Verification par switch karega (Bina 2nd/3rd choice dikhaye)
        text = (
            "🥇 **FIRST TOKEN VERIFICATION SETTINGS:**\n\n"
            "Manage your link shorteners, tutorial tracks, and time bounds below:"
        )
        return await callback_query.message.edit_text(text, reply_markup=await get_first_verify_panel())
        
    elif data == "layer:premium":
        msg_text = settings.get("premium_message", "PREMIUM PLAN DETAILS NOT DEFINED.")
        text = f"👑 **PREMIUM PLAN:**\n\n`{msg_text}`"
        return await callback_query.message.edit_text(text, reply_markup=await get_premium_panel())

    # --- 2. BOOLEAN TOGGLES ---
    elif data.startswith("toggle:"):
        key = data.split(":")[1]
        current_state = settings.get(key, False)
        await db.update_bot_setting(key, not current_state)
        await callback_query.answer("🔄 Status Updated Live!")

    # --- 3. VALUE CYCLES ---
    elif data == "cycle:vtime":
        intervals = ["1 Hour", "12 Hours", "24 Hours", "48 Hours"]
        curr = settings.get("first_verify_time", "24 Hours")
        nxt = intervals[(intervals.index(curr) + 1) % len(intervals)] if curr in intervals else "24 Hours"
        await db.update_bot_setting("first_verify_time", nxt)
        await callback_query.answer(f"🕒 Expiry set to {nxt}")

    # --- 4. DATA INPUT HANDLES ---
    elif data in ["action:add_prem", "action:rem_prem", "action:set_shortner", "action:set_tutorial"]:
        await callback_query.answer()
        cancel_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="layer:main")]])
        return await callback_query.message.edit_text(
            "ℹ️ **NOW SEND ME USER ID / URL VALUE:**\n\nSend `/cancel` to abort this process.", 
            reply_markup=cancel_markup
        )

    elif data == "action:close":
        return await callback_query.message.delete()

    # --- UI RE-RENDER REFRESHER ---
    # Refresh logic taaki switches click hone ke baad admin usi page par rahe
    if "first_verify" in data or "vtime" in data:
        await callback_query.message.edit_text("🥇 **FIRST TOKEN VERIFICATION SETTINGS:**", reply_markup=await get_first_verify_panel())
    elif "premium" in data:
        msg_text = settings.get("premium_message", "PREMIUM PLAN DETAILS NOT DEFINED.")
        await callback_query.message.edit_text(f"👑 **PREMIUM PLAN:**\n\n`{msg_text}`", reply_markup=await get_premium_panel())
