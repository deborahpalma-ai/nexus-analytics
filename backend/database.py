"""
NEXUS Analytics — database.py
-------------------------------
Camada de dados: PostgreSQL (Neon) via psycopg2.
Todas as queries são SQL puro para demonstrar domínio da linguagem.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st


def get_connection():
    """
    Retorna uma conexão PostgreSQL.
    Lê a DATABASE_URL dos secrets do Streamlit Cloud ou variável de ambiente.
    """
    try:
        db_url = st.secrets["DATABASE_URL"]
    except Exception:
        db_url = os.environ.get("DATABASE_URL", "")
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    return conn


def init_db():
    """Cria todas as tabelas caso não existam."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         SERIAL PRIMARY KEY,
            name       TEXT    NOT NULL,
            email      TEXT    NOT NULL UNIQUE,
            password   TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS revenue (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date        TEXT,
            description TEXT    NOT NULL,
            amount      REAL    NOT NULL CHECK(amount >= 0),
            category    TEXT    DEFAULT 'General',
            created_at  TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date        TEXT,
            description TEXT    NOT NULL,
            amount      REAL    NOT NULL CHECK(amount >= 0),
            category    TEXT    DEFAULT 'General',
            created_at  TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS clients (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            sector      TEXT,
            revenue     REAL    DEFAULT 0,
            status      TEXT    DEFAULT 'active' CHECK(status IN ('active','pending','inactive')),
            created_at  TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS suppliers (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            category    TEXT,
            contract    TEXT,
            rating      INTEGER DEFAULT 5 CHECK(rating BETWEEN 1 AND 5),
            created_at  TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS products (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            price       REAL    DEFAULT 0,
            units_sold  INTEGER DEFAULT 0,
            segment     TEXT,
            created_at  TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS projects (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            lead        TEXT,
            deadline    TEXT,
            progress    INTEGER DEFAULT 0 CHECK(progress BETWEEN 0 AND 100),
            status      TEXT    DEFAULT 'active' CHECK(status IN ('active','pending','inactive')),
            created_at  TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS kpis (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            current_val REAL    DEFAULT 0,
            target_val  REAL    DEFAULT 0,
            unit        TEXT    DEFAULT '',
            created_at  TIMESTAMP DEFAULT NOW()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


# ══════════════════════════════════════════════════════════════
#  USERS
# ══════════════════════════════════════════════════════════════

def create_user(name: str, email: str, password: str) -> dict | None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s) RETURNING id, name, email",
            (name, email, password)
        )
        user = cur.fetchone()
        conn.commit()
        cur.close()
        return dict(user) if user else None
    except Exception:
        conn.rollback()
        return None
    finally:
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, password FROM users WHERE email = %s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


# ══════════════════════════════════════════════════════════════
#  GENERIC CRUD
# ══════════════════════════════════════════════════════════════

ALLOWED_TABLES = {"revenue","expenses","clients","suppliers","products","projects","kpis"}

def fetch_all(table: str, user_id: int) -> list[dict]:
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Tabela inválida: {table}")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table} WHERE user_id = %s ORDER BY id DESC", (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()
    return rows


def insert_row(table: str, user_id: int, data: dict) -> int:
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Tabela inválida: {table}")
    data["user_id"] = user_id
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) RETURNING id",
        list(data.values())
    )
    last_id = cur.fetchone()["id"]
    conn.commit()
    cur.close(); conn.close()
    return last_id


def delete_row(table: str, row_id: int, user_id: int) -> bool:
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Tabela inválida: {table}")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE id = %s AND user_id = %s", (row_id, user_id))
    affected = cur.rowcount
    conn.commit()
    cur.close(); conn.close()
    return affected > 0


# ══════════════════════════════════════════════════════════════
#  ANALYTICAL QUERIES
# ══════════════════════════════════════════════════════════════

def summary_financials(user_id: int) -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COALESCE((SELECT SUM(amount) FROM revenue  WHERE user_id = %s), 0) AS total_revenue,
            COALESCE((SELECT SUM(amount) FROM expenses WHERE user_id = %s), 0) AS total_expenses
    """, (user_id, user_id))
    row = dict(cur.fetchone())
    cur.close(); conn.close()
    row["net_profit"] = row["total_revenue"] - row["total_expenses"]
    rev = row["total_revenue"]
    row["net_margin"] = round((row["net_profit"] / rev * 100), 2) if rev > 0 else 0
    return row


def revenue_by_category(user_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT category, SUM(amount) AS total, COUNT(*) AS entries, ROUND(AVG(amount)::numeric,2) AS avg_amount
        FROM revenue WHERE user_id = %s GROUP BY category ORDER BY total DESC
    """, (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()
    return rows


def expenses_by_category(user_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT category, SUM(amount) AS total, COUNT(*) AS entries, ROUND(AVG(amount)::numeric,2) AS avg_amount
        FROM expenses WHERE user_id = %s GROUP BY category ORDER BY total DESC
    """, (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()
    return rows


def revenue_monthly(user_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT SUBSTRING(date, 1, 7) AS month, SUM(amount) AS total
        FROM revenue WHERE user_id = %s AND date IS NOT NULL AND date != ''
        GROUP BY month ORDER BY month ASC
    """, (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()
    return rows


def expenses_monthly(user_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT SUBSTRING(date, 1, 7) AS month, SUM(amount) AS total
        FROM expenses WHERE user_id = %s AND date IS NOT NULL AND date != ''
        GROUP BY month ORDER BY month ASC
    """, (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()
    return rows


def top_clients(user_id: int, limit: int = 5) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, sector, revenue, status FROM clients
        WHERE user_id = %s ORDER BY revenue DESC LIMIT %s
    """, (user_id, limit))
    rows = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()
    return rows


def kpi_summary(user_id: int) -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN current_val >= target_val THEN 1 ELSE 0 END) AS on_target,
            SUM(CASE WHEN current_val <  target_val THEN 1 ELSE 0 END) AS below_target
        FROM kpis WHERE user_id = %s
    """, (user_id,))
    result = dict(cur.fetchone())
    cur.close(); conn.close()
    total = result["total"] or 0
    on_t  = result["on_target"] or 0
    result["hit_rate"] = round(on_t / total * 100, 1) if total > 0 else 0
    return result
