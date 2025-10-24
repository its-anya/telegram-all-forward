''' A script to send all messages from one chat to another. '''

import asyncio
import logging

from telethon.tl.patched import MessageService
from telethon.errors.rpcerrorlist import FloodWaitError
from telethon import TelegramClient
from telethon.sessions import StringSession
from settings import API_ID, API_HASH, forwards, get_forward, update_offset, STRING_SESSION


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

SENT_VIA = f'\n__Sent via__ `{str(__file__)}`'


def intify(string):
    try:
        return int(string)
    except:
        return string


async def safe_send_file(client, entity, file, **kwargs):
    """Safely send a file with flood wait handling"""
    while True:
        try:
            return await client.send_file(entity, file, **kwargs)
        except FloodWaitError as fwe:
            logging.warning(f'Flood wait for sending file: {fwe.seconds} seconds')
            await asyncio.sleep(fwe.seconds)


async def safe_send_message(client, entity, message, **kwargs):
    """Safely send a message with flood wait handling"""
    while True:
        try:
            return await client.send_message(entity, message, **kwargs)
        except FloodWaitError as fwe:
            logging.warning(f'Flood wait for sending message: {fwe.seconds} seconds')
            await asyncio.sleep(fwe.seconds)


async def forward_job():
    ''' the function that does the job 😂 '''
    if STRING_SESSION:
        session = StringSession(STRING_SESSION)
    else:
        session = 'forwarder'

    # Ensure API_ID and API_HASH are not None (assertion already in settings.py)
    assert API_ID is not None and API_HASH is not None, "API_ID and API_HASH must be set in .env file"
    
    # Convert API_ID to integer
    api_id = int(API_ID)
    api_hash = str(API_HASH)

    async with TelegramClient(session, api_id, api_hash) as client:

        confirm = ''' IMPORTANT 🛑
            Are you sure that your `config.ini` is correct ?

            Take help of @userinfobot for correct chat ids.
            
            Press [ENTER] to continue:
            '''

        input(confirm)

        error_occured = False
        for forward in forwards:
            from_chat, to_chat, offset = get_forward(forward)

            if not offset:
                offset = 0

            last_id = 0

            async for message in client.iter_messages(intify(from_chat), reverse=True, offset_id=offset):
                if isinstance(message, MessageService):
                    continue
                try:
                    await safe_send_message(client, intify(to_chat), message)
                    last_id = str(message.id)
                    logging.info('forwarding message with id = %s', last_id)
                    update_offset(forward, last_id)
                    
                    # Add a small delay to avoid hitting rate limits
                    await asyncio.sleep(0.1)
                except FloodWaitError as fwe:
                    logging.warning(f'Flood wait: {fwe.seconds} seconds')
                    await asyncio.sleep(fwe.seconds)
                except Exception as err:
                    logging.exception(err)
                    error_occured = True
                    break

            logging.info('Completed working with %s', forward)

        # Send config file with flood wait handling
        try:
            await safe_send_file(client, 'me', 'config.ini', caption='This is your config file for telegram-chat-forward.')
        except Exception as err:
            logging.error(f'Failed to send config file: {err}')

        message = 'Your forward job has completed.' if not error_occured else 'Some errors occured. Please see the output on terminal. Contact Developer.'
        final_message = f'''Hi !
        \n**{message}**
        \n**Telegram All Forward** is developed by @its-Anya.
        \nPlease star 🌟 on [GitHub](https://github.com/its-anya/telegram-all-forward.git).
        {SENT_VIA}'''
        
        try:
            await safe_send_message(client, 'me', final_message, link_preview=False)
        except Exception as err:
            logging.error(f'Failed to send final message: {err}')

if __name__ == "__main__":
    assert forwards
    asyncio.run(forward_job())