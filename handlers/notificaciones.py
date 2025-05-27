import asyncio
from datetime import datetime
from db.connection import get_db_connection

def notificar_prestamos(app):
    print("🔁 Ejecutando verificación de préstamos...")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.IdPrestamo, u.TelegramId, l.Libro, p.FechaPrestamo, p.DiasPrestamo
        FROM Prestamos p
        JOIN Usuarios u ON u.IdUsuario = p.IdUsuario
        JOIN Ejemplares e ON e.IdEjemplar = p.IdEjemplar
        JOIN Libros l ON l.IdLibro = e.IdLibro
        WHERE p.Entregado = 1 AND p.Finalizado = 0
        AND ISNULL(p.Notificado, 0) = 0
        AND u.TelegramId IS NOT NULL
    """)

    prestamos = cursor.fetchall()

    for id_prestamo, telegram_id, nombre_libro, fecha_prestamo, dias_prestamo in prestamos:
        if not fecha_prestamo:
            continue  # ignorar reservas sin fecha

        dias_restantes = dias_prestamo - (datetime.now() - fecha_prestamo).days
        print(f"⏳ Revisando préstamo: {nombre_libro}, usuario {telegram_id}, días restantes: {dias_restantes}")

        if dias_restantes == 1:
            mensaje = f"📢 Te queda 1 día para devolver *{nombre_libro}*."
        elif dias_restantes == 0:
            mensaje = f"📢 **Hoy vence** el préstamo de *{nombre_libro}*."
        elif dias_restantes < 0:
            mensaje = f"⚠️ Ya pasaron {-dias_restantes} día(s) desde que venció **{nombre_libro}**."
        else:
            continue  # aún le faltan varios días

        # 🚫 Ya no pasamos loop externo, usamos el del bot
        asyncio.run_coroutine_threadsafe(enviar_mensaje(app, telegram_id, mensaje), app.bot.loop)

        cursor.execute("UPDATE Prestamos SET Notificado = 1 WHERE IdPrestamo = ?", (id_prestamo,))
        conn.commit()

async def enviar_mensaje(app, chat_id, texto):
    try:
        await app.bot.send_message(chat_id=chat_id, text=texto, parse_mode="Markdown")
    except Exception as e:
        print(f"Error enviando a {chat_id}: {e}")