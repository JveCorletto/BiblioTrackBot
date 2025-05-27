import base64
from telegram import Update
from telegram.ext import ContextTypes
from db.connection import get_db_connection
from handlers.menu import mostrar_menu_logeado

def codificar_base64(texto):
    texto_bytes = texto.encode('utf-16le')
    return base64.b64encode(texto_bytes).decode('utf-8')

def autenticar_usuario(usuario, contrasenia):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed = codificar_base64(contrasenia)
    cursor.execute("SELECT COUNT(*) FROM Usuarios WHERE Usuario = ? AND Contrasenia = ?", (usuario, hashed))
    return cursor.fetchone()[0] > 0

def registrar_telegram_id(usuario, telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Usuarios SET TelegramId = ? WHERE Usuario = ?", (telegram_id, usuario))
    conn.commit()

def cerrar_sesion(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Usuarios SET TelegramId = NULL WHERE TelegramId = ?", (telegram_id,))
    conn.commit()
    return cursor.rowcount > 0

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Uso: /login <usuario> <contraseña>")
        return

    usuario, contrasenia = args
    telegram_id = update.effective_user.id

    if autenticar_usuario(usuario, contrasenia):
        registrar_telegram_id(usuario, telegram_id)
        await update.message.reply_text(f"✅ ¡Bienvenido, {usuario}! Tu sesión está activa.")
        await mostrar_menu_logeado(update)
    else:
        await update.message.reply_text("❌ Usuario o contraseña incorrectos.")

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if cerrar_sesion(user_id):
        await update.message.reply_text("✅ Tu sesión ha sido cerrada exitosamente.")
    else:
        await update.message.reply_text("⚠️ No tenías una sesión activa.")