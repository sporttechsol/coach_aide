from enum import Enum

from app.storage import session
from app.storage.models import Answer
from app.storage.notification_tbl import NotificationType


class AnswerValue(Enum):
    YES = "YES"
    NO = "NO"
    MAYBE = "MAYBE"


async def create(
    user_id: int,
    notification_id: int,
    notification_type: NotificationType,
    event_at_ts: int,
    value: AnswerValue,
):
    session.add(
        Answer(
            user_id=user_id,
            notification_id=notification_id,
            event_at_ts=event_at_ts,
            notification_type=notification_type.value,
            value=value.value,
        )
    )
    session.commit()


async def get_last_answers_by(
    notification_type: NotificationType, event_at_ts: int
) -> list[Answer]:
    return (
        session.query(Answer)
        .distinct(Answer.user_id)
        .filter(Answer.notification_type == notification_type.value)
        .filter(Answer.event_at_ts == event_at_ts)
        .order_by(Answer.user_id, Answer.created_at.desc())
        .all()
    )
