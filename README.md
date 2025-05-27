
# 📚 BiblioTrackBot

Un bot de Telegram para interactuar con la base de datos de la biblioteca: buscar libros, gestionar reservas y préstamos, y recibir recomendaciones personalizadas.

---

## 🚀 Requisitos

- **Python 3.10 o superior**.
- Instalar dependencias:

  ```bash
  pip install -r requirements.txt
  ```

- Configurar el archivo **.env** en la raíz del proyecto.

---

## ⚙️ Configuración del archivo `.env`

Ejemplo:

```plaintext
# Token del bot de Telegram
TELEGRAM_BOT_TOKEN=tu_token_de_telegram

# Clave de Gemini API para recomendaciones
GEMINI_API_KEY=tu_api_key_de_gemini

# Conexión a la base de datos SQL Server
DB_SERVER=NEFEREST
DB_NAME=SysBiblioteca
DB_USER=Andre
DB_PASSWORD=1234
```

---

## ⚙️ Configuración de la base de datos

El archivo `db/connection.py` toma las credenciales de la base de datos desde el `.env`:

```python
import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
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
```

---

## 🛠️ Ejecución del bot

1️⃣ Asegúrate de tener el `.env` configurado.  
2️⃣ Ejecuta el bot:

```bash
python BiblioTrackBot.py
```

---

## 🛠️ Comandos disponibles

✅ **/start**  
Muestra un mensaje de bienvenida. Si el usuario ya está logeado, muestra el menú con los comandos disponibles.

✅ **/login `<usuario>` `<contraseña>`**  
Inicia sesión con las credenciales de la App Web.

✅ **/logout**  
Cierra la sesión del usuario.

✅ **/buscar `<nombre_libro>`**  
Busca libros disponibles por nombre.

✅ **/reservas**  
Muestra las reservas activas del usuario.

✅ **/prestamos**  
Muestra los préstamos activos del usuario y su estado.

✅ **/que_leer**  
Recibe una recomendación de lectura personalizada según tu historial.

---

## ⚡ Notificaciones automáticas

El bot revisa periódicamente los préstamos activos y envía notificaciones a los usuarios si están a punto de vencer o vencidos.

Configurado para correr cada 24 horas.  
Puedes ajustar el intervalo en `BiblioTrackBot.py`:

```python
scheduler.add_job(lambda: notificar_prestamos(app), 'interval', hours=24)
```

---

## 📝 Observaciones finales

- El bot usa **Markdown** para formatear los mensajes (negritas, cursivas, etc.).
