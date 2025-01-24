from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest
from database.users_chats_db import db
from info import ADMINS, AUTH_CHANNEL

@Client.on_chat_join_request(filters.chat(AUTH_CHANNEL))
async def join_reqs(client, message: ChatJoinRequest):
    if not await db.find_join_req(message.from_user.id):
        # Add user to the join request database
        await db.add_join_req(message.from_user.id)

        # Accept the join request
        await message.approve()

        # Send a welcome message to the user
        welcome_msg = f"Welcome {message.from_user.mention}! 🎉\nYou can search for any movie, web series, or anime and enjoy them right here! 🎬🍿"
        await client.send_message(
            chat_id=message.from_user.id, 
            text=welcome_msg, 
            parse_mode=enums.ParseMode.HTML
        )

@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):
    await db.del_join_req()    
    await message.reply("<b>⚙ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴄʜᴀɴɴᴇʟ ʟᴇғᴛ ᴜꜱᴇʀꜱ ᴅᴇʟᴇᴛᴇᴅ</b>")
    
