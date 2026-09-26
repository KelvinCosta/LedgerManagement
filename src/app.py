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
    df['categoria'] = df['categoria'].fillna('N\u00e3o Categorizado')
    df['notas'] = df['notas'].fillna('')
    df['verificar'] = df['verificar'].fillna(0).astype(bool)
else:
    df['categoria'] = 'N\u00e3o Categorizado'
    df['notas'] = ''
    df['verificar'] = False

st.sidebar.header("Filtros Globais")
ano_meses = df[date_col].dt.to_period('M').astype(str).unique().tolist()
ano_meses.sort()
selected_months = st.sidebar.multiselect("Selecione os meses", ano_meses, default=ano_meses)

df['Mes_Str'] = df[date_col].dt.to_period('M').astype(str)
filtered_df = df[df['Mes_Str'].isin(selected_months)]

tab_resumo, tab_analise, tab_gestao = st.tabs(["Resumo Mensal", "An\u00e1lise de Vazamentos", "Gest\u00e3o e Anota\u00e7\u00f5es"])

with tab_resumo:
    st.header("Resumo Mensal")
    resumo = filtered_df.groupby(['Mes_Str', 'Tipo'])[val_col].sum().unstack(fill_value=0)
    if 'Entrada' not in resumo.columns:
        resumo['Entrada'] = 0.0
    if 'Sa\u00edda' not in resumo.columns:
        resumo['Sa\u00edda'] = 0.0
    resumo['Saldo'] = resumo['Entrada'] + resumo['Sa\u00edda']
    resumo = resumo.reset_index()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Entradas", f"R$ {resumo['Entrada'].sum():,.2f}")
    col2.metric("Total Sa\u00eddas", f"R$ {resumo['Sa\u00edda'].sum():,.2f}")
    col3.metric("Saldo Per\u00edodo", f"R$ {resumo['Saldo'].sum():,.2f}")

    fig = px.bar(
        resumo, x='Mes_Str', y=['Entrada', 'Sa\u00edda'], barmode='group',
        title='Entradas vs Sa\u00eddas por M\u00eas',
        labels={'value': 'Valor (R$)', 'Mes_Str': 'M\u00eas', 'variable': 'Tipo'},
        color_discrete_map={'Entrada': 'green', 'Sa\u00edda': 'red'}
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_analise:
    st.header("🔍 An\u00e1lise de Vazamentos")
    st.markdown("Aqui mostramos sa\u00eddas suspeitas. **Transa\u00e7\u00f5es categorizadas como 'Aplica\u00e7\u00e3o' s\u00e3o automaticamente removidas desta lista.**")
    
    leak_col1, leak_col2 = st.columns([2, 1])
    with leak_col1:
        threshold = st.slider("Definir limite de gastos para considerar como 'vazamento' (R$)", min_value=0, max_value=5000, value=500, step=100)
    with leak_col2:
        search_desc = st.text_input("Busca na Descri\u00e7\u00e3o", "")

    leaks = filtered_df[(filtered_df[val_col] <= -threshold) & (filtered_df['categoria'] != 'Aplica\u00e7\u00e3o')]
    if search_desc:
        leaks = leaks[leaks[desc_col].str.contains(search_desc, case=False, na=False)]

    leaks = leaks.sort_values(by=val_col)
    st.subheader(f"Gastos superiores a R$ {threshold}")
    st.metric("Somat\u00f3ria dos Vazamentos Exibidos", f"R$ {leaks[val_col].sum():,.2f}")
    st.dataframe(leaks[[date_col, val_col, desc_col, 'categoria', 'notas', 'verificar', 'arquivo_origem']], use_container_width=True)

with tab_gestao:
    st.header("Gest\u00e3o de Transa\u00e7\u00f5es")
    st.markdown("Edite as categorias, adicione notas e marque itens para verifica\u00e7\u00e3o. Para **a\u00e7\u00f5es em massa**, marque as caixinhas na tabela e use a op\u00e7\u00e3o abaixo!")
    
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        todas_categorias = sorted(["Não Categorizado", "Vazamento", "Aplicação", "Essencial", "Fixo", "Lazer", "Salário", "Recebimento", "Resgate", "Transferência", "Outro"])
        all_cats = sorted(list(set(df['categoria'].dropna().unique().tolist() + todas_categorias)))
        cat_filter = st.multiselect("Filtrar por Categoria", all_cats)
    with col_f2:
        st.write("")
        st.write("")
        only_verify = st.checkbox("Mostrar apenas itens com 'Verificar'")
    with col_f3:
        search_edit_desc = st.text_input("Buscador por Descri\u00e7\u00e3o", "", key="search_gestao_desc")
        
    edit_df = filtered_df.copy()
    if cat_filter:
        edit_df = edit_df[edit_df['categoria'].isin(cat_filter)]
    if only_verify:
        edit_df = edit_df[edit_df['verificar'] == True]
    if search_edit_desc:
        edit_df = edit_df[edit_df[desc_col].str.contains(search_edit_desc, case=False, na=False)]

    edit_df = edit_df.sort_values(by=date_col, ascending=False)
    col_m1, col_m2 = st.columns([3, 1])
    with col_m1:
        st.metric("Somatória das Transações Exibidas", f"R$ {edit_df[val_col].sum():,.2f}")
    with col_m2:
        st.write("") # push down a bit
        select_all = st.checkbox("Selecionar todas visíveis")
        
    # Inserir coluna de checkbox para ação em lote
    edit_df.insert(0, 'Selecionar', select_all)
    edited_df = st.data_editor(
        edit_df,
        column_config={
            "Selecionar": st.column_config.CheckboxColumn("\u2705", default=False),
            "categoria": st.column_config.SelectboxColumn(
                "Categoria",
                help="Classifique a transa\u00e7\u00e3o",
                options=todas_categorias,
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

    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 3])
    
    with col_btn1:
        if st.button("Salvar Altera\u00e7\u00f5es Manuais", type="primary"):
            to_save = edited_df[[id_col, 'categoria', 'notas', 'verificar']].copy()
            to_save = to_save.rename(columns={id_col: 'identificador'})
            
            all_annotations = load_annotations()
            if not all_annotations.empty:
                all_annotations = all_annotations[~all_annotations['identificador'].isin(to_save['identificador'])]
                to_save = pd.concat([all_annotations, to_save], ignore_index=True)
                
            save_annotations(to_save)
            st.cache_data.clear()
            st.success("Anota\u00e7\u00f5es salvas com sucesso!")
            st.rerun()

    with col_btn2:
        bulk_cat = st.selectbox("A\u00e7\u00e3o em Lote (Selecione as caixinhas \u2705)", todas_categorias, key="bulk_cat_select", label_visibility="collapsed")

    with col_btn3:
        if st.button("Aplicar Categoria \u00e0s Selecionadas"):
            selected_rows = edited_df[edited_df['Selecionar'] == True]
            if not selected_rows.empty:
                to_save = selected_rows[[id_col, 'categoria', 'notas', 'verificar']].copy()
                to_save['categoria'] = bulk_cat
                to_save = to_save.rename(columns={id_col: 'identificador'})
                
                all_annotations = load_annotations()
                if not all_annotations.empty:
                    all_annotations = all_annotations[~all_annotations['identificador'].isin(to_save['identificador'])]
                    to_save = pd.concat([all_annotations, to_save], ignore_index=True)
                    
                save_annotations(to_save)
                st.cache_data.clear()
                st.success(f"Categoria '{bulk_cat}' aplicada a {len(selected_rows)} transa\u00e7\u00f5es!")
                st.rerun()
            else:
                st.warning("Nenhuma linha selecionada. Marque as caixinhas '\u2705' na tabela primeiro.")
