import re

from aiogram import (
    Dispatcher,
    types,
)
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import (
    State,
    StatesGroup,
)

from app import (
    keyboards,
    text,
    utils,
)
from app.storage import (
    notification_tbl,
    schedule_dbl,
)

WEEK_DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def init(dp: Dispatcher):
    dp.register_message_handler(
        set_training_count, state=TrainingsDays.set_training_count
    )
    dp.register_message_handler(
        set_training_time, state=TrainingsDays.set_trainings_time
    )
    dp.register_message_handler(check_data, state=TrainingsDays.check_data)


class TrainingsDays(StatesGroup):
    set_training_count = State()
    set_trainings_time = State()
    update_training = State()
    check_data = State()


async def set_training_count(message: types.Message, state: FSMContext):
    try:
        training_count = int(message.text)
        if 1 > training_count or training_count > 7:
            await message.reply(
                text.ENTER_ONE_ORE_SEVEN, parse_mode="Markdown"
            )
            return

    except ValueError:
        await message.reply(text.ENTER_ONE_ORE_SEVEN, parse_mode="Markdown")
        return

    async with state.proxy() as data:
        data["trainings"] = {}
        data["trainings"]["count"] = training_count
        await TrainingsDays.set_trainings_time.set()
        await message.reply(
            f"There will be *{data['trainings']['count']}* training per week",
            parse_mode="Markdown",
        )
        await message.answer(
            "Enter the information about each of the training "
            "sessions in turn. Format [number_day_week,hh:mm]. "
            "_Example: 1,13:00_",
            parse_mode="Markdown",
        )


async def set_training_time(message: types.Message, state: FSMContext):
    try:
        week_day, training_time = message.text.replace(" ", "").split(",")
        week_day = int(week_day)

        if week_day < 1 or week_day > 7:
            await message.reply(
                "Incorrect format of the day of the week. "
                "The day of the week should be from *1 to 7*,"
                "where *1 is Monday and 7 is Sunday*.",
                parse_mode="Markdown",
            )
            return

    except ValueError:
        await message.reply(
            "Cannot read the message. "
            "Please enter it in the format [day_of_week, hh:mm].  "
            "_Example: 1,13:00_",
            parse_mode="Markdown",
        )
        return

    p = re.compile("[0-9][0-9]:[0-9][0-9]")
    training_times = p.findall(training_time)
    if len(training_times) != 1:
        await message.reply(
            "Can't read the time. "
            "Please enter it in [hh:mm] format. _Example: 13:00_",
            parse_mode="Markdown",
        )
        return

    hours, minutes = [int(x) for x in training_times[0].split(":")]

    if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
        await message.reply(
            "Incorrect time entry format. The hours should be *0 to 23*, "
            "and the minutes are *from 0 to 59*. _Examples: 00:00_",
            parse_mode="Markdown",
        )
        return

    async with state.proxy() as data:
        if "list" not in data["trainings"]:
            data["trainings"]["list"] = []

        data["trainings"]["list"].append(
            {"day": week_day, "hours": hours, "minutes": minutes}
        )
        training = data["trainings"]["list"][-1]
        time = utils.format_time(training["hours"], training["minutes"])
        await message.reply(
            f"{len(data['trainings']['list'])}. "
            f"{WEEK_DAYS[training['day'] - 1]} в {time}."
        )

        if len(data["trainings"]["list"]) == data["trainings"]["count"]:
            await TrainingsDays.check_data.set()
            training_count = data["trainings"]["count"]
            trainings_list = ""
            for i, training in enumerate(data["trainings"]["list"]):
                time = utils.format_time(
                    training["hours"], training["minutes"]
                )
                trainings_list += (
                    f"{i+1}. {WEEK_DAYS[training['day'] - 1]} в {time}\n"
                )
            await TrainingsDays.check_data.set()
            await message.answer(
                f"Let's double-check the data you entered.\n"
                f"There will be *{training_count}* training per week:\n"
                f"*{trainings_list}* Is that correct?",
                parse_mode="Markdown",
                reply_markup=keyboards.YES_OR_NO,
            )


async def check_data(message: types.Message, state: FSMContext):
    if message.text == text.YES:
        async with state.proxy() as data:
            for i, training in enumerate(data["trainings"]["list"]):
                await schedule_dbl.create_training_schedule(
                    user_id=message.from_user.id,
                    day=training["day"],
                    hours=training["hours"],
                    minutes=training["minutes"],
                )
        await notification_tbl.create_new_training_events()
        await state.reset_state()
        await message.answer(
            "Great. Thank you for the setup. Now I'll be sending "
            "you a list of who's coming to practice,"
            "a monthly attendance report,"
            "remind you of players' birthdays,"
            "as well as a payment report.",
            reply_markup=keyboards.GENERAL_TRAINER_DEFAULT,
        )
    elif message.text == text.NO:
        await TrainingsDays.set_training_count.set()
        await message.answer(
            "How many training sessions will there be a week?",
            reply_markup=types.ReplyKeyboardRemove(),
        )
