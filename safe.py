''' A script to send all messages from one chat to another with robust flood wait handling. '''

import asyncio
import logging
import random
import time
from typing import Optional

from telethon.tl.patched import MessageService
from telethon.errors.rpcerrorlist import FloodWaitError, SessionPasswordNeededError
from telethon.errors import (
    AuthKeyError, 
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    ChannelPrivateError,
    ChatAdminRequiredError
)
from telethon import TelegramClient
from telethon.sessions import StringSession
from settings import API_ID, API_HASH, forwards, get_forward, update_offset, STRING_SESSION

# Enhanced logging with more detail
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SENT_VIA = f'\n__Sent via__ `{str(__file__)}`'

# Configuration for rate limiting and flood wait prevention
CONFIG = {
    'MIN_DELAY': 1.5,  # Minimum delay between messages (seconds) - IMPORTANT for account safety
    'MAX_DELAY': 3.0,  # Maximum delay between messages (seconds)
    'RETRY_ATTEMPTS': 5,  # Number of retry attempts for failed operations
    'RETRY_DELAY': 2,  # Initial retry delay (seconds) - will use exponential backoff
    'FLOOD_WAIT_BUFFER': 5,  # Extra seconds to add to flood wait time
    'MAX_FLOOD_WAIT': 3600,  # Maximum flood wait time to handle (1 hour)
    'AUTO_MODE': True,  # Set to True for server deployment (skips user input)
}


def intify(string):
    """Convert string to int if possible, otherwise return as is"""
    try:
        return int(string)
    except:
        return string


async def smart_delay():
    """Add a random delay between messages to avoid rate limits"""
    delay = random.uniform(CONFIG['MIN_DELAY'], CONFIG['MAX_DELAY'])
    logger.debug(f'Smart delay: {delay:.2f} seconds')
    await asyncio.sleep(delay)


async def safe_operation(operation_func, operation_name: str, max_retries: int = None):
    """
    Safely execute an operation with exponential backoff and flood wait handling.
    
    Args:
        operation_func: Async function to execute
        operation_name: Name of the operation for logging
        max_retries: Maximum number of retry attempts (uses CONFIG if None)
    
    Returns:
        Result of the operation or None if all retries failed
    """
    if max_retries is None:
        max_retries = CONFIG['RETRY_ATTEMPTS']
    
    retry_count = 0
    last_error = None
    
    while retry_count <= max_retries:
        try:
            result = await operation_func()
            if retry_count > 0:
                logger.info(f'{operation_name} succeeded after {retry_count} retries')
            return result
            
        except FloodWaitError as fwe:
            wait_time = fwe.seconds + CONFIG['FLOOD_WAIT_BUFFER']
            
            # Check if flood wait is too long
            if wait_time > CONFIG['MAX_FLOOD_WAIT']:
                logger.error(
                    f'Flood wait time ({wait_time}s) exceeds maximum allowed ({CONFIG["MAX_FLOOD_WAIT"]}s). '
                    f'Skipping {operation_name}.'
                )
                return None
            
            logger.warning(
                f'Flood wait for {operation_name}: {wait_time} seconds '
                f'(original: {fwe.seconds}s + buffer: {CONFIG["FLOOD_WAIT_BUFFER"]}s)'
            )
            await asyncio.sleep(wait_time)
            retry_count += 1
            continue
            
        except (ChannelPrivateError, ChatAdminRequiredError) as err:
            logger.error(f'Permission error for {operation_name}: {err}. Skipping.')
            return None
            
        except Exception as err:
            last_error = err
            retry_count += 1
            
            if retry_count <= max_retries:
                # Exponential backoff: 2, 4, 8, 16, 32 seconds...
                backoff_time = CONFIG['RETRY_DELAY'] * (2 ** (retry_count - 1))
                logger.warning(
                    f'Error in {operation_name} (attempt {retry_count}/{max_retries}): {err}. '
                    f'Retrying in {backoff_time} seconds...'
                )
                await asyncio.sleep(backoff_time)
            else:
                logger.error(
                    f'Failed {operation_name} after {max_retries} retries. Last error: {err}'
                )
                return None
    
    return None


async def safe_send_message(client, entity, message, **kwargs):
    """Safely send a message with smart rate limiting and flood wait handling"""
    async def send():
        return await client.send_message(entity, message, **kwargs)
    
    return await safe_operation(send, 'send_message')


async def safe_send_file(client, entity, file, **kwargs):
    """Safely send a file with flood wait handling"""
    async def send():
        return await client.send_file(entity, file, **kwargs)
    
    return await safe_operation(send, 'send_file')


