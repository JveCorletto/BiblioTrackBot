from telegram import Update
from telegram.ext import ContextTypes
from db.connection import get_db_connection

def usuario_autenticado(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Usuarios WHERE TelegramId = ?", (telegram_id,))
    return cursor.fetchone()[0] > 0

async def reservas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    if not usuario_autenticado(telegram_id):
        await update.message.reply_text("🚫 Debes iniciar sesión con /login [Usuario] [Contraseña]")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT IdUsuario FROM Usuarios WHERE TelegramId = ?", (telegram_id,))
    usuario = cursor.fetchone()

    if not usuario:
        await update.message.reply_text("🚫 Debes iniciar sesión para ver tus reservas.")
        return

    id_usuario = usuario[0]

    cursor.execute("""
        SELECT l.Libro, p.DiasPrestamo
        FROM Prestamos p
        JOIN Ejemplares e ON e.IdEjemplar = p.IdEjemplar
        JOIN Libros l ON l.IdLibro = e.IdLibro
        WHERE p.IdUsuario = ?
          AND p.Entregado = 0
          AND p.FechaPrestamo IS NULL
          AND p.Finalizado = 0
    """, (id_usuario,))

    reservas = cursor.fetchall()

    if not reservas:
        await update.message.reply_text("📭 No tienes reservas pendientes.")
        return

    mensaje = "📌 *Tus reservas pendientes:*\n\n"
    for libro, dias in reservas:
        mensaje += (
            f"📖 {libro}\n"
            f"📅 Estado: Reserva pendiente de entrega ⏳\n"
            f"🗓️ Plazo solicitado: {dias} días\n\n"
        )

    await update.message.reply_text(mensaje, parse_mode="Markdown")