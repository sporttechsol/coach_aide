from enum import Enum

from app.storage import session
from app.storage.models import Schedule


class ScheduleType(Enum):
    PAYDAY = "PAYDAY"
    TRAINING = "TRAINING"
    EVENT = "EVENT"


async def create_payday_schedule(
    user_id: int, day: int, hours: int, minutes: int, user_text: str
):
    await _create(
        ScheduleType.PAYDAY.value, user_id, day, hours, minutes, user_text
    )


async def create_training_schedule(
    user_id: int, day: int, hours: int, minutes: int
):
    await _create(
        ScheduleType.TRAINING.value,
        user_id,
        day,
        hours,
        minutes,
    )


async def get_active_by(schedule_type: str) -> list[Schedule]:
    return (
        session.query(Schedule)
        .filter(Schedule.enabled)
        .filter(Schedule.type == schedule_type)
        .all()
    )


async def _create(
    schedule_type: str,
    user_id: int,
    day: int,
    hours: int,
    minutes: int,
    user_text: str = None,
):
    session.add(
        Schedule(
            user_text=user_text,
            user_id=user_id,
            day=day,
            hours=hours,
            minutes=minutes,
            type=schedule_type,
            enabled=True,
        )
    )
    session.commit()
