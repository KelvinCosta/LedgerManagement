import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'annotations.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS annotations (
            identificador TEXT PRIMARY KEY,
            categoria TEXT,
            notas TEXT,
            verificar INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def load_annotations():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM annotations", conn)
    conn.close()
    return df

def save_annotations(df_annotations):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    # df_annotations deve ter as colunas: identificador, categoria, notas, verificar
    df_annotations.to_sql('annotations', conn, if_exists='replace', index=False)
    conn.close()
