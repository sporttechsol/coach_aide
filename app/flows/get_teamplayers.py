from aiogram import (
    Dispatcher,
    types,
)
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import (
    State,
    StatesGroup,
)

from app.storage import user_tbl
from app.storage.models import User
from app.storage.user_tbl import UserType


class ShowUsersState(StatesGroup):
    show_users = State()
    select_to_block = State()
    check_data = State()


def init(dp: Dispatcher):
    dp.register_message_handler(
        show_team_players, Text(equals="Список игроков")
    )
    dp.register_message_handler(
        select_next_action, state=ShowUsersState.show_users
    )
    dp.register_message_handler(
        select_users_to_delete, state=ShowUsersState.select_to_block
    )
    dp.register_message_handler(check_data, state=ShowUsersState.check_data)


async def show_team_players(message: types.Message, state: FSMContext):
    user = await user_tbl.get_user_by(message.from_user.id)
    if user and UserType(user.type) == UserType.GENERAL_TRAINER:
        players = await user_tbl.get_active_team_players()
        if len(players) > 0:
            async with state.proxy() as data:

                def form_string_and_store_data(index: int, usr: User):
                    data["showed_users"].append(
                        (usr.user_id, usr.first_name, usr.last_name)
                    )
                    return (
                        f"{index + 1}. {usr.first_name} {usr.last_name} "
                        f"- {usr.phone}"
                    )

                data["showed_users"] = []
                players_as_strings = map(
                    lambda x: form_string_and_store_data(x[0], x[1]),
                    enumerate(players),
                )
                markup = types.ReplyKeyboardMarkup(
                    resize_keyboard=True, selective=True
                )
                markup.add("Заблокировать игроков")
                markup.add("Назад")
                await ShowUsersState.show_users.set()
                await message.answer(
                    "\n".join(players_as_strings), reply_markup=markup
                )
        else:
            await message.answer("Пока ещё никто не зарегистрировался")

    else:
        await message.reply("Хорошая попытка, но нет")


async def select_next_action(message: types.Message, state: FSMContext):
    if message.text == "Заблокировать игроков":
        await ShowUsersState.select_to_block.set()
        await message.answer(
            "Пожалуйста, отправьте нам номер игрока которого "
            "нужно заблокировать. Или несколько номеров через запятую.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    elif message.text == "Назад":
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True, selective=True
        )
        markup.add("Профайл")
        markup.add("Список игроков")
        await state.reset_state()
        await message.answer("Хорошо", reply_markup=markup)
    else:
        await message.answer("Пожалуйста, воспользуйтесь клавиатурой")


async def select_users_to_delete(message: types.Message, state: FSMContext):
    try:
        indexes = map(lambda x: int(x), message.text.split(","))
        list_users = ""
        async with state.proxy() as data:
            data["user_to_delete"] = []
            for index in indexes:
                user_data = data["showed_users"][index - 1]
                user_id, first_name, last_name = user_data
                list_users += f"{first_name} {last_name}\n"
                data["user_to_delete"].append(user_id)
        await ShowUsersState.check_data.set()
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True, selective=True
        )
        markup.add("Да")
        markup.add("Нет")
        await message.answer(
            f"Список пользователей на удаление:\n\n{list_users}\n Всё верно?",
            reply_markup=markup,
        )
    except (ValueError, IndexError):
        await message.reply(
            "Неправильный ввод. "
            "Пожалуйста вводите только номер игрока "
            "или номера через запятую"
        )


async def check_data(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text == "Да":
            user_ids = list(map(lambda x: int(x), data["user_to_delete"]))
            await user_tbl.disable_users(user_ids)
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True, selective=True
            )
            markup.add("Профайл")
            markup.add("Список игроков")
            await state.reset_state()
            await message.answer(
                "Пользователи заблокированы", reply_markup=markup
            )
        elif message.text == "Нет":
            await ShowUsersState.select_to_block.set()
            await message.answer(
                "Пожалуйста, отправьте нам номер игрока которого "
                "нужно заблокировать. Или несколько номеров через запятую."
            )
            data["user_to_delete"] = []
            data["showed_users"] = []
        else:
            await message.answer("Пожалуйста, воспользуйтесь клавиатурой")
