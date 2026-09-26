import os
from dotenv import load_dotenv

load_dotenv()

BRONZE_DIR = os.getenv('DATALAKE_BRONZE_DIR')
SILVER_DIR = os.getenv('DATALAKE_SILVER_DIR')
GOLD_DIR = os.getenv('DATALAKE_GOLD_DIR')

env_columns = os.getenv('EXPECTED_COLUMNS', 'Data,Valor,Identificador,Descrição')
EXPECTED_COLUMNS = [col.strip() for col in env_columns.split(',')]

if not BRONZE_DIR:
    raise ValueError('A variável de ambiente DATALAKE_BRONZE_DIR não está configurada.')
