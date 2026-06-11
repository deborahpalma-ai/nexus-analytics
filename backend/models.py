"""
NEXUS Analytics — models.py
-----------------------------
Camada analítica: Pandas para cálculo de KPIs,
margens, tendências e indicadores de negócio.
Cada função recebe listas de dicts (do banco) e
retorna DataFrames ou dicts prontos para visualização.
"""

import pandas as pd
import numpy as np
from typing import Optional


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def to_df(records: list[dict]) -> pd.DataFrame:
    """Converte lista de dicts para DataFrame com tipos corretos."""
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    # Converte colunas de data
    for col in ["date", "created_at", "deadline", "contract"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    # Converte colunas numéricas
    for col in ["amount", "revenue", "price", "current_val", "target_val"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in ["units_sold", "progress", "rating"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def fmt_currency(value: float) -> str:
    """Formata valor como moeda legível."""
    if abs(value) >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:,.2f}"


# ══════════════════════════════════════════════════════════════
#  FINANCIAL KPIs  (Pandas)
# ══════════════════════════════════════════════════════════════

def calc_financial_kpis(revenue_records: list, expense_records: list) -> dict:
    """
    Calcula KPIs financeiros principais usando Pandas.
    Demonstra: agregações, cálculo de margens, variações.
    """
    df_rev = to_df(revenue_records)
    df_exp = to_df(expense_records)

    total_rev = df_rev["amount"].sum() if not df_rev.empty else 0.0
    total_exp = df_exp["amount"].sum() if not df_exp.empty else 0.0
    net_profit = total_rev - total_exp
    gross_margin = (net_profit / total_rev * 100) if total_rev > 0 else 0.0
    cost_ratio   = (total_exp / total_rev * 100) if total_rev > 0 else 0.0

    avg_rev = df_rev["amount"].mean() if not df_rev.empty else 0.0
    avg_exp = df_exp["amount"].mean() if not df_exp.empty else 0.0
    median_rev = df_rev["amount"].median() if not df_rev.empty else 0.0

    return {
        "total_revenue":  round(total_rev, 2),
        "total_expenses": round(total_exp, 2),
        "net_profit":     round(net_profit, 2),
        "gross_margin":   round(gross_margin, 2),
        "cost_ratio":     round(cost_ratio, 2),
        "avg_revenue":    round(avg_rev, 2),
        "avg_expense":    round(avg_exp, 2),
        "median_revenue": round(median_rev, 2),
        "revenue_count":  len(df_rev),
        "expense_count":  len(df_exp),
    }


def monthly_evolution(revenue_records: list, expense_records: list) -> pd.DataFrame:
    """
    Evolução mensal de receita, despesa e lucro.
    Demonstra: resample/groupby, merge, fillna, cálculo de colunas derivadas.
    """
    df_rev = to_df(revenue_records)
    df_exp = to_df(expense_records)

    def monthly_sum(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
        if df.empty or "date" not in df.columns:
            return pd.DataFrame(columns=["month", col_name])
        df = df.dropna(subset=["date"])
        df["month"] = df["date"].dt.to_period("M").astype(str)
        return df.groupby("month")["amount"].sum().reset_index()\
                 .rename(columns={"amount": col_name})

    rev_m = monthly_sum(df_rev, "revenue")
    exp_m = monthly_sum(df_exp, "expenses")

    if rev_m.empty and exp_m.empty:
        return pd.DataFrame(columns=["month", "revenue", "expenses", "profit", "margin"])

    merged = pd.merge(rev_m, exp_m, on="month", how="outer").fillna(0)
    merged = merged.sort_values("month").reset_index(drop=True)
    merged["profit"] = merged["revenue"] - merged["expenses"]
    merged["margin"] = np.where(
        merged["revenue"] > 0,
        (merged["profit"] / merged["revenue"] * 100).round(2),
        0.0
    )
    return merged


def revenue_growth(revenue_records: list) -> pd.DataFrame:
    """
    Calcula crescimento percentual mês a mês.
    Demonstra: pct_change(), diff(), janela rolante.
    """
    df = to_df(revenue_records)
    if df.empty or "date" not in df.columns:
        return pd.DataFrame()

    df = df.dropna(subset=["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    monthly = df.groupby("month")["amount"].sum().reset_index()
    monthly = monthly.sort_values("month").reset_index(drop=True)
    monthly["growth_pct"]   = monthly["amount"].pct_change() * 100
    monthly["growth_abs"]   = monthly["amount"].diff()
    monthly["rolling_3m"]   = monthly["amount"].rolling(3).mean()
    monthly["cumulative"]   = monthly["amount"].cumsum()
    return monthly.round(2)


def expense_breakdown(expense_records: list) -> pd.DataFrame:
    """
    Breakdown de despesas por categoria.
    Demonstra: groupby, transform para percentual.
    """
    df = to_df(expense_records)
    if df.empty:
        return pd.DataFrame()

    grouped = df.groupby("category")["amount"].agg(
        total="sum",
        count="count",
        average="mean"
    ).reset_index()

    grouped["pct_of_total"] = (grouped["total"] / grouped["total"].sum() * 100).round(2)
    grouped = grouped.sort_values("total", ascending=False).reset_index(drop=True)
    grouped["total"]   = grouped["total"].round(2)
    grouped["average"] = grouped["average"].round(2)
    return grouped


# ══════════════════════════════════════════════════════════════
#  CLIENT ANALYTICS  (Pandas)
# ══════════════════════════════════════════════════════════════

def client_analytics(client_records: list) -> dict:
    """
    Análise do portfólio de clientes.
    Demonstra: value_counts, describe, segmentação por status.
    """
    df = to_df(client_records)
    if df.empty:
        return {
            "total": 0, "active": 0, "pending": 0, "inactive": 0,
            "total_revenue": 0, "avg_revenue": 0, "top_sector": "—"
        }

    status_counts = df["status"].value_counts().to_dict()
    sector_revenue = df.groupby("sector")["revenue"].sum()
    top_sector = sector_revenue.idxmax() if not sector_revenue.empty else "—"

    return {
        "total":         len(df),
        "active":        status_counts.get("active", 0),
        "pending":       status_counts.get("pending", 0),
        "inactive":      status_counts.get("inactive", 0),
        "total_revenue": round(df["revenue"].sum(), 2),
        "avg_revenue":   round(df["revenue"].mean(), 2),
        "max_revenue":   round(df["revenue"].max(), 2),
        "top_sector":    top_sector,
    }


def client_revenue_by_sector(client_records: list) -> pd.DataFrame:
    """Receita agrupada por setor para gráfico."""
    df = to_df(client_records)
    if df.empty:
        return pd.DataFrame()
    return df.groupby("sector")["revenue"].sum()\
             .reset_index()\
             .sort_values("revenue", ascending=False)\
             .round(2)


# ══════════════════════════════════════════════════════════════
#  PRODUCT ANALYTICS  (Pandas)
# ══════════════════════════════════════════════════════════════

def product_analytics(product_records: list) -> pd.DataFrame:
    """
    Calcula receita total por produto (price × units_sold).
    Demonstra: colunas calculadas, ranking, normalização.
    """
    df = to_df(product_records)
    if df.empty:
        return pd.DataFrame()

    df["total_revenue"] = (df["price"] * df["units_sold"]).round(2)
    df["revenue_rank"]  = df["total_revenue"].rank(ascending=False, method="dense").astype(int)

    total = df["total_revenue"].sum()
    df["pct_of_total"] = np.where(
        total > 0,
        (df["total_revenue"] / total * 100).round(2),
        0.0
    )
    return df.sort_values("total_revenue", ascending=False).reset_index(drop=True)


# ══════════════════════════════════════════════════════════════
#  PROJECT ANALYTICS  (Pandas)
# ══════════════════════════════════════════════════════════════

def project_analytics(project_records: list) -> dict:
    """
    Análise do pipeline de projetos.
    Demonstra: filtragem booleana, médias condicionais.
    """
    df = to_df(project_records)
    if df.empty:
        return {
            "total": 0, "active": 0, "pending": 0, "inactive": 0,
            "avg_progress": 0, "on_track": 0, "at_risk": 0
        }

    status_counts = df["status"].value_counts().to_dict()
    avg_prog = df["progress"].mean()
    on_track = int((df["progress"] >= 70).sum())
    at_risk   = int((df["progress"] < 30).sum())

    return {
        "total":        len(df),
        "active":       status_counts.get("active", 0),
        "pending":      status_counts.get("pending", 0),
        "inactive":     status_counts.get("inactive", 0),
        "avg_progress": round(float(avg_prog), 1),
        "on_track":     on_track,
        "at_risk":      at_risk,
    }


# ══════════════════════════════════════════════════════════════
#  KPI ANALYTICS  (Pandas)
# ══════════════════════════════════════════════════════════════

def kpi_analytics(kpi_records: list) -> pd.DataFrame:
    """
    Processa KPIs: delta, status, distância do target.
    Demonstra: apply, np.where, colunas condicionais.
    """
    df = to_df(kpi_records)
    if df.empty:
        return pd.DataFrame()

    df["delta"]        = (df["current_val"] - df["target_val"]).round(2)
    df["delta_pct"]    = np.where(
        df["target_val"] != 0,
        ((df["current_val"] - df["target_val"]) / df["target_val"].abs() * 100).round(2),
        0.0
    )
    df["on_target"]    = df["current_val"] >= df["target_val"]
    df["status_label"] = np.where(df["on_target"], "✅ On Target", "⚠️ Below Target")
    df["achievement"]  = np.where(
        df["target_val"] != 0,
        (df["current_val"] / df["target_val"].abs() * 100).round(1),
        0.0
    )
    return df


# ══════════════════════════════════════════════════════════════
#  EXECUTIVE SUMMARY  (combina tudo)
# ══════════════════════════════════════════════════════════════

def executive_summary(
    revenue_records: list,
    expense_records: list,
    client_records: list,
    project_records: list,
    kpi_records: list
) -> dict:
    """
    Resumo executivo completo — combina todas as análises.
    Este é o método chamado pelo Dashboard principal.
    """
    fin   = calc_financial_kpis(revenue_records, expense_records)
    cli   = client_analytics(client_records)
    proj  = project_analytics(project_records)
    df_kpi = kpi_analytics(kpi_records)

    kpi_on_target = int(df_kpi["on_target"].sum()) if not df_kpi.empty else 0
    kpi_total     = len(df_kpi)

    return {
        "financials":     fin,
        "clients":        cli,
        "projects":       proj,
        "kpi_on_target":  kpi_on_target,
        "kpi_total":      kpi_total,
        "kpi_hit_rate":   round(kpi_on_target / kpi_total * 100, 1) if kpi_total > 0 else 0,
    }
