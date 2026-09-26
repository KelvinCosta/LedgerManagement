import os
from dotenv import load_dotenv

load_dotenv()

BRONZE_DIR = os.getenv("DATALAKE_BRONZE_DIR")
SILVER_DIR = os.getenv("DATALAKE_SILVER_DIR")
GOLD_DIR = os.getenv("DATALAKE_GOLD_DIR")

if not BRONZE_DIR:
    raise ValueError("A variável de ambiente DATALAKE_BRONZE_DIR não está configurada.")
