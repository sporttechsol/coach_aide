# coding: utf-8
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
metadata = Base.metadata


class User(Base):
    __tablename__ = "user"

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('user_id_seq'::regclass)"),
    )
    user_id = Column(Integer, nullable=False, unique=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(16), nullable=False)
    birthday = Column(Date, nullable=False)
    type = Column(
        Enum("TEAM_PLAYER", "GENERAL_TRAINER", "TRAINER", name="user_type"),
        nullable=False,
    )
    enabled = Column(Boolean, nullable=False)
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class Schedule(Base):
    __tablename__ = "schedule"

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('schedule_id_seq'::regclass)"),
    )
    user_text = Column(Text)
    user_id = Column(ForeignKey("user.user_id"), nullable=False)
    day = Column(Integer, nullable=False)
    hours = Column(Integer, nullable=False)
    minutes = Column(Integer, nullable=False)
    type = Column(
        Enum("PAYDAY", "TRAINING", "EVENT", name="schedule_type"),
        nullable=False,
    )
    enabled = Column(Boolean, nullable=False)
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    user = relationship("User")


class Notification(Base):
    __tablename__ = "notification"

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('notification_id_seq'::regclass)"),
    )
    notify_at = Column(DateTime, nullable=False)
    event_at_ts = Column(Integer, nullable=False)
    user_text = Column(Text)
    schedule_id = Column(ForeignKey("schedule.id"))
    type = Column(
        Enum(
            "PAYDAY_QUESTION",
            "POLL_BEFORE_TRAINING",
            "POLL_AFTER_TRAINING",
            "REPORT_AFTER_TRAINING",
            "REPORT_BEFORE_TRAINING",
            "MONTH_REPORT_USER",
            "MONTH_REPORT_TRAINER",
            "YEAR_REPORT_TRAINER",
            "PAYDAY_REPORT",
            "BIRTHDAY",
            "CUSTOM_EVENT",
            name="notification_type",
        ),
        nullable=False,
    )
    enabled = Column(Boolean, nullable=False)
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    schedule = relationship("Schedule")


class Answer(Base):
    __tablename__ = "answer"

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('answer_id_seq'::regclass)"),
    )
    user_id = Column(ForeignKey("user.user_id"), nullable=False)
    notification_id = Column(ForeignKey("notification.id"), nullable=False)
    notification_type = Column(
        Enum(
            "PAYDAY_QUESTION",
            "POLL_BEFORE_TRAINING",
            "POLL_AFTER_TRAINING",
            "REPORT_AFTER_TRAINING",
            "REPORT_BEFORE_TRAINING",
            "MONTH_REPORT_USER",
            "MONTH_REPORT_TRAINER",
            "YEAR_REPORT_TRAINER",
            "PAYDAY_REPORT",
            "BIRTHDAY",
            "CUSTOM_EVENT",
            name="notification_type",
        )
    )
    event_at_ts = Column(Integer, nullable=False)
    value = Column(
        Enum("YES", "NO", "MAYBE", name="answer_value"), nullable=False
    )
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    notification = relationship("Notification")
    user = relationship("User")
