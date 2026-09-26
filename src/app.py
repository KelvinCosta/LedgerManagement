import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.config import SILVER_DIR, EXPECTED_COLUMNS
from src.db import load_annotations, save_annotations

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
id_col = EXPECTED_COLUMNS[2]
desc_col = EXPECTED_COLUMNS[3] if len(EXPECTED_COLUMNS) > 3 else EXPECTED_COLUMNS[2]

annotations_df = load_annotations()
if not annotations_df.empty:
    df = df.merge(annotations_df, left_on=id_col, right_on='identificador', how='left')
    df['categoria'] = df['categoria'].fillna('Não Categorizado')
    df['notas'] = df['notas'].fillna('')
    df['verificar'] = df['verificar'].fillna(0).astype(bool)
else:
    df['identificador'] = df[id_col]
    df['categoria'] = 'Não Categorizado'
    df['notas'] = ''
    df['verificar'] = False

st.sidebar.header("Filtros Globais")
ano_meses = df[date_col].dt.to_period('M').astype(str).unique().tolist()
ano_meses.sort()
selected_months = st.sidebar.multiselect("Selecione os meses", ano_meses, default=ano_meses)

df['Mes_Str'] = df[date_col].dt.to_period('M').astype(str)
filtered_df = df[df['Mes_Str'].isin(selected_months)]

tab_resumo, tab_analise, tab_gestao = st.tabs(["Resumo Mensal", "Análise de Vazamentos", "Gestão e Anotações"])

with tab_resumo:
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
        resumo, x='Mes_Str', y=['Entrada', 'Saída'], barmode='group',
        title='Entradas vs Saídas por Mês',
        labels={'value': 'Valor (R$)', 'Mes_Str': 'Mês', 'variable': 'Tipo'},
        color_discrete_map={'Entrada': 'green', 'Saída': 'red'}
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_analise:
    st.header("🔍 Análise de Vazamentos")
    st.markdown("Aqui mostramos saídas suspeitas. **Transações categorizadas como 'Aplicação' são automaticamente removidas desta lista.**")
    
    leak_col1, leak_col2 = st.columns([2, 1])
    with leak_col1:
        threshold = st.slider("Definir limite de gastos para considerar como 'vazamento' (R$)", min_value=0, max_value=5000, value=500, step=100)
    with leak_col2:
        search_desc = st.text_input("Busca na Descrição", "")

    leaks = filtered_df[(filtered_df[val_col] <= -threshold) & (filtered_df['categoria'] != 'Aplicação')]
    if search_desc:
        leaks = leaks[leaks[desc_col].str.contains(search_desc, case=False, na=False)]

    leaks = leaks.sort_values(by=val_col)
    st.subheader(f"Gastos superiores a R$ {threshold}")
    st.metric("Somatória dos Vazamentos Exibidos", f"R$ {leaks[val_col].sum():,.2f}")
    st.dataframe(leaks[[date_col, val_col, desc_col, 'categoria', 'notas', 'verificar', 'arquivo_origem']], use_container_width=True)

with tab_gestao:
    st.header("Gestão de Transações")
    st.markdown("Edite as categorias, adicione notas e marque itens para verificação. Clique em **Salvar Alterações** para persistir os dados.")
    
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        cat_filter = st.multiselect("Filtrar por Categoria", df['categoria'].unique().tolist())
    with col_f2:
        st.write("")
        st.write("")
        only_verify = st.checkbox("Mostrar apenas itens com 'Verificar'")
    with col_f3:
        search_edit_desc = st.text_input("Buscador por Descrição", "", key="search_gestao_desc")
        
    edit_df = filtered_df.copy()
    if cat_filter:
        edit_df = edit_df[edit_df['categoria'].isin(cat_filter)]
    if only_verify:
        edit_df = edit_df[edit_df['verificar'] == True]
    if search_edit_desc:
        edit_df = edit_df[edit_df[desc_col].str.contains(search_edit_desc, case=False, na=False)]

    edit_df = edit_df.sort_values(by=date_col, ascending=False)
    
    edited_df = st.data_editor(
        edit_df,
        column_config={
            "categoria": st.column_config.SelectboxColumn(
                "Categoria",
                help="Classifique a transação",
                options=["Não Categorizado", "Vazamento", "Aplicação", "Essencial", "Fixo", "Lazer", "Salário"],
                required=True,
            ),
            "notas": st.column_config.TextColumn("Notas"),
            "verificar": st.column_config.CheckboxColumn("Verificar?", default=False),
            id_col: None, 
            "identificador": None, 
            "arquivo_origem": None,
            "Tipo": None,
            "Mes_Str": None
        },
        disabled=[date_col, val_col, desc_col],
        use_container_width=True,
        hide_index=True,
        key="data_editor"
    )

    if st.button("Salvar Alterações", type="primary"):
        to_save = edited_df[['identificador', 'categoria', 'notas', 'verificar']].copy()
        
        all_annotations = load_annotations()
        if not all_annotations.empty:
            all_annotations = all_annotations[~all_annotations['identificador'].isin(to_save['identificador'])]
            to_save = pd.concat([all_annotations, to_save], ignore_index=True)
            
        save_annotations(to_save)
        st.cache_data.clear()
        st.success("Anotações salvas com sucesso!")
        st.rerun()
