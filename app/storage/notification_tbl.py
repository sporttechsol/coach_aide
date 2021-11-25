from enum import Enum

import arrow

from app.settings import APP_CONF
from app.storage import (
    schedule_dbl,
    session,
)
from app.storage.models import Notification
from app.storage.schedule_dbl import ScheduleType

POLL_BEFORE_SHIFT = -3
POLL_AFTER_SHIFT = 3
REPORT_BEFORE_SHIFT = -1
REPORT_AFTER_SHIFT = 1


class NotificationType(Enum):
    PAYDAY_QUESTION = "PAYDAY_QUESTION"
    POLL_BEFORE_TRAINING = "POLL_BEFORE_TRAINING"
    POLL_AFTER_TRAINING = "POLL_AFTER_TRAINING"
    REPORT_AFTER_TRAINING = "REPORT_AFTER_TRAINING"
    REPORT_BEFORE_TRAINING = "REPORT_BEFORE_TRAINING"
    MONTH_REPORT_USER = "MONTH_REPORT_USER"
    MONTH_REPORT_TRAINER = "MONTH_REPORT_TRAINER"
    YEAR_REPORT_TRAINER = "YEAR_REPORT_TRAINER"
    PAYDAY_REPORT = "PAYDAY_REPORT"
    BIRTHDAY = "BIRTHDAY"
    CUSTOM_EVENT = "CUSTOM_EVENT"


async def create_new_training_events():
    training_schedules = await schedule_dbl.get_active_by(
        ScheduleType.TRAINING.value
    )
    for training_schedule in training_schedules:
        last_future_event = await get_last_future_by(training_schedule.id)
        if last_future_event is None:
            now = arrow.utcnow()
            start_date = now.shift(weekday=training_schedule.day - 1).replace(
                hour=training_schedule.hours, minute=training_schedule.minutes
            )
            end_date = start_date.shift(months=1)
            interval = arrow.Arrow.range(
                "week", start_date.datetime, end_date.datetime
            )

            for event_at in interval:
                six_hours_before = event_at.shift(minutes=POLL_BEFORE_SHIFT)
                session.add(
                    Notification(
                        notify_at=six_hours_before.datetime,
                        event_at_ts=event_at.int_timestamp,
                        schedule_id=training_schedule.id,
                        type=NotificationType.POLL_BEFORE_TRAINING.value,
                        enabled=True,
                    )
                )
                one_and_half_hour_after = event_at.shift(
                    minutes=POLL_AFTER_SHIFT
                )
                session.add(
                    Notification(
                        notify_at=one_and_half_hour_after.datetime,
                        event_at_ts=event_at.int_timestamp,
                        schedule_id=training_schedule.id,
                        type=NotificationType.POLL_AFTER_TRAINING.value,
                        enabled=True,
                    )
                )
                one_and_half_hour_before = event_at.shift(
                    minutes=REPORT_BEFORE_SHIFT
                )
                session.add(
                    Notification(
                        notify_at=one_and_half_hour_before.datetime,
                        event_at_ts=event_at.int_timestamp,
                        schedule_id=training_schedule.id,
                        type=NotificationType.REPORT_BEFORE_TRAINING.value,
                        enabled=True,
                    )
                )
                six_hours_after = event_at.shift(minutes=REPORT_AFTER_SHIFT)
                session.add(
                    Notification(
                        notify_at=six_hours_after.datetime,
                        event_at_ts=event_at.int_timestamp,
                        schedule_id=training_schedule.id,
                        type=NotificationType.REPORT_AFTER_TRAINING.value,
                        enabled=True,
                    )
                )

        session.commit()


async def create_new_payday_events():
    payday_schedules = await schedule_dbl.get_active_by("PAYDAY")
    for payday_schedule in payday_schedules:
        last_future_notification = await get_last_future_by(payday_schedule.id)
        if last_future_notification is None:
            now = arrow.utcnow()
            start_date = now.shift(days=payday_schedule.day).replace(
                hour=payday_schedule.hours, minute=payday_schedule.minutes
            )
            if start_date < now:
                start_date = start_date.shift(months=1)

            end_date = start_date.shift(months=4)
            interval = arrow.Arrow.range(
                "month", start_date.datetime, end_date.datetime
            )

            for event_at in interval:
                session.add(
                    Notification(
                        user_text=payday_schedule.user_text,
                        notify_at=event_at.datetime,
                        event_at_ts=event_at.int_timestamp,
                        schedule_id=payday_schedule.id,
                        type=NotificationType.PAYDAY_QUESTION.value,
                        enabled=True,
                    )
                )
                notify_at = event_at.shift(weeks=1)
                session.add(
                    Notification(
                        notify_at=notify_at.datetime,
                        event_at_ts=event_at.int_timestamp,
                        schedule_id=payday_schedule.id,
                        type=NotificationType.PAYDAY_REPORT.value,
                        enabled=True,
                    )
                )

    session.commit()


async def get_last_future_by(schedule_id: str) -> Notification:
    now_with_tz = arrow.utcnow().to(APP_CONF.team.timezone).datetime
    return (
        session.query(Notification)
        .filter(Notification.schedule_id == schedule_id)
        .filter(Notification.notify_at > now_with_tz)
        .order_by(Notification.notify_at.desc())
        .first()
    )


async def get_next_for_team_players() -> Notification:
    now_with_tz = (
        arrow.utcnow().to(APP_CONF.team.timezone).datetime.replace(tzinfo=None)
    )
    return (
        session.query(Notification)
        .filter(Notification.notify_at < now_with_tz)
        .filter(Notification.enabled)
        .filter(
            Notification.type.in_(
                (
                    NotificationType.POLL_BEFORE_TRAINING.value,
                    NotificationType.POLL_AFTER_TRAINING.value,
                    NotificationType.PAYDAY_QUESTION.value,
                )
            )
        )
        .order_by(Notification.notify_at.desc())
        .first()
    )


async def get_next_for_trainers() -> Notification:
    now_with_tz = (
        arrow.utcnow().to(APP_CONF.team.timezone).datetime.replace(tzinfo=None)
    )
    return (
        session.query(Notification)
        .filter(Notification.notify_at < now_with_tz)
        .filter(Notification.enabled)
        .filter(
            Notification.type.in_(
                (
                    NotificationType.REPORT_BEFORE_TRAINING.value,
                    NotificationType.REPORT_AFTER_TRAINING.value,
                    NotificationType.PAYDAY_REPORT.value,
                    NotificationType.MONTH_REPORT_TRAINER.value,
                    NotificationType.YEAR_REPORT_TRAINER.value,
                )
            )
        )
        .order_by(Notification.notify_at.desc())
        .first()
    )


async def disable(notification_id: int):
    session.query(Notification).filter(
        Notification.id == notification_id
    ).update({"enabled": False})
    session.commit()
