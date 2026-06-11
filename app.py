"""
NEXUS Analytics — app.py
--------------------------
Portal interativo Streamlit.
Stack: Python · Pandas · SQLite/SQL · Plotly · Streamlit
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

from backend.database import (
    init_db, fetch_all, insert_row, delete_row,
    summary_financials, revenue_by_category, expenses_by_category,
    revenue_monthly, expenses_monthly, top_clients, kpi_summary
)
from backend.models import (
    calc_financial_kpis, monthly_evolution, revenue_growth,
    expense_breakdown, client_analytics, client_revenue_by_sector,
    product_analytics, project_analytics, kpi_analytics,
    executive_summary, fmt_currency, to_df
)
from backend.auth import register, login

st.set_page_config(
    page_title="NEXUS Analytics",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ══════════════════════════════════════════════════════════════
#  CURRENCY
# ══════════════════════════════════════════════════════════════

CURRENCIES = {
    "USD": {"symbol": "$",  "name": "US Dollar"},
    "EUR": {"symbol": "€",  "name": "Euro"},
    "BRL": {"symbol": "R$", "name": "Real"},
}

def get_symbol() -> str:
    return CURRENCIES[st.session_state.get("currency", "USD")]["symbol"]

def fmt(value: float) -> str:
    sym = get_symbol()
    if abs(value) >= 1_000_000:
        return f"{sym}{value/1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{sym}{value/1_000:.1f}K"
    return f"{sym}{value:,.2f}"

# ══════════════════════════════════════════════════════════════
#  TRANSLATIONS
# ══════════════════════════════════════════════════════════════

TRANSLATIONS = {
    "en": {
        "tagline": "Business Performance & Financial Analytics",
        "login": "Login", "register": "Register",
        "name": "Full Name", "email": "Email", "password": "Password",
        "login_btn": "Access Platform", "register_btn": "Create Account",
        "logout": "Logout",
        "dashboard": "Dashboard", "revenue": "Revenue", "expenses": "Expenses",
        "clients": "Clients", "suppliers": "Suppliers", "products": "Products",
        "projects": "Projects", "kpis": "KPI Tracker",
        "total_revenue": "Total Revenue", "total_expenses": "Total Expenses",
        "net_profit": "Net Profit", "net_margin": "Net Margin",
        "active_clients": "Active Clients", "active_projects": "Active Projects",
        "add": "Add", "delete": "Delete",
        "no_data": "No records yet. Use the form above to add your first entry.",
        "date": "Date", "description": "Description", "amount": "Amount",
        "category": "Category", "status": "Status", "sector": "Sector",
        "active": "Active", "pending": "Pending", "inactive": "Inactive",
        "lead": "Project Lead", "deadline": "Deadline", "progress": "Progress (%)",
        "price": "Price", "units_sold": "Units Sold", "segment": "Segment",
        "supplier": "Supplier", "contract": "Contract Until", "rating": "Rating",
        "indicator": "Indicator", "current": "Current", "target": "Target", "unit": "Unit",
        "welcome": "Welcome back",
        "evolution": "Monthly Evolution", "by_category": "By Category", "by_sector": "By Sector",
        "top_clients": "Top Clients", "hit_rate": "KPI Hit Rate", "on_target": "On Target",
        "currency": "Currency", "language": "Language",
        "select_delete": "Select item to delete",
        "confirm_delete": "Confirm Delete",
        "deleted_ok": "Deleted successfully!",
        # fully translated labels
        "avg_entry": "Avg / Entry", "entries": "Entries",
        "total_suppliers": "Total Suppliers", "avg_rating": "Avg Rating",
        "total_skus": "Total SKUs", "product_revenue": "Product Revenue",
        "on_track": "On Track (≥70%)", "at_risk": "At Risk (<30%)",
        "below_target": "Below Target", "cost_ratio": "Cost Ratio",
        "avg_progress": "Avg Progress", "revenue_share": "Revenue Share",
        "total": "Total", "top_sector": "Top Sector",
        "kpi_summary": "KPI Summary", "kpis_on_target": "on target",
        "of": "out of",
        "strategic_indicators": "Strategic performance indicators.",
        "add_revenue": "Add Revenue", "add_expenses": "Add Expenses",
        "add_clients": "Add Clients", "add_suppliers": "Add Suppliers",
        "add_products": "Add Products", "add_projects": "Add Projects",
        "add_kpi": "Add KPI",
        "fill_desc_amount": "Fill in description and amount.",
        "name_required": "Name is required.",
        "active_label": "● Active", "pending_label": "◌ Pending", "inactive_label": "○ Inactive",
        "ytd": "YTD",
    },
    "pt": {
        "tagline": "Análise de Desempenho Empresarial & Financeiro",
        "login": "Entrar", "register": "Cadastrar",
        "name": "Nome Completo", "email": "E-mail", "password": "Senha",
        "login_btn": "Acessar Plataforma", "register_btn": "Criar Conta",
        "logout": "Sair",
        "dashboard": "Dashboard", "revenue": "Receitas", "expenses": "Despesas",
        "clients": "Clientes", "suppliers": "Fornecedores", "products": "Produtos",
        "projects": "Projetos", "kpis": "Rastreador de KPIs",
        "total_revenue": "Receita Total", "total_expenses": "Despesas Totais",
        "net_profit": "Lucro Líquido", "net_margin": "Margem Líquida",
        "active_clients": "Clientes Ativos", "active_projects": "Projetos Ativos",
        "add": "Adicionar", "delete": "Excluir",
        "no_data": "Nenhum registro ainda. Use o formulário acima para adicionar.",
        "date": "Data", "description": "Descrição", "amount": "Valor",
        "category": "Categoria", "status": "Status", "sector": "Setor",
        "active": "Ativo", "pending": "Pendente", "inactive": "Inativo",
        "lead": "Responsável", "deadline": "Prazo", "progress": "Progresso (%)",
        "price": "Preço", "units_sold": "Unidades Vendidas", "segment": "Segmento",
        "supplier": "Fornecedor", "contract": "Contrato até", "rating": "Avaliação",
        "indicator": "Indicador", "current": "Atual", "target": "Meta", "unit": "Unidade",
        "welcome": "Bem-vindo(a)",
        "evolution": "Evolução Mensal", "by_category": "Por Categoria", "by_sector": "Por Setor",
        "top_clients": "Principais Clientes", "hit_rate": "Taxa de KPIs", "on_target": "Na Meta",
        "currency": "Moeda", "language": "Idioma",
        "select_delete": "Selecione o item para excluir",
        "confirm_delete": "Confirmar Exclusão",
        "deleted_ok": "Excluído com sucesso!",
        "avg_entry": "Média / Entrada", "entries": "Entradas",
        "total_suppliers": "Total de Fornecedores", "avg_rating": "Avaliação Média",
        "total_skus": "Total de Produtos", "product_revenue": "Receita de Produtos",
        "on_track": "No Prazo (≥70%)", "at_risk": "Em Risco (<30%)",
        "below_target": "Abaixo da Meta", "cost_ratio": "Proporção de Custos",
        "avg_progress": "Progresso Médio", "revenue_share": "Participação na Receita",
        "total": "Total", "top_sector": "Setor Principal",
        "kpi_summary": "Resumo de KPIs", "kpis_on_target": "na meta",
        "of": "de",
        "strategic_indicators": "Indicadores estratégicos de desempenho.",
        "add_revenue": "Adicionar Receita", "add_expenses": "Adicionar Despesa",
        "add_clients": "Adicionar Cliente", "add_suppliers": "Adicionar Fornecedor",
        "add_products": "Adicionar Produto", "add_projects": "Adicionar Projeto",
        "add_kpi": "Adicionar KPI",
        "fill_desc_amount": "Preencha a descrição e o valor.",
        "name_required": "O nome é obrigatório.",
        "active_label": "● Ativo", "pending_label": "◌ Pendente", "inactive_label": "○ Inativo",
        "ytd": "Ano atual",
    },
    "es": {
        "tagline": "Análisis de Rendimiento Empresarial y Financiero",
        "login": "Iniciar sesión", "register": "Registrarse",
        "name": "Nombre completo", "email": "Correo", "password": "Contraseña",
        "login_btn": "Acceder a la Plataforma", "register_btn": "Crear Cuenta",
        "logout": "Salir",
        "dashboard": "Dashboard", "revenue": "Ingresos", "expenses": "Gastos",
        "clients": "Clientes", "suppliers": "Proveedores", "products": "Productos",
        "projects": "Proyectos", "kpis": "Rastreador KPI",
        "total_revenue": "Ingresos Totales", "total_expenses": "Gastos Totales",
        "net_profit": "Utilidad Neta", "net_margin": "Margen Neto",
        "active_clients": "Clientes Activos", "active_projects": "Proyectos Activos",
        "add": "Agregar", "delete": "Eliminar",
        "no_data": "Sin registros. Use el formulario arriba para agregar.",
        "date": "Fecha", "description": "Descripción", "amount": "Monto",
        "category": "Categoría", "status": "Estado", "sector": "Sector",
        "active": "Activo", "pending": "Pendiente", "inactive": "Inactivo",
        "lead": "Responsable", "deadline": "Fecha límite", "progress": "Progreso (%)",
        "price": "Precio", "units_sold": "Unidades vendidas", "segment": "Segmento",
        "supplier": "Proveedor", "contract": "Contrato hasta", "rating": "Calificación",
        "indicator": "Indicador", "current": "Actual", "target": "Objetivo", "unit": "Unidad",
        "welcome": "Bienvenido(a)",
        "evolution": "Evolución Mensual", "by_category": "Por Categoría", "by_sector": "Por Sector",
        "top_clients": "Principales Clientes", "hit_rate": "Tasa de KPIs", "on_target": "En Objetivo",
        "currency": "Moneda", "language": "Idioma",
        "select_delete": "Seleccione el elemento a eliminar",
        "confirm_delete": "Confirmar eliminación",
        "deleted_ok": "¡Eliminado con éxito!",
        "avg_entry": "Promedio / Entrada", "entries": "Entradas",
        "total_suppliers": "Total de Proveedores", "avg_rating": "Calificación Promedio",
        "total_skus": "Total de Productos", "product_revenue": "Ingresos de Productos",
        "on_track": "En Plazo (≥70%)", "at_risk": "En Riesgo (<30%)",
        "below_target": "Por debajo del objetivo", "cost_ratio": "Proporción de Costos",
        "avg_progress": "Progreso Promedio", "revenue_share": "Participación en Ingresos",
        "total": "Total", "top_sector": "Sector Principal",
        "kpi_summary": "Resumen de KPIs", "kpis_on_target": "en objetivo",
        "of": "de",
        "strategic_indicators": "Indicadores estratégicos de rendimiento.",
        "add_revenue": "Agregar Ingreso", "add_expenses": "Agregar Gasto",
        "add_clients": "Agregar Cliente", "add_suppliers": "Agregar Proveedor",
        "add_products": "Agregar Producto", "add_projects": "Agregar Proyecto",
        "add_kpi": "Agregar KPI",
        "fill_desc_amount": "Complete la descripción y el monto.",
        "name_required": "El nombre es obligatorio.",
        "active_label": "● Activo", "pending_label": "◌ Pendiente", "inactive_label": "○ Inactivo",
        "ytd": "Año actual",
    },
}

def t(key: str) -> str:
    lang = st.session_state.get("lang", "en")
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)

# ══════════════════════════════════════════════════════════════
#  THEME / CSS
# ══════════════════════════════════════════════════════════════

GOLD    = "#C9A84C"
RUBY    = "#E84855"
EMERALD = "#2ECC8B"
SAPPH   = "#4A90E2"
AMBER   = "#F5A623"
PLAT    = "#E8E8F0"
PLAT3   = "#7878A0"

def get_plotly_layout():
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=PLAT3, family="DM Sans, sans-serif", size=12),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", color=PLAT3),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", color=PLAT3),
    )

def apply_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #0A0A0F; color: #E8E8F0; }
    .block-container { padding: 1.5rem 2rem; max-width: 1400px; }
    [data-testid="stSidebar"] { background: #12121A !important; border-right: 1px solid rgba(201,168,76,0.1); }
    [data-testid="stSidebar"] * { color: #B8B8CC !important; }
    .nexus-logo { font-family: 'Cormorant Garamond', serif; font-size: 2rem; font-weight: 300; letter-spacing: 6px; color: #C9A84C; text-align: center; padding: 1rem 0 0.25rem; }
    .nexus-tagline { font-size: 0.62rem; letter-spacing: 2px; text-transform: uppercase; color: #7878A0; text-align: center; margin-bottom: 0.5rem; }
    .gold-divider { height: 1px; width: 60px; margin: 0.5rem auto 1rem; background: linear-gradient(90deg, transparent, #C9A84C, transparent); }
    [data-testid="stMetric"] { background: #12121A; border: 1px solid rgba(201,168,76,0.08); border-radius: 16px; padding: 1rem 1.25rem; border-top: 2px solid #C9A84C; }
    [data-testid="stMetricLabel"] { font-size: 0.65rem !important; letter-spacing: 2px; text-transform: uppercase; color: #7878A0 !important; }
    [data-testid="stMetricValue"] { font-family: 'Cormorant Garamond', serif !important; font-size: 2rem !important; font-weight: 300 !important; color: #E8E8F0 !important; }
    h1, h2, h3 { font-family: 'Cormorant Garamond', serif !important; font-weight: 300 !important; color: #E8E8F0 !important; letter-spacing: 1px; }
    h1 { font-size: 2rem !important; }
    .stTextInput input, .stNumberInput input, [data-testid="stDateInput"] input {
        background: #1A1A26 !important; border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 8px !important; color: #E8E8F0 !important; }
    .stButton > button {
        background: linear-gradient(135deg, #8B6914, #C9A84C) !important;
        color: #0A0A0F !important; border: none !important; font-weight: 600 !important;
        letter-spacing: 1.5px !important; text-transform: uppercase !important;
        font-size: 0.72rem !important; border-radius: 8px !important; padding: 0.5rem 1.5rem !important; }
    .stButton > button:hover { opacity: 0.9 !important; }
    [data-testid="stDataFrame"] { border: 1px solid rgba(201,168,76,0.08); border-radius: 12px; overflow: hidden; }
    .stTabs [data-baseweb="tab-list"] { background: #12121A; border-radius: 10px; gap: 4px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { background: transparent; border-radius: 8px; color: #7878A0; font-size: 0.8rem; letter-spacing: 1px; }
    .stTabs [aria-selected="true"] { background: rgba(201,168,76,0.12) !important; color: #C9A84C !important; }
    .streamlit-expanderHeader { background: #12121A !important; border: 1px solid rgba(201,168,76,0.08) !important; border-radius: 10px; }
    .stSuccess { background: rgba(46,204,139,0.1) !important; border: 1px solid rgba(46,204,139,0.3) !important; color: #2ECC8B !important; border-radius: 8px !important; }
    .stError { background: rgba(232,72,85,0.1) !important; border: 1px solid rgba(232,72,85,0.3) !important; color: #E84855 !important; border-radius: 8px !important; }
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: #12121A; }
    ::-webkit-scrollbar-thumb { background: #8B6914; border-radius: 4px; }
    .page-header-line { width: 40px; height: 1px; background: #C9A84C; margin: 0.5rem 0 1.25rem; }
    .kpi-mini-card { background: #12121A; border: 1px solid rgba(201,168,76,0.08); border-radius: 12px; padding: 12px 16px; margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  DELETE WIDGET
# ══════════════════════════════════════════════════════════════

def delete_widget(section: str, uid: int, records: list, label_fn, key_prefix: str):
    if not records:
        return
    with st.expander(f"🗑  {t('delete')}"):
        options = {label_fn(r): r["id"] for r in records}
        chosen_label = st.selectbox(t("select_delete"), list(options.keys()), key=f"{key_prefix}_del_select")
        if st.button(t("confirm_delete"), key=f"{key_prefix}_del_btn"):
            chosen_id = options[chosen_label]
            delete_row(section, chosen_id, uid)
            st.success(t("deleted_ok"))
            st.rerun()

# ══════════════════════════════════════════════════════════════
#  AUTH PAGE
# ══════════════════════════════════════════════════════════════

def page_auth():
    apply_css()
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(f"""
        <div class="nexus-logo">NEXUS</div>
        <div class="nexus-tagline">{t('tagline')}</div>
        <div class="gold-divider"></div>
        """, unsafe_allow_html=True)

        lc1, lc2, lc3 = st.columns(3)
        with lc1:
            lang_choice = st.selectbox("🌐", ["EN","PT","ES"],
                index=["en","pt","es"].index(st.session_state.get("lang","en")),
                key="auth_lang", label_visibility="collapsed")
            if lang_choice.lower() != st.session_state.get("lang","en"):
                st.session_state["lang"] = lang_choice.lower(); st.rerun()
        with lc2:
            st.markdown("<div style='text-align:center;color:#7878A0;font-size:20px;padding-top:4px'>🌐  💰</div>", unsafe_allow_html=True)
        with lc3:
            cur_opts = ["🇺🇸 USD","🇪🇺 EUR","🇧🇷 BRL"]
            cur_keys = ["USD","EUR","BRL"]
            cur_idx  = cur_keys.index(st.session_state.get("currency","USD"))
            cur_sel  = st.selectbox("💰", cur_opts, index=cur_idx, key="auth_cur", label_visibility="collapsed")
            new_cur  = cur_keys[cur_opts.index(cur_sel)]
            if new_cur != st.session_state.get("currency","USD"):
                st.session_state["currency"] = new_cur; st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        tab_login, tab_register = st.tabs([f"  {t('login')}  ", f"  {t('register')}  "])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            email    = st.text_input(t("email"),    key="li_email", placeholder="your@email.com")
            password = st.text_input(t("password"), type="password", key="li_pass", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(t("login_btn"), use_container_width=True, key="btn_login"):
                result = login(email, password)
                if result["ok"]:
                    st.session_state["user"] = result["user"]
                    st.session_state["page"] = "dashboard"
                    st.rerun()
                else:
                    st.error(result["error"])

        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            name    = st.text_input(t("name"),     key="reg_name",  placeholder="Your full name")
            email_r = st.text_input(t("email"),    key="reg_email", placeholder="your@email.com")
            pass_r  = st.text_input(t("password"), type="password", key="reg_pass", placeholder="Min. 6 characters")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(t("register_btn"), use_container_width=True, key="btn_register"):
                result = register(name, email_r, pass_r)
                if result["ok"]:
                    st.success("✅ Account created! Please log in.")
                else:
                    st.error(result["error"])

# ══════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════

def sidebar_nav():
    with st.sidebar:
        st.markdown(f"""
        <div class="nexus-logo">NEXUS</div>
        <div class="nexus-tagline">{t('tagline')}</div>
        <div class="gold-divider"></div>
        """, unsafe_allow_html=True)

        user = st.session_state.get("user", {})
        initials = "".join(w[0].upper() for w in user.get("name","U").split()[:2])
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;padding:0.5rem 0 1.5rem;">
            <div style="width:36px;height:36px;border-radius:50%;
                background:linear-gradient(135deg,#8B6914,#C9A84C);
                display:flex;align-items:center;justify-content:center;
                font-weight:600;color:#0A0A0F;font-size:13px;flex-shrink:0">{initials}</div>
            <div>
                <div style="font-size:13px;font-weight:500;color:#E8E8F0">{user.get('name','')}</div>
                <div style="font-size:11px;color:#7878A0">{user.get('email','')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#7878A0;margin-bottom:6px'>Overview</div>", unsafe_allow_html=True)
        for icon, key, label in [("◈","dashboard",t("dashboard")),("◎","revenue",t("revenue")),("◫","expenses",t("expenses"))]:
            if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
                st.session_state["page"] = key; st.rerun()

        st.markdown(f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#7878A0;margin:12px 0 6px'>{t('clients')[:8]}</div>", unsafe_allow_html=True)
        for icon, key, label in [("◉","clients",t("clients")),("◧","suppliers",t("suppliers")),("◈","products",t("products"))]:
            if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
                st.session_state["page"] = key; st.rerun()

        st.markdown(f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#7878A0;margin:12px 0 6px'>{t('projects')[:10]}</div>", unsafe_allow_html=True)
        for icon, key, label in [("◑","projects",t("projects")),("◐","kpis",t("kpis"))]:
            if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
                st.session_state["page"] = key; st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#7878A0;margin-bottom:4px'>{t('language')}</div>", unsafe_allow_html=True)
        lang_map = {"English":"en","Português":"pt","Español":"es"}
        chosen_lang = st.selectbox("", list(lang_map.keys()),
            index=list(lang_map.values()).index(st.session_state.get("lang","en")),
            label_visibility="collapsed", key="lang_select")
        if lang_map[chosen_lang] != st.session_state.get("lang","en"):
            st.session_state["lang"] = lang_map[chosen_lang]; st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#7878A0;margin-bottom:4px'>{t('currency')}</div>", unsafe_allow_html=True)
        cur_opts = ["🇺🇸 USD — Dólar", "🇪🇺 EUR — Euro", "🇧🇷 BRL — Real"]
        cur_keys = ["USD","EUR","BRL"]
        cur_idx  = cur_keys.index(st.session_state.get("currency","USD"))
        chosen_cur = st.selectbox("", cur_opts, index=cur_idx, label_visibility="collapsed", key="cur_select")
        new_cur = cur_keys[cur_opts.index(chosen_cur)]
        if new_cur != st.session_state.get("currency","USD"):
            st.session_state["currency"] = new_cur; st.rerun()
        st.markdown(f"<div style='font-size:11px;color:#C9A84C;margin-top:4px'>Active: <b>{get_symbol()}</b></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"⇠  {t('logout')}", use_container_width=True, key="btn_logout"):
            for k in ["user","page"]: st.session_state.pop(k, None)
            st.rerun()

# ══════════════════════════════════════════════════════════════
#  HELPERS UI
# ══════════════════════════════════════════════════════════════

def page_title(title: str, subtitle: str = ""):
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<p style='color:#7878A0;font-size:13px;margin-top:-8px'>{subtitle}</p>", unsafe_allow_html=True)
    st.markdown('<div class="page-header-line"></div>', unsafe_allow_html=True)

def empty_state():
    st.markdown(f"""
    <div style="text-align:center;padding:3rem;color:#7878A0;">
        <div style="font-size:3rem;opacity:.2;margin-bottom:1rem">◇</div>
        <p style="font-size:13px">{t('no_data')}</p>
    </div>""", unsafe_allow_html=True)

def plotly_bar(labels, values, colors=None, title=""):
    layout = get_plotly_layout()
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors or GOLD, marker_line_width=0))
    fig.update_layout(**layout, title=dict(text=title, font=dict(color=PLAT, size=14)))
    fig.update_traces(marker_cornerradius=4)
    st.plotly_chart(fig, use_container_width=True)

def plotly_donut(labels, values, colors, title=""):
    layout = get_plotly_layout()
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.65,
                           marker=dict(colors=colors, line=dict(width=0)),
                           textfont=dict(color=PLAT3)))
    fig.update_layout(**layout, title=dict(text=title, font=dict(color=PLAT, size=14)))
    st.plotly_chart(fig, use_container_width=True)

def status_label(status: str) -> str:
    return {"active": t("active_label"), "pending": t("pending_label"), "inactive": t("inactive_label")}.get(status, status)

def status_badge(status: str) -> str:
    colors = {"active": EMERALD, "pending": AMBER, "inactive": PLAT3}
    c = colors.get(status, PLAT3)
    l = status_label(status)
    return f'<span style="background:rgba(200,200,200,0.08);color:{c};padding:2px 10px;border-radius:20px;font-size:11px">{l}</span>'

# ══════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════

def page_dashboard():
    uid  = st.session_state["user"]["id"]
    name = st.session_state["user"]["name"].split()[0]

    rev_records  = fetch_all("revenue",  uid)
    exp_records  = fetch_all("expenses", uid)
    cli_records  = fetch_all("clients",  uid)
    proj_records = fetch_all("projects", uid)
    kpi_records  = fetch_all("kpis",     uid)

    summary = executive_summary(rev_records, exp_records, cli_records, proj_records, kpi_records)
    fin  = summary["financials"]
    cli  = summary["clients"]
    proj = summary["projects"]

    page_title(t("dashboard"), f"{t('welcome')}, {name}.")

    # ── KPI Cards financeiros ─────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.metric(t("total_revenue"),   fmt(fin["total_revenue"]),  delta=t("ytd"))
    with c2: st.metric(t("total_expenses"),  fmt(fin["total_expenses"]), delta=t("ytd"), delta_color="inverse")
    with c3: st.metric(t("net_profit"),      fmt(fin["net_profit"]))
    with c4: st.metric(t("net_margin"),      f"{fin['gross_margin']}%")
    with c5: st.metric(t("active_clients"),  cli["active"])
    with c6: st.metric(t("active_projects"), proj["active"])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gráficos ──────────────────────────────────────────────
    col_l, col_r = st.columns([2, 1])
    with col_l:
        df_evo = monthly_evolution(rev_records, exp_records)
        if not df_evo.empty:
            layout = get_plotly_layout()
            layout["legend"] = dict(bgcolor="rgba(0,0,0,0)", font=dict(color=PLAT3), orientation="h", y=-0.15)
            fig = go.Figure()
            fig.add_trace(go.Bar(name=t("revenue"),  x=df_evo["month"], y=df_evo["revenue"],  marker_color=GOLD, marker_cornerradius=3))
            fig.add_trace(go.Bar(name=t("expenses"), x=df_evo["month"], y=df_evo["expenses"], marker_color=RUBY, marker_cornerradius=3))
            fig.update_layout(**layout, barmode="group",
                              title=dict(text=t("evolution"), font=dict(color=PLAT, size=14)))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(t("no_data"))

    with col_r:
        if fin["total_revenue"] > 0:
            plotly_donut(
                labels=[t("net_profit"), t("total_expenses")],
                values=[max(0, fin["net_profit"]), fin["total_expenses"]],
                colors=[EMERALD, RUBY], title=t("net_margin"))
        else:
            st.info(t("no_data"))

    # ── Resumo de KPIs no Dashboard ───────────────────────────
    if kpi_records:
        smry = kpi_summary(uid)
        total_k = smry["total"]
        on_t    = smry["on_target"]
        below_t = smry["below_target"]

        st.markdown(f"### {t('kpi_summary')}")
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"""
            <div class="kpi-mini-card">
                <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{PLAT3};margin-bottom:8px">{t('kpi_summary')}</div>
                <div style="font-family:'Cormorant Garamond',serif;font-size:2rem;font-weight:300;color:{PLAT}">{on_t} <span style="font-size:1rem;color:{PLAT3}">{t('of')} {total_k}</span></div>
                <div style="font-size:12px;color:{EMERALD};margin-top:4px">{t('kpis_on_target')}</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="kpi-mini-card">
                <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{PLAT3};margin-bottom:8px">{t('on_target')}</div>
                <div style="font-family:'Cormorant Garamond',serif;font-size:2rem;font-weight:300;color:{EMERALD}">{on_t}</div>
                <div style="font-size:12px;color:{PLAT3};margin-top:4px">✅ {t('on_target')}</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="kpi-mini-card">
                <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{PLAT3};margin-bottom:8px">{t('below_target')}</div>
                <div style="font-family:'Cormorant Garamond',serif;font-size:2rem;font-weight:300;color:{RUBY}">{below_t}</div>
                <div style="font-size:12px;color:{PLAT3};margin-top:4px">⚠️ {t('below_target')}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Top Clientes ──────────────────────────────────────────
    if cli_records:
        st.markdown(f"### {t('top_clients')}")
        df_top = to_df(top_clients(uid))
        if not df_top.empty:
            display = df_top.copy()
            display["revenue"] = display["revenue"].apply(fmt)
            display["status"]  = display["status"].apply(status_label)
            st.dataframe(display, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
#  PAGE: REVENUE
# ══════════════════════════════════════════════════════════════

def page_revenue():
    uid = st.session_state["user"]["id"]
    page_title(t("revenue"))
    sym = get_symbol()

    with st.expander(f"➕  {t('add_revenue')}", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1: rv_date = st.date_input(t("date"), key="rv_date")
        with c2: rv_desc = st.text_input(t("description"), key="rv_desc", placeholder="e.g. Software license sale")
        with c3: rv_amt  = st.number_input(f"{t('amount')} ({sym})", min_value=0.0, step=0.01, key="rv_amt")
        with c4: rv_cat  = st.text_input(t("category"), key="rv_cat", placeholder="e.g. SaaS, Consulting")
        if st.button(t("add"), key="btn_add_rev"):
            if rv_desc and rv_amt > 0:
                insert_row("revenue", uid, {"date": str(rv_date), "description": rv_desc, "amount": rv_amt, "category": rv_cat or "General"})
                st.success("✅"); st.rerun()
            else:
                st.error(t("fill_desc_amount"))

    records = fetch_all("revenue", uid)
    if not records:
        empty_state(); return

    fin = calc_financial_kpis(records, [])
    c1, c2, c3 = st.columns(3)
    with c1: st.metric(t("total_revenue"), fmt(fin["total_revenue"]))
    with c2: st.metric(t("avg_entry"),     fmt(fin["avg_revenue"]))
    with c3: st.metric(t("entries"),       fin["revenue_count"])

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([3, 2])
    with col_l:
        df_growth = revenue_growth(records)
        if not df_growth.empty and len(df_growth) >= 2:
            layout = get_plotly_layout()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_growth["month"], y=df_growth["amount"],
                name=t("revenue"), line=dict(color=GOLD, width=2),
                fill="tozeroy", fillcolor="rgba(201,168,76,0.08)",
                mode="lines+markers", marker=dict(size=5)))
            fig.update_layout(**layout, title=dict(text=t("evolution"), font=dict(color=PLAT, size=14)))
            st.plotly_chart(fig, use_container_width=True)
    with col_r:
        cats = revenue_by_category(uid)
        if cats:
            df_cat = pd.DataFrame(cats)
            plotly_donut(df_cat["category"].tolist(), df_cat["total"].tolist(),
                         [GOLD, SAPPH, EMERALD, AMBER, RUBY], title=t("by_category"))

    df = to_df(records)
    display = df[["id","date","description","category","amount"]].copy()
    display["amount"] = display["amount"].apply(fmt)
    display["date"]   = display["date"].astype(str)
    st.dataframe(display, use_container_width=True, hide_index=True)

    delete_widget("revenue", uid, records,
                  lambda r: f"{r.get('date','—')}  |  {r.get('description','')}  |  {fmt(r.get('amount',0))}",
                  "rev")

