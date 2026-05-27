#(©)Codexbotz

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from bot import Bot
from asyncio import TimeoutError
from helper_func import encode, get_message_id, admin

@Bot.on_message(filters.private & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            first_message = await client.ask(
                text="Forward The First Message From Your Batch Channel (With Forward Tag)... Or Give Me First Message Link Of Your Batch Channel\n\nNOTE : MAKE SURE THIS BOT IS ADMIN IN YOUR CHANNEL WITH FULL RIGHT", 
                chat_id=message.from_user.id, 
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)), 
                timeout=60
            )
        except TimeoutError:
            return
        
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply("❌ Error\n\nInvalid forwarded post or link. Make sure the bot is an admin in that channel.", quote=True)
            continue

    while True:
        try:
            second_message = await client.ask(
                text="Forward The Last Message From Your Batch Channel (With Forward Tag)... Or Give Me Last Message Link Of Your Batch Channel", 
                chat_id=message.from_user.id, 
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)), 
                timeout=60
            )
        except TimeoutError:
            return
        
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply("❌ Error\n\nInvalid forwarded post or link. Make sure the bot is an admin in that channel.", quote=True)
            continue

    # वीडियो फॉर्मेट के अनुसार चैनल आईडी निकालना (फॉरवर्डेड मैसेज या लिंक से)
    if first_message.forward_date:
        channel_id = first_message.forward_from_chat.id
    else:
        # अगर लिंक भेजा है तो helper फ़ंक्शन से चैट आईडी मिलेगी, नहीं तो एक डिफ़ॉल्ट हैंडलिंग
        channel_id = first_message.chat.id 

    string = f"get-{f_msg_id * abs(channel_id)}-{s_msg_id * abs(channel_id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("SHARE URL 🚀", url=f'https://telegram.me/share/url?url={link}')]])
    await second_message.reply_text(f"HERE IS YOUR LINK :\n\n{link}", quote=True, reply_markup=reply_markup)


@Bot.on_message(filters.private & filters.command('link'))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            user_message = await client.ask(
                text="SEND ME YOUR MESSAGE WHICH YOU WANT TO STORE", 
                chat_id=message.from_user.id, 
                timeout=60
            )
        except TimeoutError:
            return

        # यूज़र के मैसेज को बिना DB चैनल के प्रोसेस करने के लिए सीधे उसी का ID इस्तेमाल कर रहे हैं
        msg_id = user_message.id
        chat_id = user_message.chat.id
        break

    base64_string = await encode(f"get-{msg_id * abs(chat_id)}")
    link = f"https://t.me/{client.username}?start={base64_string}"
    
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("SHARE URL 🚀", url=f'https://telegram.me/share/url?url={link}')]])
    await user_message.reply_text(f"HERE IS YOUR LINK :\n\n{link}", quote=True, reply_markup=reply_markup)


@Bot.on_message(filters.private & filters.command("custom_batch"))
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
        except TimeoutError:
            break

        if user_msg.text and user_msg.text.strip().upper() == "STOP":
            break

        # बिना DB चैनल के, सीधे यूज़र द्वारा भेजे गए मैसेज की ID लिस्ट में सेव होगी
        collected.append(user_msg.id)

    await message.reply("✅ Batch collection complete.", reply_markup=ReplyKeyboardRemove())

    if not collected:
        await message.reply("❌ No messages were added to batch.")
        return

    chat_id = message.chat.id
    start_id = collected[0] * abs(chat_id)
    end_id = collected[-1] * abs(chat_id)
    string = f"get-{start_id}-{end_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("SHARE URL 🚀", url=f'https://telegram.me/share/url?url={link}')]])
    await message.reply(f"HERE IS YOUR CUSTOM BATCH LINK :\n\n{link}", reply_markup=reply_markup)
