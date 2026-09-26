import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.config import SILVER_DIR, EXPECTED_COLUMNS

st.set_page_config(page_title="Ledger Management", layout="wide")
st.title("📊 Painel de Controle - Livro Caixa")

@st.cache_data
def load_data():
    silver_path = Path(SILVER_DIR)
    if not silver_path.exists() or not any(silver_path.iterdir()):
        return None
    dfs = []
    for parquet_file in silver_path.glob("*.parquet"):
        dfs.append(pd.read_parquet(parquet_file))
    if not dfs:
        return None
    df = pd.concat(dfs, ignore_index=True)
    return df

df = load_data()
if df is None or df.empty:
    st.warning("Nenhum dado encontrado na camada Silver. Execute a ingestão primeiro.")
    st.stop()

date_col = EXPECTED_COLUMNS[0]
val_col = EXPECTED_COLUMNS[1]
desc_col = EXPECTED_COLUMNS[3] if len(EXPECTED_COLUMNS) > 3 else EXPECTED_COLUMNS[2]

st.sidebar.header("Filtros")
ano_meses = df[date_col].dt.to_period('M').astype(str).unique().tolist()
ano_meses.sort()
selected_months = st.sidebar.multiselect("Selecione os meses", ano_meses, default=ano_meses)

df['Mes_Str'] = df[date_col].dt.to_period('M').astype(str)
filtered_df = df[df['Mes_Str'].isin(selected_months)]

st.header("Resumo Mensal")
resumo = filtered_df.groupby(['Mes_Str', 'Tipo'])[val_col].sum().unstack(fill_value=0)
if 'Entrada' not in resumo.columns:
    resumo['Entrada'] = 0.0
if 'Saída' not in resumo.columns:
    resumo['Saída'] = 0.0

resumo['Saldo'] = resumo['Entrada'] + resumo['Saída']
resumo = resumo.reset_index()

col1, col2, col3 = st.columns(3)
col1.metric("Total Entradas", f"R$ {resumo['Entrada'].sum():,.2f}")
col2.metric("Total Saídas", f"R$ {resumo['Saída'].sum():,.2f}")
col3.metric("Saldo Período", f"R$ {resumo['Saldo'].sum():,.2f}")

fig = px.bar(
    resumo, 
    x='Mes_Str', 
    y=['Entrada', 'Saída'], 
    barmode='group',
    title='Entradas vs Saídas por Mês',
    labels={'value': 'Valor (R$)', 'Mes_Str': 'Mês', 'variable': 'Tipo'},
    color_discrete_map={'Entrada': 'green', 'Saída': 'red'}
)
st.plotly_chart(fig, use_container_width=True)

st.header("🔍 Análise de Vazamentos")

# Filtros para a análise de vazamentos
leak_col1, leak_col2 = st.columns([2, 1])
with leak_col1:
    threshold = st.slider("Definir limite de gastos para considerar como 'vazamento' (R$)", min_value=0, max_value=5000, value=500, step=100)
with leak_col2:
    search_desc = st.text_input("Busca na Descrição", "")

# Aplicar filtro de valor (Lembre-se que as saídas são negativas)
leaks = filtered_df[filtered_df[val_col] <= -threshold]

# Aplicar filtro de descrição se o usuário digitou algo
if search_desc:
    leaks = leaks[leaks[desc_col].str.contains(search_desc, case=False, na=False)]

leaks = leaks.sort_values(by=val_col)
total_vazamentos = leaks[val_col].sum()

# Mostrar a métrica e a tabela
st.subheader(f"Gastos superiores a R$ {threshold}")
st.metric("Somatória dos Vazamentos Exibidos", f"R$ {total_vazamentos:,.2f}")

st.dataframe(leaks[[date_col, val_col, desc_col, 'Tipo', 'arquivo_origem']], use_container_width=True)

st.header("Tabela Geral de Transações")
st.dataframe(filtered_df.sort_values(by=date_col, ascending=False), use_container_width=True)
