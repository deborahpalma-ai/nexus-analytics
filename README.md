# ◈ NEXUS Analytics
### Business Performance & Financial Analytics Platform

---

## Stack Tecnológica

| Camada | Tecnologia | Função |
|---|---|---|
| **Interface** | Streamlit | Portal interativo e responsivo |
| **Análise** | Pandas | KPIs, margens, crescimento, tendências |
| **Banco de Dados** | SQLite + SQL puro | Armazenamento relacional com queries explícitas |
| **Visualização** | Plotly | Gráficos executivos interativos |
| **Segurança** | bcrypt | Hash seguro de senhas |

---

## Estrutura do Projeto

```
nexus-analytics/
├── app.py                  ← Portal Streamlit (interface principal)
├── requirements.txt        ← Dependências Python
├── nexus.db                ← Banco SQLite (criado automaticamente)
├── backend/
│   ├── __init__.py
│   ├── database.py         ← SQL: criação de tabelas e queries analíticas
│   ├── models.py           ← Pandas: KPIs, margens, crescimento
│   └── auth.py             ← Autenticação com bcrypt
└── README.md
```

---

## Como Rodar

### 1. Pré-requisitos
- Python 3.10 ou superior
- pip atualizado

### 2. Clone / Abra no VS Code
Abra a pasta `nexus-analytics` no VS Code.

### 3. Crie um ambiente virtual (recomendado)
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 4. Instale as dependências
```bash
pip install -r requirements.txt
```

### 5. Execute o app
```bash
streamlit run app.py
```

O browser abrirá automaticamente em `http://localhost:8501`

---

## Funcionalidades

### Autenticação
- Cadastro com nome, e-mail e senha (hash bcrypt)
- Login com validação
- Sessão persistida por usuário
- Dados completamente isolados por usuário

### Módulos
| Módulo | Descrição |
|---|---|
| **Dashboard** | KPIs consolidados, gráficos de evolução mensal, top clientes |
| **Receitas** | Registro, análise mensal, crescimento, breakdown por categoria |
| **Despesas** | Registro, cost ratio, margem líquida, análise por categoria |
| **Clientes** | Portfólio, receita por setor, status, analytics |
| **Fornecedores** | Rede de fornecedores, avaliações, contratos |
| **Produtos** | Catálogo, receita por produto, participação de mercado |
| **Projetos** | Pipeline com progresso visual, responsáveis, prazos |
| **KPIs** | Tracker de indicadores estratégicos com metas e deltas |

### Idiomas
- 🇺🇸 English
- 🇧🇷 Português
- 🇪🇸 Español

---

## O que isso demonstra para empresas

```
Python        → lógica de negócio, análise, autenticação
Pandas        → KPIs, margens, crescimento, análise exploratória
SQL (SQLite)  → modelagem relacional, queries analíticas, CASE WHEN, GROUP BY
Streamlit     → portal interativo de dados
Plotly        → visualização executiva
```

> **"Essa profissional entende dados E entende negócios."**
> — Perfil ideal para: Business Analyst · Data Analyst · Operations Analyst · Product Operations

---

## Requisitos Mínimos

- Python 3.10+
- Streamlit 1.35+
- Pandas 2.2+
- Plotly 5.22+
- bcrypt 4.1+
