from pyrogram import Client, __version__
from database.ia_filterdb import Media
import requests
import re
import os
from urllib.parse import unquote
from database.users_chats_db import db
from info import API_ID, API_HASH, ADMINS, BOT_TOKEN, LOG_CHANNEL, PORT, SUPPORT_GROUP
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from datetime import date, datetime
import asyncio
import pytz
from aiohttp import web
from plugins import web_server, check_expired_premium
import time

# ======= ADD THIS NEW FUNCTION ======= #
async def download_file(url, user_id, file_name=None):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            original_name = unquote(url.split("/")[-1].split("?")[0])
            ext = original_name.split('.')[-1] if '.' in original_name else ''
            final_name = f"{file_name}.{ext}" if file_name else original_name
            file_path = f"downloads/{user_id}_{final_name}"
            
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
                
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk: f.write(chunk)
            return file_path
        return None
    except Exception as e:
        print(f"Download error: {e}")
        return None

class Bot(Client):
    def __init__(self):
        super().__init__(
            name='aks',
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            sleep_threshold=5,
            workers=150,
            plugins={"root": "plugins"}
        )

    # ======= ADD THIS NEW METHOD ======= #
    async def handle_url_upload(self, message):
        user_id = message.from_user.id
        command_text = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else ""
        
        url_match = re.search(r'(https?://\S+)', command_text)
        rename_match = re.search(r'rename=([^\s]+)', command_text)
        
        if not url_match:
            await message.reply("❗ Provide URL like: /upload https://example.com/file.pdf rename=myfile")
            return
        
        url = url_match.group(1)
        custom_name = rename_match.group(1) if rename_match else None
        
        user = await db.get_user(user_id)
        if not user.get("is_premium", False):
            last_used = user.get("last_used", datetime.min)
            if (datetime.now() - last_used).total_seconds() < 3600:
                remaining = 3600 - int((datetime.now() - last_used).total_seconds())
                await message.reply(f"⏳ Free users have 1-hour cooldown! Wait {remaining//60} mins or /upgrade")
                return
        
        downloaded_file = await download_file(url, user_id, custom_name)
        if downloaded_file:
            await message.reply_document(
                document=downloaded_file,
                caption=f"📤 Uploaded by {message.from_user.mention}"
            )
            os.remove(downloaded_file)
            await db.update_user(user_id, {"last_used": datetime.now()})
        else:
            await message.reply("❌ Failed to process your request")

    async def start(self):
        st = time.time()
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await super().start()
        await Media.ensure_indexes()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        temp.B_LINK = me.mention
        self.username = '@' + me.username
        self.loop.create_task(check_expired_premium(self))
        print(f"{me.first_name} is started now ❤️")
        tz = pytz.timezone('Asia/Kolkata')
        today = date.today()
        now = datetime.now(tz)
        timee = now.strftime("%H:%M:%S %p")
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()
        await self.send_message(chat_id=LOG_CHANNEL, text=f"<b>{me.mention} ʀᴇsᴛᴀʀᴛᴇᴅ 🤖\n\n📆 ᴅᴀᴛᴇ - <code>{today}</code>\n🕙 ᴛɪᴍᴇ - <code>{timee}</code>\n🌍 ᴛɪᴍᴇ ᴢᴏɴᴇ - <code>Asia/Kolkata</code></b>")
        await self.send_message(chat_id=SUPPORT_GROUP, text=f"<b>{me.mention} ʀᴇsᴛᴀʀᴛᴇᴅ 🤖</b>")
        tt = time.time() - st
        seconds = int(tt)
        for admin in ADMINS:
            await self.send_message(chat_id=admin, text=f"<b>✅ ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ\n🕥 ᴛɪᴍᴇ ᴛᴀᴋᴇɴ - <code>{seconds} sᴇᴄᴏɴᴅs</code></b>")

    async def stop(self, *args):
        self.add_handler(MessageHandler(self.handle_url_upload, filters.command("upload") & filters.private))
        await super().stop()
        print("Bot stopped.")

    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current + new_diff + 1)))
            for message in messages:
                yield message
                current += 1

app = Bot()
app.run()
