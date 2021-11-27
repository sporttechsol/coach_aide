from datetime import date
from enum import Enum

from app.storage import session
from app.storage.models import User


class UserType(Enum):
    TEAM_PLAYER = "TEAM_PLAYER"
    GENERAL_TRAINER = "GENERAL_TRAINER"
    TRAINER = "TRAINER"


async def create_team_player(
    user_id: int, first_name: str, last_name: str, phone: str, birthday: date
):
    await _create_user(
        UserType.TEAM_PLAYER.value,
        user_id,
        first_name,
        last_name,
        phone,
        birthday,
    )


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


async def is_registered(user_id: int) -> bool:
    return (
        session.query(User).filter(User.user_id == user_id).first() is not None
    )


async def is_enabled(user_id: int) -> bool:
    return (
        session.query(User)
        .filter(User.user_id == user_id)
        .filter(User.enabled)
        .first()
        is None
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
                UserType.GENERAL_TRAINER.value, UserType.TRAINER.value
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
