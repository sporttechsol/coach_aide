import logging

import asyncio
from aiogram import (
    Dispatcher,
    types,
)
from aiogram.utils import exceptions

log = logging.getLogger(__name__)


def format_time(hours: int, minutes: int):
    return f"{hours:02d}:{minutes:02d}"


async def send_message(
    dispatcher: Dispatcher,
    user_id: int,
    text: str,
    keyboard=None,
    disable_notification: bool = False,
    parse_mode: str = None,
) -> bool:
    try:
        await dispatcher.bot.send_message(
            user_id,
            text,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_markup=keyboard,
        )
    except exceptions.BotBlocked:
        log.error(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.error(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.error(
            f"Target [ID:{user_id}]: Flood limit is exceeded. "
            f"Sleep {e.timeout} seconds."
        )
        await asyncio.sleep(e.timeout)
        return await send_message(dispatcher, user_id, text)  # Recursive call
    except exceptions.UserDeactivated:
        log.error(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.TelegramAPIError:
        log.error(f"Target [ID:{user_id}]: failed")
    else:
        log.info(f"Target [ID:{user_id}]: success")
        return True

    return False


async def forward_message(
    dispatcher: Dispatcher,
    user_id: int,
    message: types.Message,
):
    await dispatcher.bot.forward_message(
        user_id, message.chat.id, message.message_id
    )
