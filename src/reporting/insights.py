import pandas as pd
from pathlib import Path
from src.config import SILVER_DIR, EXPECTED_COLUMNS

def generate_monthly_report():
    silver_path = Path(SILVER_DIR)
    if not silver_path.exists() or not any(silver_path.iterdir()):
        print('Nenhum dado encontrado na camada Silver para gerar relatórios.')
        return
    dfs = []
    for parquet_file in silver_path.glob('*.parquet'):
        df = pd.read_parquet(parquet_file)
        dfs.append(df)
    if not dfs:
        return
    full_df = pd.concat(dfs, ignore_index=True)
    date_col = EXPECTED_COLUMNS[0]
    val_col = EXPECTED_COLUMNS[1]
    full_df['Ano_Mes'] = full_df[date_col].dt.to_period('M')
    resumo = full_df.groupby(['Ano_Mes', 'Tipo'])[val_col].sum().unstack(fill_value=0)
    if 'Entrada' not in resumo.columns:
        resumo['Entrada'] = 0.0
    if 'Saída' not in resumo.columns:
        resumo['Saída'] = 0.0
    resumo['Saldo_Mensal'] = resumo['Entrada'] + resumo['Saída']
    print('\n--- RESUMO MENSAL ---')
    print(resumo)
    print('---------------------\n')
    return full_df

def detect_potential_leaks(df: pd.DataFrame, threshold=-1000.0):
    if df is None or df.empty:
        return
    val_col = EXPECTED_COLUMNS[1]
    date_col = EXPECTED_COLUMNS[0]
    desc_col = EXPECTED_COLUMNS[3] if len(EXPECTED_COLUMNS) > 3 else EXPECTED_COLUMNS[2]
    leaks = df[df[val_col] <= threshold].sort_values(by=val_col)
    print(f'\n--- POTENCIAIS VAZAMENTOS (Saídas menores que {threshold}) ---')
    if leaks.empty:
        print('Nenhum vazamento identificado com os parâmetros atuais.')
    else:
        print(leaks[[date_col, val_col, desc_col, 'arquivo_origem']])
    print('------------------------------------------------------------\n')

if __name__ == '__main__':
    df_completo = generate_monthly_report()
    if df_completo is not None:
        detect_potential_leaks(df_completo, threshold=-500.0)
