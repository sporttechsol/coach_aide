from datetime import date
from enum import Enum

import arrow

from app.storage import session
from app.storage.models import User


class UserType(Enum):
    TEAM_PLAYER = "TEAM_PLAYER"
    GENERAL_TRAINER = "GENERAL_TRAINER"
    TRAINER = "TRAINER"


async def create_or_update_team_player(
    user_id: int, first_name: str, last_name: str, phone: str, birthday: date
):
    user = await get_user_by(user_id)
    if user:
        await _update_user(
            user,
            first_name,
            last_name,
            phone,
            birthday,
        )
    else:
        await _create_user(
            UserType.TEAM_PLAYER.value,
            user_id,
            first_name,
            last_name,
            phone,
            birthday,
        )

    return user is not None


async def disable_users(user_ids: list[int]):
    for user_id in user_ids:
        user = await get_user_by(user_id)
        user.enabled = False

    session.commit()


async def create_general_trainer(
    user_id: int, first_name: str, last_name: str, phone: str, birthday: date
):
    await _create_user(
        UserType.GENERAL_TRAINER.value,
        user_id,
        first_name,
        last_name,
        phone,
        birthday,
    )


async def _create_user(
    user_type: str,
    user_id: int,
    first_name: str,
    last_name: str,
    phone: str,
    birthday: date,
):
    session.add(
        User(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            birthday=birthday,
            type=user_type,
            enabled=True,
        )
    )
    session.commit()


async def _update_user(
    user: User,
    first_name: str,
    last_name: str,
    phone: str,
    birthday: date,
):
    user.first_name = first_name
    user.last_name = last_name
    user.phone = phone
    user.birthday = birthday
    user.updated_at = arrow.utcnow().date()
    session.commit()


async def get_user_by(user_id: int) -> User:
    return session.query(User).filter(User.user_id == user_id).first()


async def is_enabled(user_id: int) -> bool:
    return (
        session.query(User)
        .filter(User.user_id == user_id)
        .filter(User.enabled)
        .first()
        is not None
    )


async def get_active_team_players() -> list[User]:
    return (
        session.query(User)
        .filter(User.enabled)
        .filter(User.type == UserType.TEAM_PLAYER.value)
        .all()
    )


async def get_active_trainers() -> list[User]:
    return (
        session.query(User)
        .filter(User.enabled)
        .filter(
            User.type.in_(
                [UserType.GENERAL_TRAINER.value, UserType.TRAINER.value]
            )
        )
        .all()
    )


async def get_general_trainer() -> User:
    return (
        session.query(User)
        .filter(User.enabled)
        .filter(User.type == UserType.GENERAL_TRAINER.value)
        .first()
    )
