import pandas as pd
from pathlib import Path
import os
from src.config import EXPECTED_COLUMNS

def save_to_silver(df: pd.DataFrame, source_filename: str, silver_dir: str):
    if df is None or df.empty:
        print(f'Nenhum dado para salvar de {source_filename}.')
        return
    os.makedirs(silver_dir, exist_ok=True)
    df['arquivo_origem'] = source_filename
    val_col = EXPECTED_COLUMNS[1]
    df['Tipo'] = df[val_col].apply(lambda x: 'Entrada' if x >= 0 else 'Saída')
    output_filename = f'{Path(source_filename).stem}.parquet'
    output_path = Path(silver_dir) / output_filename
    df.to_parquet(output_path, engine='pyarrow', index=False)
    print(f'Arquivo salvo com sucesso na camada Silver: {output_path}')
