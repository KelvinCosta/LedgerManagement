import pandas as pd
from pathlib import Path

def parse_csv(file_path: Path) -> pd.DataFrame:
    try:
        try:
            df = pd.read_csv(file_path, sep=',')
            if len(df.columns) == 1:
                df = pd.read_csv(file_path, sep=';')
        except Exception:
            df = pd.read_csv(file_path, sep=';')

        expected_columns = ['Data', 'Valor', 'Identificador', 'Descrição']
        
        missing_cols = [col for col in expected_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"{file_path.name} missing columns: {missing_cols}")

        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
        
        if df['Valor'].dtype == 'O': 
            df['Valor'] = df['Valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
            
        return df[expected_columns]

    except Exception as e:
        print(f"Erro ao processar o arquivo CSV {file_path}: {e}")
        return None
