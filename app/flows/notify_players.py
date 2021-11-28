import logging

import arrow
import asyncio
from aiogram import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from app import (
    text,
    utils,
)
from app.storage import (
    answer_tbl,
    notification_tbl,
    user_tbl,
)
from app.storage.answer_tbl import AnswerValue
from app.storage.models import Notification
from app.storage.notification_tbl import NotificationType

log = logging.getLogger(__name__)


def init(dp: Dispatcher):
    dp.register_callback_query_handler(
        callback_players_handler,
        Text(startswith=NotificationType.POLL_BEFORE_TRAINING.value),
    )
    dp.register_callback_query_handler(
        callback_players_handler,
        Text(startswith=NotificationType.POLL_AFTER_TRAINING.value),
    )
    dp.register_callback_query_handler(
        callback_players_handler,
        Text(startswith=NotificationType.PAYDAY_QUESTION.value),
    )


async def callback_players_handler(call: CallbackQuery):
    notification_type, event_id, event_at_ts, value = call.data.split(":")
    await answer_tbl.create(
        call.from_user.id,
        int(event_id),
        NotificationType(notification_type),
        int(event_at_ts),
        AnswerValue(value),
    )

    if value.endswith(AnswerValue.YES.value):
        await call.answer(text="Great. Glad to hear it.")
    elif value.endswith(AnswerValue.NO.value):
        await call.answer(text="That's too bad. But I think you'll make it.")
    elif value.endswith(AnswerValue.MAYBE.value):
        await call.answer(
            text="Thank you. We hope for a positive response later.",
        )
    else:
        raise ValueError(f"Wrong answer_value[{value}]")


async def do_send_message(dispatcher: Dispatcher):
    next_event = await notification_tbl.get_next_for_team_players()
    if next_event:
        count = 0
        team_players = await user_tbl.get_active_team_players()
        try:
            for team_player in team_players:
                msg, kbr = _gen_keyboard_and_message(next_event)
                log.info(f"Will send message: {msg}")
                if await utils.send_message(
                    dispatcher,
                    team_player.user_id,
                    msg,
                    kbr,
                    parse_mode="Markdown",
                ):
                    count += 1
                await asyncio.sleep(0.05)
        finally:
            await notification_tbl.disable(next_event.id)
            log.info(f"{count} messages successful sent.")


def _gen_keyboard_and_message(next_event: Notification):
    event_type = NotificationType(next_event.type)
    training_date = arrow.get(next_event.event_at_ts).format(
        "DD.MM.YYYY в HH:mm"
    )
    answer_id = f"{event_type.name}:{next_event.id}:{next_event.event_at_ts}"
    if event_type is NotificationType.POLL_BEFORE_TRAINING:
        message = f"There's (*{training_date}*) training today. Will you come?"
        keyboard = _gen_keyboard(answer_id)
    elif event_type is NotificationType.POLL_AFTER_TRAINING:
        message = f"Been to training today (*{training_date}*)?"
        keyboard = _gen_keyboard(answer_id, with_maybe=False)
    elif event_type is NotificationType.PAYDAY_QUESTION:
        message = next_event.user_text
        keyboard = _gen_keyboard(answer_id, with_maybe=False)
    else:
        raise ValueError(f"Wrong event_type[{event_type}]")

    return message, keyboard


def _gen_keyboard(answer_id: str, with_maybe: bool = True):
    keyboard = InlineKeyboardMarkup(row_width=2)
    yes_btn = InlineKeyboardButton(
        text.YES, callback_data=f"{answer_id}:{AnswerValue.YES.value}"
    )
    no_btn = InlineKeyboardButton(
        text.NO, callback_data=f"{answer_id}:{AnswerValue.NO.value}"
    )
    keyboard.row(yes_btn, no_btn)

    if with_maybe:
        maybe_btn = InlineKeyboardButton(
            text.MAYBE, callback_data=f"{answer_id}:{AnswerValue.MAYBE.value}"
        )
        keyboard.row(maybe_btn)

    return keyboard
