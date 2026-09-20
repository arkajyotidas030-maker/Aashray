"""initial evidence/incident schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("last_lat", sa.Float(), nullable=True),
        sa.Column("last_lon", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("t", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("emergency_type", sa.String(64), nullable=True),
        sa.Column("people_count", sa.Integer(), nullable=True),
        sa.Column("severity", sa.Integer(), nullable=True),
        sa.Column("trapped", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("injury", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("media_path", sa.String(512), nullable=True),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column("source", sa.String(32), nullable=False, server_default="live"),
        sa.Column("as_of", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_evidence_user_id", "evidence", ["user_id"])
    op.create_index("ix_evidence_t", "evidence", ["t"])

    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("centroid", sa.Text(), nullable=True),
        sa.Column("geometry", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("isolated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("disagreement", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sitrep_cache", sa.Text(), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_incidents_code", "incidents", ["code"], unique=True)

    op.create_table(
        "incident_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("evidence.id"), nullable=False),
        sa.Column("contribution_score", sa.Float(), nullable=False, server_default="0"),
        sa.UniqueConstraint("incident_id", "evidence_id"),
    )
    op.create_index("ix_incident_evidence_incident_id", "incident_evidence", ["incident_id"])
    op.create_index("ix_incident_evidence_evidence_id", "incident_evidence", ["evidence_id"])

    op.create_table(
        "checkins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("t", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(32), nullable=False, server_default="live"),
    )
    op.create_index("ix_checkins_user_id", "checkins", ["user_id"])
    op.create_index("ix_checkins_t", "checkins", ["t"])

    op.create_table(
        "blocked_edges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("edge_id", sa.String(64), nullable=False),
        sa.Column("t", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(32), nullable=False, server_default="simulated"),
    )
    op.create_index("ix_blocked_edges_edge_id", "blocked_edges", ["edge_id"])

    op.create_table(
        "alert_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("zone_level", sa.String(32), nullable=False),
        sa.Column("t", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "incident_id", "zone_level"),
    )
    op.create_index("ix_alert_events_user_id", "alert_events", ["user_id"])
    op.create_index("ix_alert_events_incident_id", "alert_events", ["incident_id"])

    op.create_table(
        "demo_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tick", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rainfall_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("playing", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("as_of", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("demo_state")
    op.drop_table("alert_events")
    op.drop_table("blocked_edges")
    op.drop_table("checkins")
    op.drop_table("incident_evidence")
    op.drop_table("incidents")
    op.drop_table("evidence")
    op.drop_table("users")
