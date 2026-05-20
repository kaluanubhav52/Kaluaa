# Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Premium Inline Settings Plugin

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import admin  # Sirf admin check ke liye
from database.database import db

# Active configuration state tracking dictionary
user_states = {}

# --- HELPER: Human Readable Time Converter ---
def seconds_to_readable(seconds):
    if seconds >= 3600:
        return f"{seconds // 3600}h"
    return f"{seconds // 60}m"

def readable_to_seconds(time_str):
    value = int(time_str[:-1])
    if time_str.endswith('h'):
        return value * 3600
    return value * 60

# --- KEYBOARD BUILDERS ---

async def get_main_settings_keyboard():
    bot_cfg = await db.get_bot_settings()
    verify_status = "🟢 ON" if bot_cfg.get('is_verify_on', True) else "🔴 OFF"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 PREMIUM PLAN", callback_data="menu_premium")],
        [InlineKeyboardButton("🔗 LINK SHORTNER", callback_data="menu_shortener")],
        [InlineKeyboardButton("⏰ TOKEN VERIFICATION", callback_data="menu_token_verify")],
        [InlineKeyboardButton("📝 CUSTOM CAPTION", callback_data="menu_caption")],
        [InlineKeyboardButton("📢 CUSTOM FORCE SUBSCRIBE", callback_data="menu_fsub")],
        [InlineKeyboardButton("⚙️ CUSTOM BUTTON", callback_data="menu_button")],
        [InlineKeyboardButton("🗑️ AUTO DELETE", callback_data="menu_autodelete")],
        [InlineKeyboardButton("🌐 PERMANENT LINK", callback_data="menu_permalink")],
        [InlineKeyboardButton(f"🔒 PROTECT CONTENT - {verify_status}", callback_data="toggle_protect")], # Static text converted
        [InlineKeyboardButton("◀️ CLOSE MENU", callback_data="close_settings_menu")]
    ])

async def get_token_verify_keyboard():
    bot_cfg = await db.get_bot_settings()
    verify_status = "🟢 ON" if bot_cfg.get('is_verify_on', True) else "🔴 OFF"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 VERIFY SHORTNER URL", callback_data="token_set_shortner")],
        [InlineKeyboardButton("🔑 VERIFY SHORTNER API", callback_data="token_set_api")],
        [InlineKeyboardButton("⏱️ VERIFY TIME", callback_data="token_set_time")],
        [InlineKeyboardButton(f"⚙️ VERIFY IS ON - {verify_status}", callback_data="token_toggle_status")],
        [InlineKeyboardButton("◀️ BACK", callback_data="go_to_main_settings")]
    ])

# --- /settings COMMAND ---

@Client.on_message(filters.command("settings") & filters.private & admin)
async def admin_settings_cmd(client: Client, message: Message):
    text = (
        "**✨ VENOM FILE STORE SETTINGS ✨**\n\n"
        "Customize your bot internal modules directly using inline options given below."
    )
    markup = await get_main_settings_keyboard()
    await message.reply_text(text=text, reply_markup=markup)

# --- CALLBACK CONTROLLERS ---

