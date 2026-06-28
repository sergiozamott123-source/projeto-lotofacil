"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-27
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sorteios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("numero_concurso", sa.Integer(), nullable=False),
        sa.Column("data_sorteio", sa.DateTime(), nullable=False),
        sa.Column("dezenas", postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column("total_pares", sa.Integer(), nullable=False),
        sa.Column("total_impares", sa.Integer(), nullable=False),
        sa.Column("repetidas_anterior", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("numero_concurso"),
    )
    op.create_index(op.f("ix_sorteios_id"), "sorteios", ["id"], unique=False)
    op.create_index(op.f("ix_sorteios_numero_concurso"), "sorteios", ["numero_concurso"], unique=True)

    op.create_table(
        "apostas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("dezenas", postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column("numero_concurso_alvo", sa.Integer(), nullable=True),
        sa.Column("origem", sa.Enum("manual", "ia", name="origemenum"), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_apostas_id"), "apostas", ["id"], unique=False)

    op.create_table(
        "jogos_realizados",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("aposta_id", sa.Integer(), nullable=False),
        sa.Column("numero_concurso", sa.Integer(), nullable=False),
        sa.Column("dezenas_acertadas", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("total_acertos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("premiado", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("faixa_premio", sa.String(), nullable=True),
        sa.Column("conferido_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["aposta_id"], ["apostas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_jogos_realizados_id"), "jogos_realizados", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_jogos_realizados_id"), table_name="jogos_realizados")
    op.drop_table("jogos_realizados")
    op.drop_index(op.f("ix_apostas_id"), table_name="apostas")
    op.drop_table("apostas")
    op.drop_index(op.f("ix_sorteios_numero_concurso"), table_name="sorteios")
    op.drop_index(op.f("ix_sorteios_id"), table_name="sorteios")
    op.drop_table("sorteios")
    op.execute("DROP TYPE IF EXISTS origemenum")
