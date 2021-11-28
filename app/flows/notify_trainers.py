import logging

import asyncio
from aiogram import Dispatcher

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
from app.storage.models import (
    Answer,
    Notification,
    User,
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
        players_answers = await answer_tbl.get_last_answers_by(
            event_type, next_event.event_at_ts
        )
        try:
            team_players = await user_tbl.get_active_team_players()
            msg = _gen_message(next_event, players_answers, team_players)
            for trainer in trainers:
                if await utils.send_message(
                    dispatcher,
                    trainer.user_id,
                    msg,
                    parse_mode="Markdown",
                ):
                    count += 1
                await asyncio.sleep(0.05)
        finally:
            await notification_tbl.disable(next_event.id)
            log.info(f"{count} messages successful sent.")


def _gen_message(
    next_notification: Notification,
    player_answers: list[Answer],
    team_players: list[User],
):
    event_type = NotificationType(next_notification.type)

    def users_by_answer(answer: AnswerValue) -> str:
        players = list(
            map(
                lambda x: f"{x.first_name} {x.last_name}\n",
                map(
                    lambda x: x.user,
                    filter(
                        lambda x: AnswerValue(x.value) == answer,
                        player_answers,
                    ),
                ),
            )
        )
        return "".join(players) or f"{text.NO_ANSWER}\n"

    user_ids_with_answers = set(map(lambda r: r.user_id, player_answers))
    no_answer = "".join(
        list(
            map(
                lambda x: f"{x.first_name} {x.last_name}\n",
                filter(
                    lambda x: x.user_id not in user_ids_with_answers,
                    team_players,
                ),
            )
        )
    )
    if not no_answer:
        no_answer = text.NO_ANSWER

    if event_type is NotificationType.REPORT_BEFORE_TRAINING:
        message = (
            f"*They're going to practice today:*\n{users_by_answer(AnswerValue.YES)}"
            f"\n*Doubt:*\n{users_by_answer(AnswerValue.MAYBE)}"
            f"\n*They won't come:*\n{users_by_answer(AnswerValue.NO)}"
            f"\n*No answer:*\n" + no_answer
        )
    elif event_type is NotificationType.REPORT_AFTER_TRAINING:
        message = (
            f"*Today's training was:*\n{users_by_answer(AnswerValue.YES)}"
            f"\n*They weren't*:\n{users_by_answer(AnswerValue.NO)}"
            f"\n*No answer:*\n{no_answer}"
        )
    elif event_type is NotificationType.PAYDAY_QUESTION:
        message = "Paid. NOBODY!"
    else:
        raise ValueError(f"Wrong event_type[{event_type}]")

    return message
