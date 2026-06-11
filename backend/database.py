"""
NEXUS Analytics — database.py
-------------------------------
Camada de dados: SQLite via SQLAlchemy core.
Todas as queries são SQL puro para demonstrar domínio da linguagem.
"""

import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "nexus.db"


def get_connection():
    """Retorna uma conexão SQLite com row_factory para dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Cria todas as tabelas do banco de dados caso não existam.
    SQL explícito para demonstrar modelagem relacional.
    """
    conn = get_connection()
    cur = conn.cursor()

    # ── USERS ─────────────────────────────────────────────
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        -- ── REVENUE ───────────────────────────────────────
        CREATE TABLE IF NOT EXISTS revenue (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date        TEXT,
            description TEXT    NOT NULL,
            amount      REAL    NOT NULL CHECK(amount >= 0),
            category    TEXT    DEFAULT 'General',
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        -- ── EXPENSES ──────────────────────────────────────
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date        TEXT,
            description TEXT    NOT NULL,
            amount      REAL    NOT NULL CHECK(amount >= 0),
            category    TEXT    DEFAULT 'General',
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        -- ── CLIENTS ───────────────────────────────────────
        CREATE TABLE IF NOT EXISTS clients (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            sector      TEXT,
            revenue     REAL    DEFAULT 0,
            status      TEXT    DEFAULT 'active'
                            CHECK(status IN ('active','pending','inactive')),
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        -- ── SUPPLIERS ─────────────────────────────────────
        CREATE TABLE IF NOT EXISTS suppliers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            category    TEXT,
            contract    TEXT,
            rating      INTEGER DEFAULT 5 CHECK(rating BETWEEN 1 AND 5),
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        -- ── PRODUCTS ──────────────────────────────────────
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            price       REAL    DEFAULT 0,
            units_sold  INTEGER DEFAULT 0,
            segment     TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        -- ── PROJECTS ──────────────────────────────────────
        CREATE TABLE IF NOT EXISTS projects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            lead        TEXT,
            deadline    TEXT,
            progress    INTEGER DEFAULT 0 CHECK(progress BETWEEN 0 AND 100),
            status      TEXT    DEFAULT 'active'
                            CHECK(status IN ('active','pending','inactive')),
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        -- ── KPIs ──────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS kpis (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            current_val REAL    DEFAULT 0,
            target_val  REAL    DEFAULT 0,
            unit        TEXT    DEFAULT '',
            created_at  TEXT    DEFAULT (datetime('now'))
        );
    """)

    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════
#  USERS
# ══════════════════════════════════════════════════════════════

def create_user(name: str, email: str, password: str) -> dict | None:
    """Insere novo usuário. Retorna o usuário criado ou None se email duplicado."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )
        conn.commit()
        user = conn.execute(
            "SELECT id, name, email FROM users WHERE email = ?", (email,)
        ).fetchone()
        return dict(user) if user else None
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    """Busca usuário pelo e-mail."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, name, email, password FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ══════════════════════════════════════════════════════════════
#  GENERIC CRUD  (revenue, expenses, clients, suppliers,
#                 products, projects, kpis)
# ══════════════════════════════════════════════════════════════

def fetch_all(table: str, user_id: int) -> list[dict]:
    """SELECT * para a tabela e usuário informados."""
    allowed = {"revenue","expenses","clients","suppliers","products","projects","kpis"}
    if table not in allowed:
        raise ValueError(f"Tabela inválida: {table}")
    conn = get_connection()
    rows = conn.execute(
        f"SELECT * FROM {table} WHERE user_id = ? ORDER BY id DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_row(table: str, user_id: int, data: dict) -> int:
    """INSERT genérico. Retorna o id do registro inserido."""
    allowed = {"revenue","expenses","clients","suppliers","products","projects","kpis"}
    if table not in allowed:
        raise ValueError(f"Tabela inválida: {table}")
    data["user_id"] = user_id
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    conn = get_connection()
    cur = conn.execute(
        f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
        list(data.values())
    )
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def delete_row(table: str, row_id: int, user_id: int) -> bool:
    """DELETE seguro: só apaga se o registro pertencer ao usuário."""
    allowed = {"revenue","expenses","clients","suppliers","products","projects","kpis"}
    if table not in allowed:
        raise ValueError(f"Tabela inválida: {table}")
    conn = get_connection()
    cur = conn.execute(
        f"DELETE FROM {table} WHERE id = ? AND user_id = ?",
        (row_id, user_id)
    )
    conn.commit()
    affected = cur.rowcount
    conn.close()
    return affected > 0


# ══════════════════════════════════════════════════════════════
#  ANALYTICAL QUERIES  (SQL puro para KPIs do dashboard)
# ══════════════════════════════════════════════════════════════

def summary_financials(user_id: int) -> dict:
    """
    Retorna totais financeiros consolidados via SQL.
    Demonstra uso de SUM, subquery e COALESCE.
    """
    conn = get_connection()
    row = conn.execute("""
        SELECT
            COALESCE((SELECT SUM(amount) FROM revenue  WHERE user_id = :uid), 0) AS total_revenue,
            COALESCE((SELECT SUM(amount) FROM expenses WHERE user_id = :uid), 0) AS total_expenses,
            (
                COALESCE((SELECT SUM(amount) FROM revenue  WHERE user_id = :uid), 0) -
                COALESCE((SELECT SUM(amount) FROM expenses WHERE user_id = :uid), 0)
            ) AS net_profit
    """, {"uid": user_id}).fetchone()
    conn.close()
    result = dict(row)
    rev = result["total_revenue"]
    result["net_margin"] = round((result["net_profit"] / rev * 100), 2) if rev > 0 else 0
    return result


def revenue_by_category(user_id: int) -> list[dict]:
    """GROUP BY categoria para gráfico de pizza."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            category,
            SUM(amount)   AS total,
            COUNT(*)      AS entries,
            ROUND(AVG(amount), 2) AS avg_amount
        FROM revenue
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def expenses_by_category(user_id: int) -> list[dict]:
    """GROUP BY categoria de despesas."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            category,
            SUM(amount)   AS total,
            COUNT(*)      AS entries,
            ROUND(AVG(amount), 2) AS avg_amount
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def revenue_monthly(user_id: int) -> list[dict]:
    """Agrega receita por mês (YYYY-MM) para gráfico de linha."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            SUBSTR(date, 1, 7)  AS month,
            SUM(amount)         AS total
        FROM revenue
        WHERE user_id = ? AND date IS NOT NULL AND date != ''
        GROUP BY month
        ORDER BY month ASC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def expenses_monthly(user_id: int) -> list[dict]:
    """Agrega despesas por mês."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            SUBSTR(date, 1, 7)  AS month,
            SUM(amount)         AS total
        FROM expenses
        WHERE user_id = ? AND date IS NOT NULL AND date != ''
        GROUP BY month
        ORDER BY month ASC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def top_clients(user_id: int, limit: int = 5) -> list[dict]:
    """Top clientes por receita usando ORDER BY + LIMIT."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT name, sector, revenue, status
        FROM clients
        WHERE user_id = ?
        ORDER BY revenue DESC
        LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def kpi_summary(user_id: int) -> dict:
    """
    Resumo de KPIs: on target, below target, hit rate.
    Demonstra CASE WHEN em SQL.
    """
    conn = get_connection()
    row = conn.execute("""
        SELECT
            COUNT(*)  AS total,
            SUM(CASE WHEN current_val >= target_val THEN 1 ELSE 0 END) AS on_target,
            SUM(CASE WHEN current_val <  target_val THEN 1 ELSE 0 END) AS below_target
        FROM kpis
        WHERE user_id = ?
    """, (user_id,)).fetchone()
    conn.close()
    result = dict(row)
    total = result["total"] or 0
    on_t  = result["on_target"] or 0
    result["hit_rate"] = round(on_t / total * 100, 1) if total > 0 else 0
    return result
