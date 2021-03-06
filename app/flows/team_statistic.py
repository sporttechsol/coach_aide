import arrow
from aiogram import Dispatcher, types

from app import utils
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
        f"Статистика посещений за предыдущий месяц:\n\n"
        f"{training_stats_str}\n\n"
        f"_Средняя посещаемость:_ *{round(team_mean, 2)}*"
    )
    general_trainer = await user_tbl.get_general_trainer()
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True, selective=True
    )
    markup.add("Профайл")
    markup.add("Список игроков")
    await utils.send_message(
        dispatcher,
        general_trainer.user_id,
        text=message,
        parse_mode="Markdown",
    )

    active_players = await user_tbl.get_active_team_players()
    for team_player in active_players:
        trainings_count = user_data.get(team_player.user_id, 0)
        if trainings_count >= team_mean:
            result = "выше среднего. Ты молодец."
        else:
            result = "ниже среднего. Тебе надо больше тренироваться."
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True, selective=True
        )
        markup.add("Профайл")
        await utils.send_message(
            dispatcher,
            team_player.user_id,
            text=f"За прошлый месяц ты был на тренировке "
            f"*{trainings_count}* раз.\n"
            f"Это {result}",
            parse_mode="Markdown",
            keyboard=markup
        )
