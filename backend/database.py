"""
NEXUS Analytics — database.py
-------------------------------
Camada de dados: PostgreSQL (Neon) via pg8000.
Compatível com Python 3.14+
"""

import os
import pg8000.native
import streamlit as st
from urllib.parse import urlparse


def get_connection():
    """
    Retorna uma conexão PostgreSQL via pg8000.
    Lê a DATABASE_URL dos secrets do Streamlit Cloud.
    """
    try:
        db_url = st.secrets["DATABASE_URL"]
    except Exception:
        db_url = os.environ.get("DATABASE_URL", "")

    parsed = urlparse(db_url)
    conn = pg8000.native.Connection(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip("/"),
        user=parsed.username,
        password=parsed.password,
        ssl_context=True,
    )
    return conn


def run(conn, sql, params=None):
    """Executa uma query e retorna os resultados como lista de dicts."""
    try:
        if params:
            rows = conn.run(sql, *params)
        else:
            rows = conn.run(sql)
        cols = [c["name"] for c in conn.columns]
        return [dict(zip(cols, row)) for row in rows]
    except Exception:
        return []


def run_one(conn, sql, params=None):
    results = run(conn, sql, params)
    return results[0] if results else None


def init_db():
    """Cria todas as tabelas caso não existam."""
    conn = get_connection()

    statements = [
        """CREATE TABLE IF NOT EXISTS users (
            id         SERIAL PRIMARY KEY,
            name       TEXT    NOT NULL,
            email      TEXT    NOT NULL UNIQUE,
            password   TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS revenue (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date        TEXT,
            description TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            category    TEXT    DEFAULT 'General',
            created_at  TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS expenses (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date        TEXT,
            description TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            category    TEXT    DEFAULT 'General',
            created_at  TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS clients (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            sector      TEXT,
            revenue     REAL    DEFAULT 0,
            status      TEXT    DEFAULT 'active',
            created_at  TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS suppliers (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            category    TEXT,
            contract    TEXT,
            rating      INTEGER DEFAULT 5,
            created_at  TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS products (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            price       REAL    DEFAULT 0,
            units_sold  INTEGER DEFAULT 0,
            segment     TEXT,
            created_at  TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS projects (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            lead        TEXT,
            deadline    TEXT,
            progress    INTEGER DEFAULT 0,
            status      TEXT    DEFAULT 'active',
            created_at  TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS kpis (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            current_val REAL    DEFAULT 0,
            target_val  REAL    DEFAULT 0,
            unit        TEXT    DEFAULT '',
            created_at  TIMESTAMP DEFAULT NOW()
        )""",
    ]

    for sql in statements:
        try:
            conn.run(sql)
        except Exception:
            pass

    conn.close()


# ══════════════════════════════════════════════════════════════
#  USERS
# ══════════════════════════════════════════════════════════════

def create_user(name: str, email: str, password: str) -> dict | None:
    conn = get_connection()
    try:
        rows = conn.run(
            "INSERT INTO users (name, email, password) VALUES (:n, :e, :p) RETURNING id, name, email",
            n=name, e=email, p=password
        )
        cols = [c["name"] for c in conn.columns]
        user = dict(zip(cols, rows[0])) if rows else None
        conn.close()
        return user
    except Exception:
        conn.close()
        return None


def get_user_by_email(email: str) -> dict | None:
    conn = get_connection()
    rows = conn.run("SELECT id, name, email, password FROM users WHERE email = :e", e=email)
    cols = [c["name"] for c in conn.columns]
    conn.close()
    return dict(zip(cols, rows[0])) if rows else None


# ══════════════════════════════════════════════════════════════
#  GENERIC CRUD
# ══════════════════════════════════════════════════════════════

ALLOWED_TABLES = {"revenue","expenses","clients","suppliers","products","projects","kpis"}

def fetch_all(table: str, user_id: int) -> list[dict]:
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Tabela inválida: {table}")
    conn = get_connection()
    rows = conn.run(f"SELECT * FROM {table} WHERE user_id = :uid ORDER BY id DESC", uid=user_id)
    cols = [c["name"] for c in conn.columns]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


