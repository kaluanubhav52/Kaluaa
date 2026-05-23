from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.database import *
from config import *
from bot import Bot


# Unique State Management for Admin Inputs
ASK_TIME, ASK_URL, ASK_API = 101, 102, 103
user_states = {}

# Admin Validation Filter
def admin_filter(_, __, message: Message):
    try:
        return message.from_user.id == int(OWNER_ID)
    except:
        return message.from_user.id == 5898522531  # Aapka back-up Admin ID

is_admin = filters.create(admin_filter)

# ⚙️ 1. Main Dashboard Command (Group -1: Priority handler)
@Bot.on_message(filters.command("settings") & filters.private & is_admin, group=-1)
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

# 📊 2. All Callbacks Handle karne ke liye (Start button callback 'admin_settings_menu' added)
@Bot.on_callback_query(filters.regex(r"^(toggle_verify|set_url|set_api|set_time|close_settings|admin_settings_menu)$"))
async def handle_settings_callbacks(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    
    # 🔐 Security Check: Agar koi normal banda start menu ke settings button par click kare
    if data == "admin_settings_menu":
        if query.from_user.id != int(OWNER_ID) and query.from_user.id != 5898522531:
            await query.answer("⚠️ Ghabraiye nahi! Yeh panel sirf Bot Admin ke liye hai.", show_alert=True)
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

    # 🔄 Verification Switch Toggle Logic
    if data == "toggle_verify":
        settings = await db.get_bot_settings()
        current_mode = settings.get("verify_mode", True)
        new_mode = not current_mode
        
        # Database me configuration key update karna
        await db.update_bot_settings(verify_mode=new_mode)
        status_txt = "🟢 ENABLED" if new_mode else "🔴 DISABLED"
        await query.answer(f"Verification Mode turned {status_txt}!", show_alert=True)
        
        # Fresh UI render bina message jump kiye
        btn = [
            [InlineKeyboardButton(f"Verification Switch: {status_txt}", callback_data="toggle_verify")],
            [InlineKeyboardButton("📝 Set Shortener URL", callback_data="set_url"),
             InlineKeyboardButton("🔑 Set API Key", callback_data="set_api")],
            [InlineKeyboardButton("⏳ Set Expiry Time", callback_data="set_time")],
            [InlineKeyboardButton("❌ Close Panel", callback_data="close_settings")]
        ]
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(btn))

    elif data == "set_url":
        user_states[user_id] = ASK_URL
        await query.message.reply_text("📝 **Sᴇᴛ Sʜᴏʀᴛᴇɴᴇʀ URL:**\n\nApna naya shortener domain bhejein.\nExample: `linkshortify.com`")
        await query.answer()
        
    elif data == "set_api":
        user_states[user_id] = ASK_API
        await query.message.reply_text("🔑 **Sᴇᴛ Sʜᴏʀᴛᴇɴᴇʀ API KEY:**\n\nApni nayi API Key copy karke yahan send karein.")
        await query.answer()
        
    elif data == "set_time":
        user_states[user_id] = ASK_TIME
        await query.message.reply_text("⏳ **Sᴇᴛ Tᴏᴋᴇɴ Exᴘɪʀʏ Tɪᴍᴇ:**\n\nToken ki validity kitne seconds rakhni hai? (Sirf number bhejein)\nExample: `3600` (1 Ghanta)")
        await query.answer()
        
    elif data == "close_settings":
        await query.message.delete()
        await query.answer("Panel Closed.")

# 📥 3. Admin Input Messages Process karne ke liye (Group -2: Intercepts before general text handlers)
@Bot.on_message(filters.text & filters.private & is_admin, group=-2)
async def handle_admin_inputs(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return 
    
    state = user_states[user_id]
    input_text = message.text.strip()
    
    if state == ASK_URL:
        # Extra spacing aur secure prefixes clean karne ke liye
        clean_url = input_text.replace("https://", "").replace("http://", "").split("/")[0]
        await db.update_bot_settings(shortener_url=clean_url)
        await message.reply_text(f"✅ **Shortener URL successfully updated to:** `{clean_url}`")
        del user_states[user_id]
        message.stop_propagation() 
        
    elif state == ASK_API:
        await db.update_bot_settings(shortener_api=input_text)
        await message.reply_text(f"✅ **Shortener API Key successfully updated!**")
        del user_states[user_id]
        message.stop_propagation()
        
    elif state == ASK_TIME:
        try:
            seconds = int(input_text)
            await db.update_bot_settings(verify_time=seconds)
            await message.reply_text(f"✅ **Token Expiry Time successfully updated to:** `{seconds}` seconds.")
            del user_states[user_id]
            message.stop_propagation()
        except ValueError:
            await message.reply_text("❌ **Invalid Input!** Kripya sirf ek valid number (seconds me) bhejein. Dobara koshish karein:")
            message.stop_propagation()
