import os
import pyodbc
from dotenv import load_dotenv

# 📥 Cargar las variables del .env
load_dotenv()

def get_db_connection():
    # 🔗 Construir la cadena de conexión con variables de entorno
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password}"
    )

    return pyodbc.connect(conn_str)

# lpp0server.database.windows.net
# BiblioTrackUser
# B1bl10tr4ckUs3r