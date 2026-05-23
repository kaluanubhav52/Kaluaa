from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ForceReply
from database.database import *
from config import *
from bot import Bot

# Dynamic State Storage
ASK_TIME, ASK_URL, ASK_API = 101, 102, 103
admin_states = {}

# Admin Validation Filter
def admin_filter(_, __, message: Message):
    try:
        return message.from_user.id == int(OWNER_ID)
    except:
        return message.from_user.id == 5898522531  # Backup Admin ID

is_admin = filters.create(admin_filter)

# ⚙️ 1. Main Dashboard Command
@Bot.on_message(filters.command("settings") & filters.private & is_admin, group=-5)
async def settings_panel(client: Client, message: Message):
    settings = await db.get_bot_settings()
    v_mode = "🟢 ENABLED" if settings.get("verify_mode", True) else "🔴 DISABLED"
    
    btn = [
        [InlineKeyboardButton(f"Verification Switch: {v_mode}", callback_data="toggle_verify")],
        [InlineKeyboardButton("📝 Set Shortener URL", callback_data="set_url"),
         InlineKeyboardButton("🔑 Set API Key", callback_data="set_api")],
        [InlineKeyboardButton("⏳ Set Expiry Time", callback_data="set_time")],
        [InlineKeyboardButton("❌ Close Panel", callback_data="close_settings")]
    ]
    await message.reply_text(
        "⚙️ **DYNAMIC BOT SETTINGS PANEL**\n\n"
        "Yahan se aap bina bot restart kiye shortlink configuration control kar sakte hain.", 
        reply_markup=InlineKeyboardMarkup(btn)
    )

# ❌ 2. Cancel Command
@Bot.on_message(filters.command("cancel") & filters.private & is_admin, group=-10)
async def cancel_input(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in admin_states:
        del admin_states[user_id]
        await message.reply_text("❌ **Setting process ko cancel kar diya gaya hai.**")
        message.stop_propagation()
    else:
        await message.reply_text("Pehle se koi setting change process active nahi hai.")

# 📊 3. Callbacks Handle
@Bot.on_callback_query(filters.regex(r"^(toggle_verify|set_url|set_api|set_time|close_settings|admin_settings_menu)$"))
async def handle_settings_callbacks(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    
    if data == "admin_settings_menu":
        if query.from_user.id != int(OWNER_ID) and query.from_user.id != 5898522531:
            await query.answer("⚠️ Yeh panel sirf Bot Admin ke liye hai.", show_alert=True)
            return
            
        settings = await db.get_bot_settings()
        v_mode = "🟢 ENABLED" if settings.get("verify_mode", True) else "🔴 DISABLED"
        
        btn = [
            [InlineKeyboardButton(f"Verification Switch: {v_mode}", callback_data="toggle_verify")],
            [InlineKeyboardButton("📝 Set Shortener URL", callback_data="set_url"),
             InlineKeyboardButton("🔑 Set API Key", callback_data="set_api")],
            [InlineKeyboardButton("⏳ Set Expiry Time", callback_data="set_time")],
            [InlineKeyboardButton("❌ Close Panel", callback_data="close_settings")]
        ]
        await query.message.edit_text(
            "⚙️ **DYNAMIC BOT SETTINGS PANEL**\n\n"
            "Yahan se aap bina bot restart kiye shortlink configuration control kar sakte hain.", 
            reply_markup=InlineKeyboardMarkup(btn)
        )
        await query.answer()
        return

    if data == "toggle_verify":
        settings = await db.get_bot_settings()
        current_mode = settings.get("verify_mode", True)
        new_mode = not current_mode
        
        # FIXED: Aapke positional argument ('key', value) format ke hisab se change kiya
        await db.update_bot_settings("verify_mode", new_mode)
        status_txt = "🟢 ENABLED" if new_mode else "🔴 DISABLED"
        await query.answer(f"Verification Mode turned {status_txt}!", show_alert=True)
        
        btn = [
            [InlineKeyboardButton(f"Verification Switch: {status_txt}", callback_data="toggle_verify")],
            [InlineKeyboardButton("📝 Set Shortener URL", callback_data="set_url"),
             InlineKeyboardButton("🔑 Set API Key", callback_data="set_api")],
            [InlineKeyboardButton("⏳ Set Expiry Time", callback_data="set_time")],
            [InlineKeyboardButton("❌ Close Panel", callback_data="close_settings")]
        ]
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(btn))

    elif data == "set_url":
        admin_states[user_id] = ASK_URL
        await query.message.reply_text(
            "📝 **Sᴇᴛ Sʜᴏʀᴛᴇɴᴇʀ URL:**\n\nNaya domain name bhejein (e.g. `linkshortify.com`).\n\nTo stop this process send: /cancel",
            reply_markup=ForceReply(selective=True)
        )
        await query.answer()
        
    elif data == "set_api":
        admin_states[user_id] = ASK_API
        await query.message.reply_text(
            "🔑 **Sᴇᴛ Sʜᴏʀᴛᴇɴᴇʀ API KEY:**\n\nApni nayi API Key yahan send karein.\n\nTo stop this process send: /cancel",
            reply_markup=ForceReply(selective=True)
        )
        await query.answer()
        
    elif data == "set_time":
        admin_states[user_id] = ASK_TIME
        await query.message.reply_text(
            "⏳ **Sᴇᴛ Tᴏᴋᴇɴ Exᴘɪʀʏ Tɪᴍᴇ:**\n\nToken validity seconds me bhejein (e.g. `180`).\n\nTo stop this process send: /cancel",
            reply_markup=ForceReply(selective=True)
        )
        await query.answer()
        
    elif data == "close_settings":
        await query.message.delete()
        await query.answer("Panel Closed.")

# 📥 4. HIGH PRIORITY INPUT HANDLER (Group -100)
@Bot.on_message(filters.text & filters.private & is_admin, group=-2)
async def handle_admin_inputs(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in admin_states:
        return
        
    state = admin_states[user_id]
    input_text = message.text.strip()
    
    if input_text.startswith("/cancel"):
        return

    if state == ASK_URL:
        clean_url = input_text.replace("https://", "").replace("http://", "").split("/")[0]
        # FIXED: Calling style changed to positional key-value
        await db.update_bot_settings("shortener_url", clean_url)
        await message.reply_text(f"✅ **Shortener URL successfully updated to:** `{clean_url}`")
        del admin_states[user_id]
        message.stop_propagation()
        
    elif state == ASK_API:
        # FIXED: Calling style changed to positional key-value
        await db.update_bot_settings("shortener_api", input_text)
        await message.reply_text(f"✅ **Shortener API Key successfully updated!**")
        del admin_states[user_id]
        message.stop_propagation()
        
    elif state == ASK_TIME:
        try:
            seconds = int(input_text)
            # FIXED: Calling style changed to positional key-value
            await db.update_bot_settings("verify_time", seconds)
            await message.reply_text(f"✅ **Token Expiry Time successfully updated to:** `{seconds}` seconds.")
            del admin_states[user_id]
            message.stop_propagation()
        except ValueError:
            await message.reply_text("❌ **Invalid Input!** Kripya sirf ek valid number (seconds me) reply karein ya process rokne ke liye `/cancel` likhein:")
            message.stop_propagation()
