import os
import time
import db

from telethon import events
from actions import spec, mediainfo, transcode

ACTIONS = {
    'spec': spec.get_spec,
    'mediainfo': mediainfo.mi,
    'transcode': transcode.run,
}

FFMPEG_ACTIONS = {'spec', 'transcode'}
FORMAT_AS_CODE = {'mediainfo'}
MAX_MESSAGE_LEN = 4000


def register(bot, in_progress, ffmpeg_semaphore):

    @bot.on(events.CallbackQuery)
    async def callback_handler(event):
        action, occurrence_id_str = event.data.decode().split('|', 1)
        occurrence_id = int(occurrence_id_str)

        if action not in ACTIONS:
            await event.answer('Cancelled')
            return

        occurrence = await db.get_occurrence(occurrence_id)
        if occurrence is None:
            await event.answer('File reference expired, please resend it.', alert=True)
            return

        doc_id = occurrence['doc_id']
        chat_id = occurrence['chat_id']
        message_id = occurrence['message_id']

        if doc_id is in_progress:
            await event.answer('Already working on this file, please wait', alert=True)
            return

        in_progress.add(doc_id)
        try:
            await event.answer()

            button_msg = await event.get_message()
            await button_msg.delete()

            file_row = await db.get_file(doc_id)
            if file_row is not None:
                path = file_row['local_path']
            else:
                path = await _download_with_progress(bot, chat_id, message_id, doc_id)

            status_msg = await bot.send_message(
                event.chat_id, 'Processing...', reply_to=message_id
            )

            if action in FFMPEG_ACTIONS:
                async with ffmpeg_semaphore:
                    result = await ACTIONS[action](path)
            else:
                result = await ACTIONS[action](path)

            text = result.get('text')
            files = result.get('files') or []

            if text and action in FORMAT_AS_CODE:
                if len(text) > MAX_MESSAGE_LEN:
                    # Too long for one message - send as a .txt file instead.
                    txt_path = path + '.mediainfo.txt'
                    with open(txt_path, 'w') as f:
                        f.write(text)
                    files.append(txt_path)
                    await status_msg.delete()
                else:
                    await status_msg.edit(f'```\n{text}\n```', parse_mode='md')
            elif text:
                await status_msg.edit(text)
            else:
                await status_msg.delete()
            for file_path in files:
                await bot.send_file(chat_id, file=file_path, reply_to=message_id)
        finally:
            in_progress.discard(doc_id)


async def _download_with_progress(bot, chat_id, message_id, doc_id):
    # Progress and saving file to local
    original_msg = await bot.get_messages(chat_id, ids=message_id)
    filename = (original_msg.file.name if original_msg.file.name
                else f'{doc_id}{original_msg.file.ext or ""}')

    save_dir = 'audio/'
    os.makedirs(save_dir, exist_ok=True)

    status_msg = await bot.send_message(
        chat_id,
        f'Downlading file: {filename}\nProgress: 0%',
        reply_to=message_id
    )

    last_edit_time = [0.0]
    last_pct = [-1]

    async def progress(current, total):
        now = time.time()
        pct = int(current / total * 100) if total else 0

        if pct == last_pct[0]:
            return
        if now - last_edit_time[0] < 1.0 and current != total:
            return
        last_edit_time[0] = now
        last_pct[0] = pct
        try:
            await status_msg.edit(f'Downlading file: {filename}\nProgress: {pct}%')
        except Exception:
            pass

    path = await original_msg.download_media(file=save_dir, progress_callback=progress)
    await status_msg.delete()

    await db.add_file(doc_id, path, filename)
    return path