@Client.on_callback_query(filters.regex(r"^(menu_|go_to_|token_|close_settings_menu)"))
async def settings_callback_router(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    if data == "close_settings_menu":
        user_states.pop(user_id, None)
        await query.message.delete()
        return

    elif data in ["menu_main_settings", "go_to_main_settings"]:
        user_states.pop(user_id, None)
        text = "**✨ VENOM FILE STORE SETTINGS ✨**\n\nCustomize your bot internal modules directly using inline options given below."
        markup = await get_main_settings_keyboard()
        await query.message.edit_text(text=text, reply_markup=markup)

    elif data == "menu_token_verify":
        text = "**🛠️ TOKEN VERIFICATION PANEL**\n\nConfigure your shortener domain, API keys, and expiration limits safely from this window."
        markup = await get_token_verify_keyboard()
        await query.message.edit_text(text=text, reply_markup=markup)

    elif data == "token_toggle_status":
        bot_cfg = await db.get_bot_settings()
        current_status = bot_cfg.get('is_verify_on', True)
        await db.update_bot_setting('is_verify_on', not current_status)
        
        # UI Refresh
        markup = await get_token_verify_keyboard()
        await query.message.edit_text(
            text="**🛠️ TOKEN VERIFICATION PANEL**\n\nConfigure your shortener domain, API keys, and expiration limits safely from this window.",
            reply_markup=markup
        )
        await query.answer("Verification Status Updated Successfully!", show_alert=False)

    elif data == "token_set_shortner":
        user_states[user_id] = "WAITING_FOR_SHORTLINK"
        text = (
            "**✍️ SEND ME YOUR SHORTENER URL**\n\n"
            "**⚠️ FORMAT WARNING:**\n"
            "❌ `https://vjlink.online` (Incorrect)\n"
            "✅ `vjlink.online` (Correct)\n\n"
            "Type `/cancel` to abort this configuration."
        )
        await query.message.edit_text(text=text)

    elif data == "token_set_api":
        user_states[user_id] = "WAITING_FOR_API"
        text = (
            "**🔑 SEND ME YOUR SHORTENER API KEY**\n\n"
            "Paste your developer API key obtained from your shortener website dashboard.\n\n"
            "Type `/cancel` to abort this configuration."
        )
        await query.message.edit_text(text=text)

    elif data == "token_set_time":
        user_states[user_id] = "WAITING_FOR_TIME"
        text = (
            "**⏰ SEND ME THE TOKEN EXPIRATION TIME**\n\n"
            "Specify the lifespan of verified token state.\n"
            "**Examples:** `1h` (1 hour), `15m` (15 minutes), `24h` (24 hours).\n------------\n"
            "Type `/cancel` to abort this configuration."
        )
        await query.message.edit_text(text=text)

# --- CONVERSATION TEXT INPUT HANDLER ---

@Client.on_message(filters.private & filters.incoming, group=-2)
async def settings_input_interceptor(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id]
    text = message.text.strip() if message.text else ""

    if text.lower() == "/cancel":
        user_states.pop(user_id, None)
        await message.reply("❌ **Configuration update cancelled safely.**")
        markup = await get_main_settings_keyboard()
        await message.reply_text("**✨ VENOM FILE STORE SETTINGS ✨**", reply_markup=markup)
        return

    if state == "WAITING_FOR_SHORTLINK":
        if text.startswith("http://") or text.startswith("https://"):
            await message.reply("⚠️ **Format Violation! Do not include protocol tags (`https://`). Just send domain rule (e.g., `vjlink.online`).**")
            return
        
        await db.update_bot_setting('shortlink_url', text)
        user_states.pop(user_id, None)
        await message.reply(f"✅ **Shortener URL set to:** `{text}`")
        
        markup = await get_main_settings_keyboard()
        await message.reply_text("**✨ VENOM FILE STORE SETTINGS ✨**", reply_markup=markup)

    elif state == "WAITING_FOR_API":
        await db.update_bot_setting('shortlink_api', text)
        user_states.pop(user_id, None)
        await message.reply(f"✅ **Shortener API Key updated successfully!**")
        
        markup = await get_main_settings_keyboard()
        await message.reply_text("**✨ VENOM FILE STORE SETTINGS ✨**", reply_markup=markup)

    elif state == "WAITING_FOR_TIME":
        if not text.endswith(('h', 'm')) or not text[:-1].isdigit():
            await message.reply("⚠️ **Invalid Duration Format! Use format standard values like `1h` or `30m`.**")
            return
            
        seconds = readable_to_seconds(text)
        await db.update_bot_setting('verify_expire', seconds)
        user_states.pop(user_id, None)
        await message.reply(f"✅ **Token validation threshold configured to:** `{text}` ({seconds}s)")
        
        markup = await get_main_settings_keyboard()
        await message.reply_text("**✨ VENOM FILE STORE SETTINGS ✨**", reply_markup=markup)
