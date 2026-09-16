import asyncio
import os
from dotenv import load_dotenv
from telethon import events, Button, TelegramClient
import db
from handlers.callbacks import register as register_callbacks

load_dotenv()
API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
BOT_TOKEN = os.environ['BOT_TOKEN']
# client connection
bot = TelegramClient(
                    'bot', API_ID, API_HASH
                    )

# Currently active user tasks in memory
in_progress = set()

# Limit for concurrent ffmpeg spawns
ffmpeg_semaphore = asyncio.Semaphore(2)


@bot.on(events.NewMessage)
async def audio_handler(event):
    msg = event.message
    if not (msg.audio or msg.voice):
        return

    doc_id = msg.document.id

    occurrence_id = await db.add_occurrence(
        doc_id=doc_id,
        chat_id=event.chat_id,
        message_id=msg.id,
        user_id=event.sender_id,
        )

    # Buttons listed one per row ("line by line"), not side by side.
    buttons = [
        [Button.inline('Spec', f'spec|{occurrence_id}',)],
        [Button.inline('MediaInfo', f'mediainfo|{occurrence_id}')],
        [Button.inline('Transcode', f'transcode|{occurrence_id}')],
        [Button.inline('Cancel', f'close|{occurrence_id}')]
    ]
    await event.reply('Choose an action:', buttons=buttons)


async def main():
    await db.init_db()

    register_callbacks(bot, in_progress, ffmpeg_semaphore)

    await bot.start(bot_token=BOT_TOKEN)
    print('Bot is running...')
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
