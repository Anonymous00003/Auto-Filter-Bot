from pyrogram import Client, filters
from pyrogram.types import Message
import aiohttp
import os
import time
from datetime import datetime
from info import LOG_CHANNEL

async def download_file(url, message):
    file_name = url.split("/")[-1]
    download_path = f"downloads/{file_name}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(download_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(1024):
                        f.write(chunk)
                return download_path
            else:
                await message.reply("Failed to download file. Invalid URL or server error.")
                return None

@Client.on_message(filters.command("url"))
async def handle_url_upload(client, message: Message):
    try:
        # Check if URL provided
        if len(message.command) < 2:
            await message.reply("❗ Please send command like: /url https://example.com/file.zip")
            return

        url = message.command[1]
        msg = await message.reply("⏳ Starting download...")

        # Download file
        file_path = await download_file(url, message)
        if not file_path:
            return

        # Ask for rename
        await msg.edit("✅ Download complete! Send me a new file name (or type /skip to keep original name)")
        
        # Wait for rename input
        try:
            rename_msg = await client.listen.Message(
                filters.text & filters.user(message.from_user.id),
                timeout=300
            )
            if rename_msg.text.lower() != "/skip":
                new_path = f"downloads/{rename_msg.text}"
                os.rename(file_path, new_path)
                file_path = new_path
        except Exception as e:
            await message.reply(f"⏱️ Rename timed out. Using original name: {os.path.basename(file_path)}")

        # Upload to Telegram
        start_time = time.time()
        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption=f"Uploaded via URL\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Cleanup and log
        os.remove(file_path)
        await msg.delete()
        await client.send_message(
            LOG_CHANNEL,
            f"#URL_UPLOAD\nUser {message.from_user.mention} uploaded:\n{url}"
        )

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
