#(©)Codexbotz

import asyncio
import re
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from bot import Bot
from asyncio import TimeoutError
from helper_func import encode, admin

# Helper function to check if the bot is admin in the channel and get the message ID & chat ID
async def get_any_channel_msg_id(client: Client, message: Message):
    chat_id = None
    msg_id = None

    # 1. Agar direct link bheja hai
    if message.text and not message.forward_from_chat:
        regex = r"https:\/\/t\.me\/(c\/)?([a-zA-Z0-9_]+)\/(\d+)"
        match = re.match(regex, message.text.strip())
        if match:
            chat_identifier = match.group(2)
            msg_id = int(match.group(3))
            
            # Private channel context (c/123456)
            if match.group(1):
                chat_id = int(f"-100{chat_identifier}")
            else:
                chat_id = f"@{chat_identifier}"
        else:
            return None, None

    # 2. Agar message forward kiya hai
    elif message.forward_from_chat:
        chat_id = message.forward_from_chat.id
        msg_id = message.forward_from_message_id
    else:
        return None, None

    # 3. Check privileges: Kya bot us channel mein full admin hai?
    try:
        member = await client.get_chat_member(chat_id, "me")
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return msg_id, chat_id
        else:
            return "NOT_ADMIN", None
    except Exception as e:
        print(f"Admin check error: {e}")
        return None, None


@Bot.on_message(filters.private & admin & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            first_message = await client.ask(
                text="Forward the First Message from ANY Channel (where I am Admin)..\n\nor Send the Channel Post Link", 
                chat_id=message.from_user.id, 
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)), 
                timeout=60
            )
        except:
            return
            
        f_msg_id, f_chat_id = await get_any_channel_msg_id(client, first_message)
        if f_msg_id == "NOT_ADMIN":
            await first_message.reply("❌ Error\n\nMain us channel mein Admin nahi hoon! Mujhe pehle full rights ke sath Admin banayein.", quote=True)
            continue
        elif f_msg_id:
            break
        else:
            await first_message.reply("❌ Error\n\nInvalid Link ya Forwarded message. Koshish karein ki post valid ho.", quote=True)
            continue

    while True:
        try:
            second_message = await client.ask(
                text="Forward the Last Message from the SAME Channel..\nor Send the Channel Post link", 
                chat_id=message.from_user.id, 
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)), 
                timeout=60
            )
        except:
            return
            
        s_msg_id, s_chat_id = await get_any_channel_msg_id(client, second_message)
        if s_msg_id == "NOT_ADMIN":
            await second_message.reply("❌ Error\n\nMain us channel mein Admin nahi hoon!", quote=True)
            continue
        elif s_msg_id:
            if s_chat_id != f_chat_id:
                await second_message.reply("❌ Error\n\nDono posts ek hi channel se honi chahiye! Dobara last message bhejin.", quote=True)
                continue
            break
        else:
            await second_message.reply("❌ Error\n\nInvalid Link ya Forwarded message.", quote=True)
            continue

    # Hardcoded channel id ki jagah dynamic target channel id use ho rahi hai
    string = f"get-{f_msg_id * abs(f_chat_id)}-{s_msg_id * abs(f_chat_id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await second_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)


@Bot.on_message(filters.private & admin & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            channel_message = await client.ask(
                text="Forward Message from ANY Channel (where I am Admin)..\nor Send the Channel Post link", 
                chat_id=message.from_user.id, 
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)), 
                timeout=60
            )
        except:
            return
            
        msg_id, chat_id = await get_any_channel_msg_id(client, channel_message)
        if msg_id == "NOT_ADMIN":
            await channel_message.reply("❌ Error\n\nMain us channel mein Admin nahi hoon! Mujhe pehle full rights ke sath Admin banayein.", quote=True)
            continue
        elif msg_id:
            break
        else:
            await channel_message.reply("❌ Error\n\nInvalid Link ya Forwarded message.", quote=True)
            continue

    base64_string = await encode(f"get-{msg_id * abs(chat_id)}")
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await channel_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)


@Bot.on_message(filters.private & admin & filters.command("custom_batch"))
async def custom_batch(client: Client, message: Message):
    collected = []
    STOP_KEYBOARD = ReplyKeyboardMarkup([["STOP"]], resize_keyboard=True)

    await message.reply("Send all messages you want to include in batch.\n\nPress STOP when you're done.", reply_markup=STOP_KEYBOARD)

    while True:
        try:
            user_msg = await client.ask(
                chat_id=message.chat.id,
                text="Waiting for files/messages...\nPress STOP to finish.",
                timeout=60
            )
        except asyncio.TimeoutError:
            break

        if user_msg.text and user_msg.text.strip().upper() == "STOP":
            break

        # Empty / Service Message Filter
        if user_msg.service or (not user_msg.text and not user_msg.media):
            await message.reply("⚠️ **This message is empty or invalid. Skipping...**")
            continue

        try:
            sent = await user_msg.copy(client.db_channel.id, disable_notification=True)
            collected.append(sent.id)
        except Exception as e:
            await message.reply(f"❌ Failed to store a message:\n<code>{e}</code>")
            continue

    await message.reply("✅ Batch collection complete.", reply_markup=ReplyKeyboardRemove())

    if not collected:
        await message.reply("❌ No messages were added to batch.")
        return

    start_id = collected[0] * abs(client.db_channel.id)
    end_id = collected[-1] * abs(client.db_channel.id)
    string = f"get-{start_id}-{end_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await message.reply(f"<b>Here is your custom batch link:</b>\n\n{link}", reply_markup=reply_markup)