async def forward_job():
    """Main forwarding job with comprehensive error handling"""
    start_time = time.time()
    
    if STRING_SESSION:
        session = StringSession(STRING_SESSION)
    else:
        session = 'forwarder'

    # Ensure API credentials are valid
    assert API_ID is not None and API_HASH is not None, \
        "API_ID and API_HASH must be set in .env file"
    
    api_id = int(API_ID)
    api_hash = str(API_HASH)

    logger.info('Starting Telegram Chat Forward script...')
    logger.info(f'Configuration: MIN_DELAY={CONFIG["MIN_DELAY"]}s, MAX_DELAY={CONFIG["MAX_DELAY"]}s')

    async with TelegramClient(session, api_id, api_hash) as client:
        
        # Skip user input if in auto mode (for server deployment)
        if not CONFIG['AUTO_MODE']:
            confirm = ''' IMPORTANT 🛑
            Are you sure that your `config.ini` is correct?

            Take help of @userinfobot for correct chat ids.
            
            Press [ENTER] to continue:
            '''
            input(confirm)
        else:
            logger.info('Running in AUTO MODE (server deployment)')

        total_messages = 0
        error_count = 0
        
        for forward in forwards:
            try:
                from_chat, to_chat, offset = get_forward(forward)
                
                if not offset:
                    offset = 0

                logger.info(f'Starting forward: {forward} (from: {from_chat}, to: {to_chat}, offset: {offset})')
                
                last_id = 0
                messages_in_this_forward = 0

                async for message in client.iter_messages(intify(from_chat), reverse=True, offset_id=offset):
                    if isinstance(message, MessageService):
                        logger.debug(f'Skipping service message: {message.id}')
                        continue
                    
                    # Send message with safe operation
                    result = await safe_send_message(client, intify(to_chat), message)
                    
                    if result is not None:
                        last_id = str(message.id)
                        total_messages += 1
                        messages_in_this_forward += 1
                        logger.info(
                            f'✓ Forwarded message {last_id} '
                            f'(total: {total_messages}, this forward: {messages_in_this_forward})'
                        )
                        update_offset(forward, last_id)
                        
                        # Smart delay to prevent rate limits
                        await smart_delay()
                    else:
                        error_count += 1
                        logger.warning(f'✗ Failed to forward message {message.id}')
                        # Continue with next message instead of breaking

                logger.info(
                    f'Completed forward: {forward} '
                    f'(processed: {messages_in_this_forward} messages)'
                )

            except Exception as err:
                logger.exception(f'Critical error processing forward {forward}: {err}')
                error_count += 1
                # Continue with next forward instead of stopping

        # Calculate statistics
        elapsed_time = time.time() - start_time
        logger.info('='*60)
        logger.info('FORWARDING JOB COMPLETED')
        logger.info(f'Total messages forwarded: {total_messages}')
        logger.info(f'Errors encountered: {error_count}')
        logger.info(f'Time elapsed: {elapsed_time:.2f} seconds')
        logger.info(f'Average rate: {total_messages/elapsed_time*60:.2f} messages/minute')
        logger.info('='*60)

        # Send config file backup
        config_result = await safe_send_file(
            client, 
            'me', 
            'config.ini', 
            caption='✅ Your config file for telegram-chat-forward (backup)'
        )
        
        if config_result is None:
            logger.warning('Failed to send config file backup')

        # Send completion message
        status_emoji = '✅' if error_count == 0 else '⚠️'
        message_text = (
            'Your forward job has completed successfully!' 
            if error_count == 0 
            else f'Forward job completed with {error_count} errors. Check logs for details.'
        )
        
        final_message = f'''{status_emoji} Hi!

**{message_text}**

📊 **Statistics:**
• Messages forwarded: {total_messages}
• Errors: {error_count}
• Time taken: {elapsed_time/60:.1f} minutes
• Average rate: {total_messages/elapsed_time*60:.1f} msgs/min

**Telegram Chat Forward** is developed by @AahnikDaw.
Please star 🌟 on [GitHub](https://github.com/aahnik/telegram-chat-forward).
{SENT_VIA}'''
        
        final_result = await safe_send_message(client, 'me', final_message, link_preview=False)
        
        if final_result is None:
            logger.warning('Failed to send final completion message')


if __name__ == "__main__":
    assert forwards, "No forwards configured in config.ini"
    
    try:
        asyncio.run(forward_job())
    except KeyboardInterrupt:
        logger.info('Script interrupted by user')
    except Exception as err:
        logger.exception(f'Fatal error: {err}')
        raise
