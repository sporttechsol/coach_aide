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

from app import (
    keyboards,
    text,
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
        show_team_players, Text(equals=text.LIST_OF_PLAYERS)
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
                await ShowUsersState.show_users.set()
                await message.answer(
                    "\n".join(players_as_strings),
                    reply_markup=keyboards.SHOW_USERS,
                )
        else:
            await message.answer("No one has signed up yet")

    else:
        await message.reply("Nice try, but no. 😂")


async def select_next_action(message: types.Message, state: FSMContext):
    if message.text == text.BLOCK_PLAYERS:
        await ShowUsersState.select_to_block.set()
        await message.answer(
            "Please, send us the number of the player "
            "to be blocked. Or several numbers, separated by commas. "
            "_Example:1,2,3 or just 1_",
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode="Markdown",
        )
    elif message.text == text.BACK:
        await state.reset_state()
        await message.answer(
            "Good. 😊", reply_markup=keyboards.GENERAL_TRAINER_DEFAULT
        )
    else:
        await message.answer(text.PLEASE_USE_KEYBOARD)


async def select_users_to_delete(message: types.Message, state: FSMContext):
    try:
        indexes = map(lambda x: int(x), message.text.split(","))
        list_users = ""
        async with state.proxy() as data:
            data["user_to_delete"] = []
            for index in indexes:
                user_data = data["showed_users"][index - 1]
                user_id, first_name, last_name = user_data
                list_users += f"*{first_name} {last_name}*\n"
                data["user_to_delete"].append(user_id)
        await ShowUsersState.check_data.set()
        await message.answer(
            f"List of users to delete:\n\n{list_users}\n All right?",
            reply_markup=keyboards.YES_OR_NO,
            parse_mode="Markdown",
        )
    except (ValueError, IndexError):
        await message.reply(
            "Incorrect input. "
            "Please enter the player number only"
            "or numbers, separated by commas"
        )


async def check_data(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text == text.YES:
            user_ids = list(map(lambda x: int(x), data["user_to_delete"]))
            await user_tbl.disable_users(user_ids)
            await state.reset_state()
            await message.answer(
                "Users blocked 🔨",
                reply_markup=keyboards.GENERAL_TRAINER_DEFAULT,
            )
        elif message.text == text.NO:
            await ShowUsersState.select_to_block.set()
            await message.answer(
                "Please send us the number of the player "
                "to be blocked. Or several numbers, separated by commas"
            )
            data["user_to_delete"] = []
            data["showed_users"] = []
        else:
            await message.answer(text.PLEASE_USE_KEYBOARD)
