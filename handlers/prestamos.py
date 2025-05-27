from telegram import Update
from datetime import datetime
from telegram.ext import ContextTypes
from db.connection import get_db_connection

def usuario_autenticado(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Usuarios WHERE TelegramId = ?", (telegram_id,))
    return cursor.fetchone()[0] > 0

async def prestamos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    
    if not usuario_autenticado(telegram_id):
        await update.message.reply_text("🚫 Debes iniciar sesión con /login [Usuario] [Contraseña]")
        return

    # Validar sesión
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT IdUsuario FROM Usuarios WHERE TelegramId = ?", (telegram_id,))
    usuario = cursor.fetchone()

    if not usuario:
        await update.message.reply_text("🚫 Debes iniciar sesión para ver tus préstamos.")
        return

    id_usuario = usuario[0]

    # Traer préstamos activos
    cursor.execute("""
        SELECT p.DiasPrestamo, p.FechaPrestamo, l.Libro
        FROM Prestamos p
        JOIN Ejemplares e ON p.IdEjemplar = e.IdEjemplar
        JOIN Libros l ON e.IdLibro = l.IdLibro
        WHERE p.IdUsuario = ?
          AND p.Entregado = 1
          AND p.Finalizado = 0
    """, (id_usuario,))

    prestamos = cursor.fetchall()

    if not prestamos:
        await update.message.reply_text("📭 No tienes préstamos activos en este momento.")
        return

    mensaje = "📚 *Tus préstamos activos:*\n\n"

    for dias_prestamo, fecha_prestamo, nombre_libro in prestamos:
        if not fecha_prestamo:
            estado = "⏳ Pendiente de entrega"
            dias_restantes = "N/D"
        else:
            hoy = datetime.now()
            dias_transcurridos = (hoy - fecha_prestamo).days
            dias_restantes = dias_prestamo - dias_transcurridos
            estado = "🟢 A tiempo" if dias_restantes >= 0 else "🔴 Demorado"

        mensaje += (
            f"📖 *{nombre_libro}*\n"
            f"📅 Fecha préstamo: {fecha_prestamo.strftime('%Y-%m-%d') if fecha_prestamo else 'Pendiente'}\n"
            f"⏳ Días restantes: {dias_restantes if dias_restantes != 'N/D' else '---'}\n"
            f"🔎 Estado: {estado}\n\n"
        )

    await update.message.reply_text(mensaje, parse_mode="Markdown")