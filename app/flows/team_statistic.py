import arrow
from aiogram import Dispatcher

from app import (
    keyboards,
    utils,
)
from app.storage import (
    answer_tbl,
    notification_tbl,
    user_tbl,
)
from app.storage.answer_tbl import AnswerValue
from app.storage.notification_tbl import NotificationType as Nt


async def do_send_message(dispatcher: Dispatcher):
    # month_ago = arrow.utcnow().shift(months=-1)
    # start_prev_month = month_ago.floor("month")
    # end_prev_month = month_ago.ceil("month")
    month_ago = arrow.utcnow()
    start_prev_month = month_ago.floor("day")
    end_prev_month = month_ago.ceil("day")
    executed_polls = await notification_tbl.get_executed_polls_by(
        start_prev_month.int_timestamp, end_prev_month.int_timestamp
    )
    poll_after_trainings = filter(
        lambda x: Nt(x.type) == Nt.POLL_AFTER_TRAINING,
        executed_polls,
    )
    training_stats = []
    team_mean = 0
    user_data = {}
    poll_after_trainings = list(poll_after_trainings)
    for exec_poll in poll_after_trainings:
        users_last_answers = await answer_tbl.get_last_answers_by(
            Nt(exec_poll.type), exec_poll.event_at_ts
        )

        answers_who_was = list(
            filter(
                lambda x: AnswerValue(x.value) == AnswerValue.YES,
                users_last_answers,
            )
        )

        for answer in answers_who_was:
            if user_data.get(answer.user_id):
                user_data[answer.user_id] += 1
            else:
                user_data[answer.user_id] = 1

        count_was_on_trainings = len(answers_who_was)
        team_mean += count_was_on_trainings
        training_day = arrow.get(exec_poll.event_at_ts).format(
            "DD-MM-YYYY hh:mm"
        )
        training_stats.append(f"{training_day} - *{count_was_on_trainings}*")

    team_mean = team_mean / (len(poll_after_trainings) or 1)

    training_stats_str = "\n".join(training_stats)
    message = (
        f"Statistics for the previous month:\n\n"
        f"{training_stats_str}\n\n"
        f"_Average attendance:_ *{round(team_mean, 2)}*"
    )
    general_trainer = await user_tbl.get_general_trainer()
    await utils.send_message(
        dispatcher,
        general_trainer.user_id,
        keyboard=keyboards.GENERAL_TRAINER_DEFAULT,
        text=message,
        parse_mode="Markdown",
    )

    active_players = await user_tbl.get_active_team_players()
    for team_player in active_players:
        trainings_count = user_data.get(team_player.user_id, 0)
        if trainings_count >= team_mean:
            result = "above average. You're good 💪"
        else:
            result = "below average. You need to practise more 🏋️"
        await utils.send_message(
            dispatcher,
            team_player.user_id,
            text=f"In the last month you have been in training "
            f"*{trainings_count}* times.\n"
            f"This is {result}",
            parse_mode="Markdown",
            keyboard=keyboards.PLAYER_DEFAULT,
        )
