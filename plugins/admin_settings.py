from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ForceReply
from database.database import *
from config import *
from bot import Bot

# Admin Validation Filter
def admin_filter(_, __, message: Message):
    try:
        return message.from_user.id == int(OWNER_ID)
    except:
        return message.from_user.id == 5898522531  # Aapka back-up Admin ID

is_admin = filters.create(admin_filter)

# ⚙️ 1. Main Dashboard Command
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

# 📊 2. Callbacks Handle karne ke liye
@Bot.on_callback_query(filters.regex(r"^(toggle_verify|set_url|set_api|set_time|close_settings|admin_settings_menu)$"))
async def handle_settings_callbacks(client: Client, query: CallbackQuery):
    data = query.data
    
    # Security Check for start button
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

    if data == "toggle_verify":
        settings = await db.get_bot_settings()
        current_mode = settings.get("verify_mode", True)
        new_mode = not current_mode
        
        await db.update_bot_settings(verify_mode=new_mode)
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

    # 🔥 FORCE REPLY SOLUTIONS: Ab ye buttons input box me reply select kar denge automatic
    elif data == "set_url":
        await query.message.reply_text(
            "📝 **Sᴇᴛ Sʜᴏʀᴛᴇɴᴇʀ URL:**\n\nIs message ka reply karte hue apna domain name bhejein.\nExample: `linkshortify.com`",
            reply_markup=ForceReply(selective=True)
        )
        await query.answer()
        
    elif data == "set_api":
        await query.message.reply_text(
            "🔑 **Sᴇᴛ Sʜᴏʀᴛᴇɴᴇʀ API KEY:**\n\nIs message ka reply karte hue apni API Key send karein.",
            reply_markup=ForceReply(selective=True)
        )
        await query.answer()
        
    elif data == "set_time":
        await query.message.reply_text(
            "⏳ **Sᴇᴛ Tᴏᴋᴇɴ Exᴘɪʀʏ Tɪᴍᴇ:**\n\nIs message ka reply karte hue token validity seconds me bhejein.\nExample: `3600` (1 Ghanta)",
            reply_markup=ForceReply(selective=True)
        )
        await query.answer()
        
    elif data == "close_settings":
        await query.message.delete()
        await query.answer("Panel Closed.")

# 📥 3. Admin Input Messages Process karne ke liye (Ab ye strictly text ki jagah 'reply_to_message' check karega)
@Bot.on_message(filters.text & filters.private & is_admin, group=-2)
async def handle_admin_inputs(client: Client, message: Message):
    # Agar message kisi bot message ka reply nahi hai, toh ignore karo aur baki code chalne do
    if not message.reply_to_message:
        return
        
    reply_text = message.reply_to_message.text
    input_text = message.text.strip()
    
    # Strict dynamic text match jisse koi doosra filter isme tang na adaye
    if "Sᴇᴛ Sʜᴏʀᴛᴇɴᴇʀ URL:" in reply_text:
        clean_url = input_text.replace("https://", "").replace("http://", "").split("/")[0]
        await db.update_bot_settings(shortener_url=clean_url)
        await message.reply_text(f"✅ **Shortener URL successfully updated to:** `{clean_url}`")
        message.stop_propagation() 
        
    elif "Sᴇᴛ Sʜᴏʀᴛᴇɴᴇʀ API KEY:" in reply_text:
        await db.update_bot_settings(shortener_api=input_text)
        await message.reply_text(f"✅ **Shortener API Key successfully updated!**")
        message.stop_propagation()
        
    elif "Sᴇᴛ Tᴏᴋᴇɴ Exᴘɪʀʏ Tɪᴍᴇ:" in reply_text:
        try:
            seconds = int(input_text)
            await db.update_bot_settings(verify_time=seconds)
            await message.reply_text(f"✅ **Token Expiry Time successfully updated to:** `{seconds}` seconds.")
            message.stop_propagation()
        except ValueError:
            await message.reply_text("❌ **Invalid Input!** Kripya sirf ek valid number (seconds me) reply karein:")
            message.stop_propagation()
