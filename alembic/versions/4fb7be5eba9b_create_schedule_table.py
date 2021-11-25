"""create schedule table

Revision ID: 4fb7be5eba9b
Revises: f58a8f2cb758
Create Date: 2021-10-19 15:43:01.113561

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "4fb7be5eba9b"
down_revision = "f58a8f2cb758"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "schedule",
        sa.Column("id", sa.Integer, primary_key=True, unique=True),
        sa.Column("user_text", sa.TEXT, nullable=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("user.user_id"),
            nullable=False,
        ),
        sa.Column("day", sa.Integer, nullable=False),
        sa.Column("hours", sa.Integer, nullable=False),
        sa.Column("minutes", sa.Integer, nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "PAYDAY",
                "TRAINING",
                "EVENT",
                name="schedule_type",
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
    op.drop_table("schedule")
