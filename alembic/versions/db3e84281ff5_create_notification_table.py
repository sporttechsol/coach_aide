"""create notification table

Revision ID: db3e84281ff5
Revises: 4fb7be5eba9b
Create Date: 2021-10-23 15:21:23.795636

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.


revision = "db3e84281ff5"
down_revision = "4fb7be5eba9b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notification",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("notify_at", sa.DateTime, nullable=False),
        sa.Column("event_at_ts", sa.Integer, nullable=False),
        sa.Column("user_text", sa.Text, nullable=True),
        sa.Column(
            "schedule_id",
            sa.Integer,
            sa.ForeignKey("schedule.id"),
            nullable=True,
        ),
        sa.Column(
            "type",
            sa.Enum(
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
        ),
        sa.Column("enabled", sa.Boolean, nullable=False, default=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("notification")
