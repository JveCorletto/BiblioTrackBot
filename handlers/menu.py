from telegram import Update
from db.connection import get_db_connection

async def mostrar_menu_logeado(update: Update):
    telegram_id = update.effective_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Usuario FROM Usuarios WHERE TelegramId = ?", (telegram_id,))
    resultado = cursor.fetchone()
    nombre = resultado[0] if resultado else "Usuario"

    await update.message.reply_text(
        f"🎉 ¡Hola, {nombre}! Aquí están los comandos que puedes usar:\n\n"
        "🔍 /buscar <nombre_libro> - Busca libros disponibles por nombre.\n"
        "📚 /reservas - Consulta tus reservas activas.\n"
        "📖 /prestamos - Revisa tus préstamos activos y su estado.\n"
        "🤖 /que_leer - Recibe una recomendación de lectura personalizada.\n"
        "🚪 /logout - Cierra tu sesión actual.\n\n"
        "¡Disfruta explorando la biblioteca! 📚"
    )

def obtener_nombre_usuario(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Usuario FROM Usuarios WHERE TelegramId = ?", (telegram_id,))
    resultado = cursor.fetchone()
    return resultado[0] if resultado else "Usuario"