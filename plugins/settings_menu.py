# Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Premium Inline Settings Plugin (Fix: Resolved Button Unresponsiveness)

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import OWNER_ID
from database.database import db
from database.db_premium import add_premium, remove_premium, collection
from pytz import timezone
from datetime import datetime

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
        [InlineKeyboardButton(f"🔒 PROTECT CONTENT - {verify_status}", callback_data="toggle_protect")],
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

def get_premium_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ADD PREMIUM USER", callback_data="prem_add_user")],
        [InlineKeyboardButton("❌ REMOVE PREMIUM USER", callback_data="prem_rem_user")],
        [InlineKeyboardButton("📊 TOTAL PREMIUM USERS", callback_data="prem_total_users")],
        [InlineKeyboardButton("◀️ BACK", callback_data="go_to_main_settings")]
    ])

# --- /settings COMMAND (OWNER ONLY CHECK) ---

@Client.on_message(filters.command("settings") & filters.private)
async def admin_settings_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    
    if isinstance(OWNER_ID, list):
        if user_id not in OWNER_ID:
            return
    else:
        if user_id != int(OWNER_ID):
            return

    text = (
        "**✨ VENOM FILE STORE SETTINGS ✨**\n\n"
        "Customize your bot internal modules directly using inline options given below."
    )
    markup = await get_main_settings_keyboard()
    await message.reply_text(text=text, reply_markup=markup)

# --- CALLBACK CONTROLLERS ---