def insert_row(table: str, user_id: int, data: dict) -> int:
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Tabela inválida: {table}")
    data["user_id"] = user_id
    cols = ", ".join(data.keys())
    placeholders = ", ".join([f":{k}" for k in data.keys()])
    conn = get_connection()
    rows = conn.run(
        f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) RETURNING id",
        **data
    )
    last_id = rows[0][0] if rows else None
    conn.close()
    return last_id


def delete_row(table: str, row_id: int, user_id: int) -> bool:
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Tabela inválida: {table}")
    conn = get_connection()
    conn.run(f"DELETE FROM {table} WHERE id = :rid AND user_id = :uid", rid=row_id, uid=user_id)
    conn.close()
    return True


# ══════════════════════════════════════════════════════════════
#  ANALYTICAL QUERIES
# ══════════════════════════════════════════════════════════════

def summary_financials(user_id: int) -> dict:
    conn = get_connection()
    rows = conn.run("""
        SELECT
            COALESCE((SELECT SUM(amount) FROM revenue  WHERE user_id = :uid), 0) AS total_revenue,
            COALESCE((SELECT SUM(amount) FROM expenses WHERE user_id = :uid), 0) AS total_expenses
    """, uid=user_id)
    cols = [c["name"] for c in conn.columns]
    conn.close()
    row = dict(zip(cols, rows[0]))
    row["net_profit"] = row["total_revenue"] - row["total_expenses"]
    rev = row["total_revenue"]
    row["net_margin"] = round((row["net_profit"] / rev * 100), 2) if rev > 0 else 0
    return row


def revenue_by_category(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.run("""
        SELECT category, SUM(amount) AS total, COUNT(*) AS entries
        FROM revenue WHERE user_id = :uid GROUP BY category ORDER BY total DESC
    """, uid=user_id)
    cols = [c["name"] for c in conn.columns]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


def expenses_by_category(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.run("""
        SELECT category, SUM(amount) AS total, COUNT(*) AS entries
        FROM expenses WHERE user_id = :uid GROUP BY category ORDER BY total DESC
    """, uid=user_id)
    cols = [c["name"] for c in conn.columns]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


def revenue_monthly(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.run("""
        SELECT SUBSTRING(date, 1, 7) AS month, SUM(amount) AS total
        FROM revenue WHERE user_id = :uid AND date IS NOT NULL AND date != ''
        GROUP BY month ORDER BY month ASC
    """, uid=user_id)
    cols = [c["name"] for c in conn.columns]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


def expenses_monthly(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.run("""
        SELECT SUBSTRING(date, 1, 7) AS month, SUM(amount) AS total
        FROM expenses WHERE user_id = :uid AND date IS NOT NULL AND date != ''
        GROUP BY month ORDER BY month ASC
    """, uid=user_id)
    cols = [c["name"] for c in conn.columns]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


def top_clients(user_id: int, limit: int = 5) -> list[dict]:
    conn = get_connection()
    rows = conn.run("""
        SELECT name, sector, revenue, status FROM clients
        WHERE user_id = :uid ORDER BY revenue DESC LIMIT :lim
    """, uid=user_id, lim=limit)
    cols = [c["name"] for c in conn.columns]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


def kpi_summary(user_id: int) -> dict:
    conn = get_connection()
    rows = conn.run("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN current_val >= target_val THEN 1 ELSE 0 END) AS on_target,
            SUM(CASE WHEN current_val <  target_val THEN 1 ELSE 0 END) AS below_target
        FROM kpis WHERE user_id = :uid
    """, uid=user_id)
    cols = [c["name"] for c in conn.columns]
    conn.close()
    result = dict(zip(cols, rows[0]))
    total = result["total"] or 0
    on_t  = result["on_target"] or 0
    result["hit_rate"] = round(on_t / total * 100, 1) if total > 0 else 0
    return result