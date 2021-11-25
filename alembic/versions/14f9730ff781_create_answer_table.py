"""create answer table

Revision ID: 14f9730ff781
Revises: db3e84281ff5
Create Date: 2021-11-09 16:59:42.213315

"""
import sqlalchemy as sa

# revision identifiers, used by Alembic.
import sqlalchemy.dialects.postgresql as pg

from alembic import op

revision = "14f9730ff781"
down_revision = "db3e84281ff5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "answer",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("user.user_id"),
            nullable=False,
        ),
        sa.Column(
            "notification_id",
            sa.Integer,
            sa.ForeignKey("notification.id"),
            nullable=False,
        ),
        sa.Column(
            "notification_type",
            pg.ENUM(name="notification_type", create_type=False),
        ),
        sa.Column("event_at_ts", sa.Integer, nullable=False),
        sa.Column(
            "value",
            sa.Enum(
                "YES",
                "NO",
                "MAYBE",
                name="answer_value",
            ),
            nullable=False,
        ),
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
    op.drop_table("answer")
