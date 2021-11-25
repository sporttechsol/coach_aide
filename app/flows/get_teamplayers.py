from aiogram import (
    Dispatcher,
    types,
)
from aiogram.dispatcher.filters import Text

from app.storage import user_tbl


def init(dp: Dispatcher):
    dp.register_message_handler(
        show_team_players, Text(equals="Список Игроков")
    )


async def show_team_players(message: types.Message):
    players = await user_tbl.get_active_team_players()
    players_as_strings = map(
        lambda x: f"{x.first_name} {x.last_name} - {x.phone}", players
    )
    await message.answer("\n".join(players_as_strings))
