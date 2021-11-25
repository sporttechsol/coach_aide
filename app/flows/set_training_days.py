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

from app import utils
from app.storage import (
    notification_tbl,
    schedule_dbl,
)

WEEK_DAYS = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
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
            await message.reply("Введите число от 1 до 7")
            return

    except ValueError:
        await message.reply("Введите число от 1 до 7")
        return

    async with state.proxy() as data:
        data["trainings"] = {}
        data["trainings"]["count"] = training_count
        await TrainingsDays.set_trainings_time.set()
        await message.reply(
            f"В неделю будет {data['trainings']['count']} тренировки"
        )
        await message.answer(
            "Введите по очереди информацию о каждой из тренировок. "
            "Формат [номер_дня_недели,чч:мм]"
        )


async def set_training_time(message: types.Message, state: FSMContext):
    try:
        week_day, training_time = message.text.replace(" ", "").split(",")
        week_day = int(week_day)

        if week_day < 1 or week_day > 7:
            await message.reply(
                "Неправильный формат дня недели. "
                "День недели должен быть от 1 и до 7, "
                "где 1 - это понедельник, а 7 - это воскресенье"
            )
            return

    except ValueError:
        await message.reply(
            "Не удаёться прочитать сообщение. "
            "Пожалуйста, введите его в формате [номер_дня_недели, чч:мм]"
        )
        return

    p = re.compile("[0-9][0-9]:[0-9][0-9]")
    training_times = p.findall(training_time)
    if len(training_times) != 1:
        await message.reply(
            "Не удаётся прочитать время. "
            "Пожалуйста, введите его в формате [чч:мм]"
        )
        return

    hours, minutes = [int(x) for x in training_times[0].split(":")]

    if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
        await message.reply(
            "Неправильный формат ввода времени. Часы должны быть от 0 до 23, "
            "а минуты от 0 до 59. Примеры: 00:00"
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
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True, selective=True
            )
            markup.add(
                "Да",
                "Нет",
            )
            await TrainingsDays.check_data.set()
            await message.answer(
                f"Давайте перепроверим введённые вами данные.\n"
                f"В неделю будет {training_count} тренировки:\n"
                f"{trainings_list} Всё верно?",
                reply_markup=markup,
            )


async def check_data(message: types.Message, state: FSMContext):
    if message.text == "Да":
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
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True, selective=True
        )
        markup.add(
            "Список Игроков",
        )
        await message.answer(
            "Отлично. Спасибо за настройку. Теперь я буду присылать "
            "вам список тех, кто придёт на тренировку, "
            "месячный отчёт по посещаемости, "
            "напоминать про дни рождения игроков, "
            "а так же отчёт по оплате",
            reply_markup=markup,
        )
    elif message.text == "Нет":
        await TrainingsDays.set_training_count.set()
        await message.answer(
            "Сколько будет тренировок в неделю?",
            reply_markup=types.ReplyKeyboardRemove(),
        )
