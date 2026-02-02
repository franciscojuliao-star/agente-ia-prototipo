"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar enum de roles
    op.execute("CREATE TYPE userrole AS ENUM ('PROFESSOR', 'ALUNO')")

    # Criar enum de tipo de material
    op.execute("CREATE TYPE tipomaterial AS ENUM ('PDF', 'VIDEO', 'LINK', 'TEXTO')")

    # Criar enum de tipo de conteúdo
    op.execute("CREATE TYPE tipoconteudo AS ENUM ('QUIZ', 'RESUMO', 'FLASHCARD')")

    # Criar enum de status de conteúdo
    op.execute("CREATE TYPE statusconteudo AS ENUM ('AGUARDANDO_APROVACAO', 'APROVADO', 'REJEITADO')")

    # Criar tabela de usuários
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('senha_hash', sa.String(255), nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('PROFESSOR', 'ALUNO', name='userrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Criar tabela de materiais
    op.create_table(
        'materiais',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('professor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('disciplina', sa.String(255), nullable=False, index=True),
        sa.Column('titulo', sa.String(500), nullable=False),
        sa.Column('tipo', sa.Enum('PDF', 'VIDEO', 'LINK', 'TEXTO', name='tipomaterial'), nullable=False),
        sa.Column('conteudo_original', sa.Text(), nullable=True),
        sa.Column('url', sa.String(2048), nullable=True),
        sa.Column('arquivo_path', sa.String(500), nullable=True),
        sa.Column('num_chunks', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Criar tabela de conteúdos gerados
    op.create_table(
        'conteudos_gerados',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('professor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tipo', sa.Enum('QUIZ', 'RESUMO', 'FLASHCARD', name='tipoconteudo'), nullable=False),
        sa.Column('conteudo_json', postgresql.JSON(), nullable=False),
        sa.Column('status', sa.Enum('AGUARDANDO_APROVACAO', 'APROVADO', 'REJEITADO', name='statusconteudo'), nullable=False, index=True),
        sa.Column('material_fonte_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False),
        sa.Column('topico', sa.String(500), nullable=False),
        sa.Column('disciplina', sa.String(255), nullable=False, index=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('aprovado_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('modificacoes_professor', postgresql.JSON(), nullable=True),
        sa.Column('motivo_rejeicao', sa.String(1000), nullable=True),
    )

    # Criar tabela de tentativas de alunos
    op.create_table(
        'tentativas_alunos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('aluno_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('conteudo_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conteudos_gerados.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('respostas_json', postgresql.JSON(), nullable=False),
        sa.Column('pontuacao', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('tentativas_alunos')
    op.drop_table('conteudos_gerados')
    op.drop_table('materiais')
    op.drop_table('users')

    op.execute("DROP TYPE statusconteudo")
    op.execute("DROP TYPE tipoconteudo")
    op.execute("DROP TYPE tipomaterial")
    op.execute("DROP TYPE userrole")
