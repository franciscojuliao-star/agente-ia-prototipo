#!/usr/bin/env python3
"""
Script de migração para adicionar:
1. Valor 'ADMIN' ao enum userrole
2. Coluna 'ativo' à tabela users
3. Criar usuário administrador padrão
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app.auth.jwt import get_password_hash
from app.models import User, UserRole


def run_migration():
    """Executa a migração do banco de dados."""
    print("Iniciando migração...")

    with engine.connect() as conn:
        # 1. Adiciona valor ADMIN ao enum userrole (se não existir)
        print("1. Adicionando ADMIN ao enum userrole...")
        try:
            conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'ADMIN'"))
            conn.commit()
            print("   OK - ADMIN adicionado ao enum")
        except Exception as e:
            print(f"   AVISO: {e}")
            conn.rollback()

        # 2. Adiciona coluna ativo (se não existir)
        print("2. Adicionando coluna 'ativo' à tabela users...")
        try:
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT FALSE
            """))
            conn.commit()
            print("   OK - Coluna ativo adicionada")
        except Exception as e:
            print(f"   AVISO: {e}")
            conn.rollback()

        # 3. Ativa usuários existentes (que já estavam no sistema antes da mudança)
        print("3. Ativando usuários existentes...")
        try:
            result = conn.execute(text("""
                UPDATE users
                SET ativo = TRUE
                WHERE ativo = FALSE AND role != 'ADMIN'
            """))
            conn.commit()
            print(f"   OK - {result.rowcount} usuários ativados")
        except Exception as e:
            print(f"   AVISO: {e}")
            conn.rollback()

    # 4. Cria usuário administrador padrão
    print("4. Criando usuário administrador padrão...")
    db = SessionLocal()
    try:
        # Verifica se já existe um admin
        admin_exists = db.query(User).filter(User.role == UserRole.ADMIN).first()

        if admin_exists:
            print(f"   AVISO - Já existe um administrador: {admin_exists.email}")
        else:
            admin = User(
                email="admin@ava.com",
                senha_hash=get_password_hash("admin123"),
                nome="Administrador",
                role=UserRole.ADMIN,
                ativo=True,  # Admin já começa ativo
            )
            db.add(admin)
            db.commit()
            print("   OK - Administrador criado:")
            print("   Email: admin@ava.com")
            print("   Senha: admin123")
            print("   IMPORTANTE: Altere a senha após o primeiro login!")

    except Exception as e:
        print(f"   ERRO: {e}")
        db.rollback()
    finally:
        db.close()

    print("\nMigração concluída!")


if __name__ == "__main__":
    run_migration()
