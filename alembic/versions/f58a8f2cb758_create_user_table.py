"""create user table

Revision ID: f58a8f2cb758
Revises:
Create Date: 2021-10-19 15:28:06.768732

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "f58a8f2cb758"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, nullable=False, unique=True),
        sa.Column("first_name", sa.String(50), nullable=False),
        sa.Column("last_name", sa.String(50), nullable=False),
        sa.Column("phone", sa.String(16), nullable=False),
        sa.Column("birthday", sa.Date, nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "TEAM_PLAYER",
                "GENERAL_TRAINER",
                "TRAINER",
                name="user_type",
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
    op.drop_table("user")