# ══════════════════════════════════════════════════════════════
#  PAGE: EXPENSES
# ══════════════════════════════════════════════════════════════

def page_expenses():
    uid = st.session_state["user"]["id"]
    page_title(t("expenses"))
    sym = get_symbol()

    with st.expander(f"➕  {t('add_expenses')}", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1: ex_date = st.date_input(t("date"), key="ex_date")
        with c2: ex_desc = st.text_input(t("description"), key="ex_desc", placeholder="e.g. Cloud infrastructure")
        with c3: ex_amt  = st.number_input(f"{t('amount')} ({sym})", min_value=0.0, step=0.01, key="ex_amt")
        with c4: ex_cat  = st.text_input(t("category"), key="ex_cat", placeholder="e.g. Technology")
        if st.button(t("add"), key="btn_add_exp"):
            if ex_desc and ex_amt > 0:
                insert_row("expenses", uid, {"date": str(ex_date), "description": ex_desc, "amount": ex_amt, "category": ex_cat or "General"})
                st.success("✅"); st.rerun()
            else:
                st.error(t("fill_desc_amount"))

    records  = fetch_all("expenses", uid)
    rev_recs = fetch_all("revenue",  uid)
    if not records:
        empty_state(); return

    fin = calc_financial_kpis(rev_recs, records)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric(t("total_expenses"), fmt(fin["total_expenses"]))
    with c2: st.metric(t("cost_ratio"),     f"{fin['cost_ratio']:.1f}%", delta_color="inverse")
    with c3: st.metric(t("net_margin"),     f"{fin['gross_margin']:.1f}%")
    with c4: st.metric(t("entries"),        fin["expense_count"])

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([2, 2])
    with col_l:
        df_cat = expense_breakdown(records)
        if not df_cat.empty:
            plotly_bar(df_cat["category"].tolist(), df_cat["total"].tolist(),
                       colors=[RUBY, AMBER, SAPPH, EMERALD, GOLD, PLAT3], title=t("by_category"))
    with col_r:
        cats = expenses_by_category(uid)
        if cats:
            df_c = pd.DataFrame(cats)
            plotly_donut(df_c["category"].tolist(), df_c["total"].tolist(),
                         [RUBY, AMBER, SAPPH, EMERALD, GOLD], title=t("by_category"))

    df = to_df(records)
    display = df[["id","date","description","category","amount"]].copy()
    display["amount"] = display["amount"].apply(fmt)
    display["date"]   = display["date"].astype(str)
    st.dataframe(display, use_container_width=True, hide_index=True)

    delete_widget("expenses", uid, records,
                  lambda r: f"{r.get('date','—')}  |  {r.get('description','')}  |  {fmt(r.get('amount',0))}",
                  "exp")

# ══════════════════════════════════════════════════════════════
#  PAGE: CLIENTS
# ══════════════════════════════════════════════════════════════

def page_clients():
    uid = st.session_state["user"]["id"]
    page_title(t("clients"))
    sym = get_symbol()

    with st.expander(f"➕  {t('add_clients')}", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1: cli_name   = st.text_input(t("name"),   key="cli_name",   placeholder="Company name")
        with c2: cli_sector = st.text_input(t("sector"), key="cli_sector", placeholder="e.g. Technology")
        with c3: cli_rev    = st.number_input(f"{t('revenue')} ({sym})", min_value=0.0, step=0.01, key="cli_rev")
        with c4: cli_status = st.selectbox(t("status"), ["active","pending","inactive"],
                                           format_func=lambda s: t(s), key="cli_status")
        if st.button(t("add"), key="btn_add_cli"):
            if cli_name:
                insert_row("clients", uid, {"name": cli_name, "sector": cli_sector, "revenue": cli_rev, "status": cli_status})
                st.success("✅"); st.rerun()
            else:
                st.error(t("name_required"))

    records = fetch_all("clients", uid)
    if not records:
        empty_state(); return

    ana = client_analytics(records)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric(t("active_clients"), ana["active"])
    with c2: st.metric(t("total"),          ana["total"])
    with c3: st.metric(t("total_revenue"),  fmt(ana["total_revenue"]))
    with c4: st.metric(t("top_sector"),     ana["top_sector"])

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([3, 2])
    with col_l:
        df = to_df(records)
        display = df[["id","name","sector","revenue","status"]].copy()
        display["revenue"] = display["revenue"].apply(fmt)
        display["status"]  = display["status"].apply(status_label)
        st.dataframe(display, use_container_width=True, hide_index=True)
    with col_r:
        df_sec = client_revenue_by_sector(records)
        if not df_sec.empty:
            plotly_donut(df_sec["sector"].tolist(), df_sec["revenue"].tolist(),
                         [GOLD, SAPPH, EMERALD, AMBER, RUBY], title=t("by_sector"))

    delete_widget("clients", uid, records,
                  lambda r: f"{r.get('name','')}  |  {r.get('sector','')}  |  {fmt(r.get('revenue',0))}",
                  "cli")

# ══════════════════════════════════════════════════════════════
#  PAGE: SUPPLIERS
# ══════════════════════════════════════════════════════════════

def page_suppliers():
    uid = st.session_state["user"]["id"]
    page_title(t("suppliers"))

    with st.expander(f"➕  {t('add_suppliers')}", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1: s_name     = st.text_input(t("supplier"), key="s_name",     placeholder="Supplier name")
        with c2: s_cat      = st.text_input(t("category"), key="s_cat",      placeholder="e.g. Technology")
        with c3: s_contract = st.text_input(t("contract"), key="s_contract", placeholder="YYYY-MM")
        with c4: s_rating   = st.selectbox(t("rating"), [5,4,3,2,1], key="s_rating")
        if st.button(t("add"), key="btn_add_supp"):
            if s_name:
                insert_row("suppliers", uid, {"name": s_name, "category": s_cat, "contract": s_contract, "rating": s_rating})
                st.success("✅"); st.rerun()
            else:
                st.error(t("name_required"))

    records = fetch_all("suppliers", uid)
    if not records:
        empty_state(); return

    df = to_df(records)
    c1, c2 = st.columns(2)
    with c1: st.metric(t("total_suppliers"), len(df))
    with c2: st.metric(t("avg_rating"),      f"{df['rating'].mean():.1f} / 5")

    df["rating"] = df["rating"].apply(lambda r: "★"*int(r) + "☆"*(5-int(r)))
    st.dataframe(df[["id","name","category","contract","rating"]], use_container_width=True, hide_index=True)

    delete_widget("suppliers", uid, records,
                  lambda r: f"{r.get('name','')}  |  {r.get('category','')}  |  ★{r.get('rating','')}",
                  "supp")

# ══════════════════════════════════════════════════════════════
#  PAGE: PRODUCTS
# ══════════════════════════════════════════════════════════════

def page_products():
    uid = st.session_state["user"]["id"]
    page_title(t("products"))
    sym = get_symbol()

    with st.expander(f"➕  {t('add_products')}", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1: p_name  = st.text_input(t("name"),    key="p_name",  placeholder="Product name")
        with c2: p_price = st.number_input(f"{t('price')} ({sym})", min_value=0.0, step=0.01, key="p_price")
        with c3: p_sales = st.number_input(t("units_sold"), min_value=0, step=1, key="p_sales")
        with c4: p_seg   = st.text_input(t("segment"), key="p_seg",   placeholder="e.g. SaaS")
        if st.button(t("add"), key="btn_add_prod"):
            if p_name:
                insert_row("products", uid, {"name": p_name, "price": p_price, "units_sold": p_sales, "segment": p_seg})
                st.success("✅"); st.rerun()
            else:
                st.error(t("name_required"))

    records = fetch_all("products", uid)
    if not records:
        empty_state(); return

    df = product_analytics(records)
    c1, c2, c3 = st.columns(3)
    with c1: st.metric(t("total_skus"),      len(df))
    with c2: st.metric(t("units_sold"),      f"{df['units_sold'].sum():,}")
    with c3: st.metric(t("product_revenue"), fmt(df["total_revenue"].sum()))

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([3, 2])
    with col_l:
        display = df[["id","name","price","units_sold","segment","total_revenue","pct_of_total"]].copy()
        display["price"]         = display["price"].apply(fmt)
        display["total_revenue"] = display["total_revenue"].apply(fmt)
        display["pct_of_total"]  = display["pct_of_total"].astype(str) + "%"
        st.dataframe(display, use_container_width=True, hide_index=True)
    with col_r:
        if not df.empty:
            plotly_donut(df["name"].tolist(), df["total_revenue"].tolist(),
                         [GOLD, SAPPH, EMERALD, AMBER, RUBY], title=t("revenue_share"))

    delete_widget("products", uid, records,
                  lambda r: f"{r.get('name','')}  |  {fmt(r.get('price',0))}  |  {r.get('units_sold',0)} {t('units_sold').lower()}",
                  "prod")

# ══════════════════════════════════════════════════════════════
#  PAGE: PROJECTS
# ══════════════════════════════════════════════════════════════

def page_projects():
    uid = st.session_state["user"]["id"]
    page_title(t("projects"))

    with st.expander(f"➕  {t('add_projects')}", expanded=False):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: pj_name     = st.text_input(t("name"),     key="pj_name",     placeholder="Project name")
        with c2: pj_lead     = st.text_input(t("lead"),     key="pj_lead",     placeholder="Person responsible")
        with c3: pj_deadline = st.date_input(t("deadline"), key="pj_deadline")
        with c4: pj_progress = st.number_input(t("progress"), min_value=0, max_value=100, step=1, key="pj_progress")
        with c5: pj_status   = st.selectbox(t("status"), ["active","pending","inactive"],
                                            format_func=lambda s: t(s), key="pj_status")
        if st.button(t("add"), key="btn_add_proj"):
            if pj_name:
                insert_row("projects", uid, {"name": pj_name, "lead": pj_lead, "deadline": str(pj_deadline), "progress": pj_progress, "status": pj_status})
                st.success("✅"); st.rerun()
            else:
                st.error(t("name_required"))

    records = fetch_all("projects", uid)
    if not records:
        empty_state(); return

    ana = project_analytics(records)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric(t("active_projects"), ana["active"])
    with c2: st.metric(t("avg_progress"),    f"{ana['avg_progress']:.0f}%")
    with c3: st.metric(t("on_track"),        ana["on_track"])
    with c4: st.metric(t("at_risk"),         ana["at_risk"])

    st.markdown("<br>", unsafe_allow_html=True)
    df = to_df(records)
    for _, row in df.iterrows():
        c1, c2, c3, c4, c5 = st.columns([3, 2, 1, 2, 1])
        with c1:
            st.markdown(f"**{row['name']}**  <span style='color:{PLAT3};font-size:12px'>· {row.get('lead','')} </span>", unsafe_allow_html=True)
            prog  = int(row.get("progress", 0))
            color = EMERALD if prog >= 70 else (AMBER if prog >= 30 else RUBY)
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.06);border-radius:4px;height:4px;width:100%;margin-top:4px">
              <div style="width:{prog}%;height:4px;border-radius:4px;background:{color}"></div>
            </div>
            <span style="font-size:11px;color:{PLAT3}">{prog}%</span>
            """, unsafe_allow_html=True)
        with c2:
            deadline = str(row.get("deadline",""))[:10]
            st.markdown(f"<span style='font-family:DM Mono,monospace;color:{GOLD};font-size:13px'>{deadline}</span>", unsafe_allow_html=True)
        with c4:
            st.markdown(status_badge(row.get("status","inactive")), unsafe_allow_html=True)
        st.markdown("<hr style='border-color:rgba(255,255,255,0.04);margin:6px 0'>", unsafe_allow_html=True)

    delete_widget("projects", uid, records,
                  lambda r: f"{r.get('name','')}  |  {r.get('lead','')}  |  {r.get('progress',0)}%  |  {t(r.get('status',''))}",
                  "proj")

# ══════════════════════════════════════════════════════════════
#  PAGE: KPIs
# ══════════════════════════════════════════════════════════════

def page_kpis():
    uid = st.session_state["user"]["id"]
    page_title(t("kpis"), t("strategic_indicators"))

    with st.expander(f"➕  {t('add_kpi')}", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1: k_name    = st.text_input(t("indicator"), key="k_name",  placeholder="e.g. Net Margin")
        with c2: k_current = st.number_input(t("current"), step=0.01,     key="k_current")
        with c3: k_target  = st.number_input(t("target"),  step=0.01,     key="k_target")
        with c4:
            sym = get_symbol()
            unit_options = {
                f"% — {t('net_margin')}": "%",
                f"{sym} — {t('amount')}": sym,
                f"pts — NPS / Score": "pts",
                f"un — {t('units_sold')}": "un",
                f"days — {t('deadline')}": "days",
                f"x — {t('revenue')} ratio": "x",
            }
            unit_label = st.selectbox(t("unit"), list(unit_options.keys()), key="k_unit_label")
            k_unit = unit_options[unit_label]

        if st.button(t("add"), key="btn_add_kpi"):
            if k_name:
                insert_row("kpis", uid, {"name": k_name, "current_val": k_current, "target_val": k_target, "unit": k_unit})
                st.success("✅"); st.rerun()
            else:
                st.error(t("name_required"))

    records = fetch_all("kpis", uid)
    if not records:
        empty_state(); return

    df   = kpi_analytics(records)
    smry = kpi_summary(uid)
    total_k = smry["total"]
    on_t    = smry["on_target"]
    below_t = smry["below_target"]

    # ── Cards com "X de Y na meta" ────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric(t("kpis"), total_k)
    with c2: st.metric(t("on_target"), on_t)
    with c3: st.metric(t("below_target"), below_t)
    with c4:
        label = f"{on_t} {t('of')} {total_k} {t('kpis_on_target')}"
        st.metric(t("hit_rate"), label)

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([3, 2])

    with col_l:
        for _, row in df.iterrows():
            color       = EMERALD if row["on_target"] else RUBY
            achievement = min(100, max(0, float(row["achievement"])))
            status_txt  = t("on_target") if row["on_target"] else t("below_target")
            st.markdown(f"""
            <div style="background:#12121A;border:1px solid rgba(201,168,76,0.08);border-radius:12px;padding:14px 18px;margin-bottom:8px">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:500;color:#E8E8F0">{row['name']}</span>
                <span style="font-size:11px;background:rgba(200,200,200,0.08);color:{color};padding:2px 10px;border-radius:20px">
                  {'✅' if row['on_target'] else '⚠️'} {status_txt}
                </span>
              </div>
              <div style="display:flex;gap:24px;margin-top:10px">
                <div>
                  <div style="font-size:10px;letter-spacing:1.5px;color:{PLAT3};text-transform:uppercase">{t('current')}</div>
                  <div style="font-family:'DM Mono',monospace;font-size:18px;color:{PLAT}">{row['current_val']}{row['unit']}</div>
                </div>
                <div>
                  <div style="font-size:10px;letter-spacing:1.5px;color:{PLAT3};text-transform:uppercase">{t('target')}</div>
                  <div style="font-family:'DM Mono',monospace;font-size:18px;color:{PLAT3}">{row['target_val']}{row['unit']}</div>
                </div>
                <div>
                  <div style="font-size:10px;letter-spacing:1.5px;color:{PLAT3};text-transform:uppercase">Delta</div>
                  <div style="font-family:'DM Mono',monospace;font-size:18px;color:{color}">{'+' if row['delta']>=0 else ''}{row['delta']}{row['unit']}</div>
                </div>
              </div>
              <div style="background:rgba(255,255,255,0.05);border-radius:4px;height:4px;width:100%;margin-top:12px">
                <div style="width:{achievement}%;height:4px;border-radius:4px;background:linear-gradient(90deg,#8B6914,{GOLD})"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    with col_r:
        if total_k > 0:
            plotly_donut(
                labels=[t("on_target"), t("below_target")],
                values=[on_t, below_t],
                colors=[EMERALD, RUBY],
                title=f"{on_t} {t('of')} {total_k} {t('kpis_on_target')}")

    delete_widget("kpis", uid, records,
                  lambda r: f"{r.get('name','')}  |  {r.get('current_val','')} → {r.get('target_val','')}{r.get('unit','')}",
                  "kpi")

# ══════════════════════════════════════════════════════════════
#  MAIN ROUTER
# ══════════════════════════════════════════════════════════════

def main():
    if "lang"     not in st.session_state: st.session_state["lang"]     = "en"
    if "page"     not in st.session_state: st.session_state["page"]     = "dashboard"
    if "currency" not in st.session_state: st.session_state["currency"] = "USD"

    user = st.session_state.get("user")
    if not user:
        page_auth()
        return

    apply_css()
    sidebar_nav()

    routes = {
        "dashboard": page_dashboard,
        "revenue":   page_revenue,
        "expenses":  page_expenses,
        "clients":   page_clients,
        "suppliers": page_suppliers,
        "products":  page_products,
        "projects":  page_projects,
        "kpis":      page_kpis,
    }
    routes.get(st.session_state.get("page", "dashboard"), page_dashboard)()

if __name__ == "__main__":
    main()