@Client.on_callback_query(filters.regex(r"^(menu_|go_to_|token_|prem_|close_settings_menu)"))
async def settings_callback_router(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    
    if isinstance(OWNER_ID, list):
        if user_id not in OWNER_ID:
            return await query.answer("⚠️ This menu is restricted to Bot Owner only!", show_alert=True)
    else:
        if user_id != int(OWNER_ID):
            return await query.answer("⚠️ This menu is restricted to Bot Owner only!", show_alert=True)

    data = query.data

    if data == "close_settings_menu":
        user_states.pop(user_id, None)
        await query.message.delete()
        return

    # 🛠️ FIX: Edit karne ke bajay purane message ko delete karke naya message bhejenge taaki entities crash na ho
    elif data in ["menu_main_settings", "go_to_main_settings"]:
        user_states.pop(user_id, None)
        text = "**✨ VENOM FILE STORE SETTINGS ✨**\n\nCustomize your bot internal modules directly using inline options given below."
        markup = await get_main_settings_keyboard()
        try:
            await query.message.delete()
        except:
            pass
        await query.message.reply_text(text=text, reply_markup=markup)

    elif data == "menu_token_verify":
        text = "**🛠️ TOKEN VERIFICATION PANEL**\n\nConfigure your shortener domain, API keys, and expiration limits safely from this window."
        markup = await get_token_verify_keyboard()
        try:
            await query.message.delete()
        except:
            pass
        await query.message.reply_text(text=text, reply_markup=markup)

    elif data == "menu_premium":
        text = "**💎 PREMIUM SUBSCRIPTION MANAGEMENT**\n\nAdd/Remove users from the database or check active premium subscriptions from here."
        markup = get_premium_menu_keyboard()
        try:
            await query.message.delete()
        except:
            pass
        await query.message.reply_text(text=text, reply_markup=markup)

    elif data == "token_toggle_status":
        bot_cfg = await db.get_bot_settings()
        current_status = bot_cfg.get('is_verify_on', True)
        await db.update_bot_setting('is_verify_on', not current_status)
        
        markup = await get_token_verify_keyboard()
        try:
            await query.message.delete()
        except:
            pass
        await query.message.reply_text(
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
        try:
            await query.message.delete()
        except:
            pass
        await query.message.reply_text(text=text)

    elif data == "token_set_api":
        user_states[user_id] = "WAITING_FOR_API"
        text = (
            "**🔑 SEND ME YOUR SHORTENER API KEY**\n\n"
            "Paste your developer API key obtained from your shortener website dashboard.\n\n"
            "Type `/cancel` to abort this configuration."
        )
        try:
            await query.message.delete()
        except:
            pass
        await query.message.reply_text(text=text)

    elif data == "token_set_time":
        user_states[user_id] = "WAITING_FOR_TIME"
        text = (
            "**⏰ SEND ME THE TOKEN EXPIRATION TIME**\n\n"
            "Specify the lifespan of verified token state.\n"
            "**Examples:** `1h` (1 hour), `15m` (15 minutes), `24h` (24 hours).\n------------\n"
            "Type `/cancel` to abort this configuration."
        )
        try:
            await query.message.delete()
        except:
            pass
        await query.message.reply_text(text=text)

    # --- PREMIUM SUB-MENU BUTTON ACTIONS ---

    elif data == "prem_add_user":
        user_states[user_id] = "WAITING_FOR_PREMIUM_ADD"
        text = (
            "**👤 ADD PREMIUM USER**\n\n"
            "Please send the target User ID and Time Duration in this exact format:\n\n"
            "🚩 **FORMAT:** `user_id time_value time_unit`\n"
            "📝 **Example:** `123456789 30 days`\n"
            "📝 **Example:** `123456789 1 hours`\n\n"
            "Type `/cancel` to abort this configuration."
        )
        try:
            await query.message.delete()
        except:
            pass
        await query.message.reply_text(text=text)

    elif data == "prem_rem_user":
        user_states[user_id] = "WAITING_FOR_PREMIUM_REMOVE"
        text = (
            "**❌ REMOVE PREMIUM USER**\n\n"
            "Please send the target **User ID** that you want to remove from premium list.\n\n"
            "Type `/cancel` to abort this configuration."
        )
        try:
            await query.message.delete()
        except:
            pass
        await query.message.reply_text(text=text)

    elif data == "prem_total_users":
        await query.answer("Fetching premium user list...", show_alert=False)
        ist = timezone("Asia/Kolkata")
        premium_users_cursor = collection.find({})
        premium_user_list = ['**👑 Active Premium Users in DB:**\n']
        current_time = datetime.now(ist)  

        async for u in premium_users_cursor:
            u_id = u["user_id"]
            expiration_timestamp = u["expiration_timestamp"]

            try:
                expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)
                remaining_time = expiration_time - current_time

                if remaining_time.total_seconds() <= 0:
                    await collection.delete_one({"user_id": u_id})
                    continue  

                try:
                    user_info = await client.get_users(u_id)
                    username = f"@{user_info.username}" if user_info.username else "No Username"
                except:
                    username = "Unknown"

                days, hours, minutes = (
                    remaining_time.days,
                    remaining_time.seconds // 3600,
                    (remaining_time.seconds // 60) % 60,
                )
                expiry_info = f"`{days}d {hours}h {minutes}m left`__"

                premium_user_list.append(
                    f"• **ID:** `{u_id}` | {username}\n"
                    f"  **Expiry:** {expiry_info}\n"
                )
            except Exception as e:
                premium_user_list.append(f"• **ID:** `{u_id}` (Error structure fetching)\n")

        if len(premium_user_list) == 1:  
            final_text = "⚠️ **I found 0 active premium users in database.**"
        else:
            final_text = "\n".join(premium_user_list)

        back_markup = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ BACK", callback_data="menu_premium")]])
        try:
            await query.message.delete()
        except:
            pass
        await query.message.reply_text(text=final_text, reply_markup=back_markup)

# --- CONVERSATION TEXT INPUT HANDLER ---

@Client.on_message(filters.private & filters.incoming, group=-2)
async def settings_input_interceptor(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    if isinstance(OWNER_ID, list):
        if user_id not in OWNER_ID:
            return
    else:
        if user_id != int(OWNER_ID):
            return

    state = user_states[user_id]
    text = message.text.strip() if message.text else ""

    if text.lower() == "/cancel":
        user_states.pop(user_id, None)
        await message.reply("❌ **Configuration update cancelled safely.**")
        markup = await get_main_settings_keyboard()
        await message.reply_text("**✨ VENOM FILE STORE SETTINGS ✨**", reply_markup=markup)
        return

    # --- SHORTNER INPUT PROCESSING ---
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

    # --- PREMIUM INPUT PROCESSING ---
    elif state == "WAITING_FOR_PREMIUM_ADD":
        parts = text.split()
        if len(parts) != 3:
            await message.reply("⚠️ **Invalid Format!** Please send strictly in `user_id time_value time_unit` format.")
            return

        try:
            target_id = int(parts[0])
            time_value = int(parts[1])
            time_unit = parts[2].lower()

            expiration_time = await add_premium(target_id, time_value, time_unit)
            user_states.pop(user_id, None)

            await message.reply(
                f"✅ **User `{target_id}` added as premium for {time_value} {time_unit}.**\n"
                f"⏰ Expires: `{expiration_time}`"
            )
            try:
                await client.send_message(
                    chat_id=target_id,
                    text=f"🎉 **Premium Activated!**\n\nYou received premium access for `{time_value} {time_unit}`.\nExpires on: `{expiration_time}`"
                )
            except:
                pass

        except ValueError:
            await message.reply("❌ **Processing Error!** Make sure User ID and Time Value are numeric digits.")
        except Exception as e:
            await message.reply(f"⚠️ **Error:** `{str(e)}`")

        markup = await get_main_settings_keyboard()
        await message.reply_text("**✨ VENOM FILE STORE SETTINGS ✨**", reply_markup=markup)

    elif state == "WAITING_FOR_PREMIUM_REMOVE":
        try:
            target_id = int(text)
            await remove_premium(target_id)
            user_states.pop(user_id, None)
            await message.reply(f"✅ **User `{target_id}` has been successfully removed from premium list.**")
        except ValueError:
            await message.reply("❌ **Invalid User ID!** Input must be a valid integer number.")
        except Exception as e:
            await message.reply(f"⚠️ **Error occurred:** `{str(e)}`")

        markup = await get_main_settings_keyboard()
        await message.reply_text("**✨ VENOM FILE STORE SETTINGS ✨**", reply_markup=markup)
