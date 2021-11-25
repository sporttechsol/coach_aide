import logging

import asyncio
from aiogram import Dispatcher

from app import utils
from app.storage import (
    answer_tbl,
    notification_tbl,
    user_tbl,
)
from app.storage.answer_tbl import AnswerValue
from app.storage.models import (
    Answer,
    Notification,
)
from app.storage.notification_tbl import NotificationType

log = logging.getLogger(__name__)


async def do_send_message(dispatcher: Dispatcher):
    next_event = await notification_tbl.get_next_for_trainers()
    if next_event:
        count = 0
        trainers = await user_tbl.get_active_trainers()
        next_event_type = NotificationType(next_event.type)
        if next_event_type == NotificationType.REPORT_BEFORE_TRAINING:
            event_type = NotificationType.POLL_BEFORE_TRAINING
        elif next_event_type == NotificationType.REPORT_AFTER_TRAINING:
            event_type = NotificationType.POLL_AFTER_TRAINING
        else:
            raise ValueError(f"Wrong event_type[{next_event_type}]")

        players_answers = await answer_tbl.get_by(
            event_type, next_event.event_at_ts
        )
        try:
            for trainer in trainers:
                msg = _gen_message(next_event, players_answers)
                if await utils.send_message(
                    dispatcher,
                    trainer.user_id,
                    msg,
                ):
                    count += 1
                await asyncio.sleep(0.05)
        finally:
            await notification_tbl.disable(next_event.id)
            log.info(f"{count} messages successful sent.")


def _gen_message(
    next_notification: Notification, player_answers: list[Answer]
):
    event_type = NotificationType(next_notification.type)
    players = list(
        map(
            lambda x: f"{x.first_name} {x.last_name}\n",
            map(
                lambda x: x.user,
                filter(
                    lambda x: AnswerValue(x.value) == AnswerValue.YES,
                    player_answers,
                ),
            ),
        )
    )

    if event_type is NotificationType.REPORT_BEFORE_TRAINING:
        if len(players) == 0:
            message = "Сегодня на тренировку никто не придёт."
        else:
            message = f"Сегодня на тренировку собираются:\n {''.join(players)}"
    elif event_type is NotificationType.REPORT_AFTER_TRAINING:
        if len(players) == 0:
            message = "Сегодня на тренировку никто не ходил."
        else:
            message = f"Сегодня на тренировке были:\n {''.join(players)}"
    elif event_type is NotificationType.PAYDAY_QUESTION:
        message = "Оплатили. НИКТО!"
    else:
        raise ValueError(f"Wrong event_type[{event_type}]")

    return message
