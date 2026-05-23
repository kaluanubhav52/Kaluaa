
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.database import *
from bot import Bot

# Sirf Admin access ke liye
ADMIN_ID = [5898522531]  # Yahan apna Telegram ID daalein

@Bot.on_message(filters.command("settings") & filters.user(ADMIN_ID))
async def settings_panel(client: Client, message: Message):
    """Main Settings Dashboard"""
    settings = await db.get_bot_settings()
    v_mode = "✅ ON" if settings.get("verify_mode", True) else "❌ OFF"
    
    btn = [
        [InlineKeyboardButton(f"Verification: {v_mode}", callback_data="toggle_verify")],
        [InlineKeyboardButton("Set Shortlink URL", callback_data="set_url"),
         InlineKeyboardButton("Set API Key", callback_data="set_api")],
        [InlineKeyboardButton("Set Verify Time (sec)", callback_data="set_time")],
        [InlineKeyboardButton("Close", callback_data="close_settings")]
    ]
    await message.reply("⚙️ **Bot Settings Panel**\n\nConfigure your bot settings here:", reply_markup=InlineKeyboardMarkup(btn))

@Bot.on_callback_query(filters.regex(r"^(toggle_verify|set_url|set_api|set_time|close_settings)$"))
async def handle_settings_callbacks(client: Client, query: CallbackQuery):
    data = query.data
    
    if data == "toggle_verify":
        current = await db.get_bot_settings()
        new_mode = not current.get("verify_mode", True)
        await db.update_bot_settings(verify_mode=new_mode)
        await query.answer(f"Verification set to {new_mode}")
        # Refresh panel
        await settings_panel_refresh(query)

    elif data in ["set_url", "set_api", "set_time"]:
        # User ko instruct karein ki agla message send kare
        await query.message.reply(f"Please send the new value for: **{data.replace('set_', '').upper()}**")
        # Yahan hum temporary state store kar sakte hain (agar complex ho)
        # Simple tareeke ke liye, next message handler ka wait karein
        await query.message.reply(f"I am waiting for your input for {data}...")
        
    elif data == "close_settings":
        await query.message.delete()

# Refresh Panel Function
async def settings_panel_refresh(query: CallbackQuery):
    settings = await db.get_bot_settings()
    v_mode = "✅ ON" if settings.get("verify_mode", True) else "❌ OFF"
    btn = [
        [InlineKeyboardButton(f"Verification: {v_mode}", callback_data="toggle_verify")],
        [InlineKeyboardButton("Set Shortlink URL", callback_data="set_url"),
         InlineKeyboardButton("Set API Key", callback_data="set_api")],
        [InlineKeyboardButton("Set Verify Time (sec)", callback_data="set_time")],
        [InlineKeyboardButton("Close", callback_data="close_settings")]
    ]
    await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(btn))

# Handle Input Values (Simple State)
@Bot.on_message(filters.reply & filters.user(ADMIN_ID) & filters.text)
async def handle_settings_input(client, message: Message):
    reply_text = message.reply_to_message.text
    
    if "waiting for your input for set_url" in reply_text:
        await db.update_bot_settings(shortener_url=message.text)
        await message.reply("✅ Shortlink URL updated!")
    elif "waiting for your input for set_api" in reply_text:
        await db.update_bot_settings(shortener_api=message.text)
        await message.reply("✅ API Key updated!")
    elif "waiting for your input for set_time" in reply_text:
        try:
            await db.update_bot_settings(verify_time=int(message.text))
            await message.reply("✅ Verify time updated!")
        except:
            await message.reply("❌ Please send a valid number.")
