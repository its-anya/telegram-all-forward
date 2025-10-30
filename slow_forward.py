import asyncio
import logging
from telethon.tl.patched import MessageService
from telethon.errors.rpcerrorlist import FloodWaitError
from telethon import TelegramClient
from telethon.sessions import StringSession
from settings import API_ID, API_HASH, forwards, get_forward, update_offset, STRING_SESSION

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

SENT_VIA = f'\n__Sent via__ `{str(__file__)}`'


def intify(string):
    """Convert string to int if possible, otherwise return string"""
    try:
        return int(string)
    except ValueError:
        return string


async def safe_forward(client, to_chat, message):
    """Forward a message safely with flood wait handling"""
    while True:
        try:
            return await client.forward_messages(to_chat, message)
        except FloodWaitError as fwe:
            logging.warning(f'Flood wait for forwarding message: {fwe.seconds} seconds')
            await asyncio.sleep(fwe.seconds)


async def forward_job():
    """Main forwarding function"""
    session = StringSession(STRING_SESSION) if STRING_SESSION else 'forwarder'
    assert API_ID is not None and API_HASH is not None, "API_ID and API_HASH must be set"

    async with TelegramClient(session, int(API_ID), str(API_HASH)) as client:

        confirm = '''IMPORTANT 🛑
Your `config.ini` must be correct. Check chat IDs with @userinfobot.
Press [ENTER] to continue:'''
        input(confirm)

        error_occurred = False
        offset_reports = []  # Collect per-forward final offsets for the summary

        for forward in forwards:
            from_chat, to_chat, offset = get_forward(forward)
            offset = offset or 0
            initial_offset = offset
            last_id = 0

            async for message in client.iter_messages(intify(from_chat), reverse=True, offset_id=offset):
                if isinstance(message, MessageService):
                    continue

                try:
                    await safe_forward(client, intify(to_chat), message)
                    last_id = message.id
                    logging.info('Forwarded message id = %s', last_id)
                    # FIX: convert to string for configparser
                    update_offset(forward, str(last_id))
                    await asyncio.sleep(0.5)  # Adjustable delay to reduce flood wait

                except Exception as err:
                    logging.exception(err)
                    error_occurred = True
                    break

            logging.info('Completed forward job for %s', forward)
            # Record final offset for this mapping (last_id if forwarded, else initial)
            final_offset = last_id if last_id > 0 else initial_offset
            offset_reports.append({
                'from': from_chat,
                'to': to_chat,
                'final_offset': final_offset
            })

        # Send config file safely
        try:
            await client.send_file('me', 'config.ini', caption='Your config file for telegram-chat-forward.')
        except Exception as err:
            logging.error(f'Failed to send config file: {err}')

        # Build offsets summary text
        if len(offset_reports) == 1:
            offset_summary_text = f"Your offset number is {offset_reports[0]['final_offset']}"
        else:
            lines = [f"- {r['from']} → {r['to']}: {r['final_offset']}" for r in offset_reports]
            offset_summary_text = "Your offset numbers:\n" + "\n".join(lines)

        # Send final summary message with offsets
        final_message = f"""
Hi!
**{'Your forward job has completed.' if not error_occurred else 'Some errors occurred. Check terminal output.'}**
{offset_summary_text}
**Telegram Chat Forward** is developed by OpenSource Dev.
Please star 🌟 on [GitHub](https://github.com/its-anya/telegram-all-forward).
{SENT_VIA}
"""
        try:
            await client.send_message('me', final_message, link_preview=False)
        except Exception as err:
            logging.error(f'Failed to send final message: {err}')


if __name__ == "__main__":
    assert forwards, "No forwards configured in settings.py"
    asyncio.run(forward_job())
