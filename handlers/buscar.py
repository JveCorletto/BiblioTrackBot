from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.connection import get_db_connection

def usuario_autenticado(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Usuarios WHERE TelegramId = ?", (telegram_id,))
    return cursor.fetchone()[0] > 0

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    if not usuario_autenticado(telegram_id):
        await update.message.reply_text("🚫 Debes iniciar sesión con /login [Usuario] [Contraseña]")
        return

    if not usuario_autenticado(telegram_id):
        await update.message.reply_text("🚫 Debes iniciar sesión primero con /login.")
        return

    if not context.args:
        await update.message.reply_text("📚 Uso correcto: /buscar <palabra_clave>")
        return

    palabra = " ".join(context.args)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT TOP 5 
            l.IdLibro,
            l.Libro,
            l.ISBN,
            l.AnioPublicacion,
            e.Editorial
        FROM Libros l
        JOIN Editoriales e ON l.IdEditorial = e.IdEditorial
        WHERE l.IdEstado = 1
          AND l.Libro LIKE ?
          AND EXISTS (
              SELECT 1 FROM Ejemplares ej
              WHERE ej.IdLibro = l.IdLibro
                AND NOT EXISTS (
                    SELECT 1 FROM Prestamos p
                    WHERE p.IdEjemplar = ej.IdEjemplar
                      AND p.FechaDevolucion IS NULL
                )
          )
    """, (f'%{palabra}%',))

    libros = cursor.fetchall()

    if not libros:
        await update.message.reply_text("❌ No hay libros disponibles con ese criterio.")
        return

    for libro in libros:
        id_libro, nombre, isbn, anio, editorial = libro

        cursor.execute("""
            SELECT a.Autor
            FROM Autores a
            JOIN AutoresLibros al ON al.IdAutor = a.IdAutor
            WHERE al.IdLibro = ?
        """, (id_libro,))
        autores = cursor.fetchall()
        lista_autores = ", ".join([a[0] for a in autores]) if autores else "Desconocido"

        mensaje = (
            f"📖 {nombre}\n"
            f"✍️ Autor(es): {lista_autores}\n"
            f"🏢 Editorial: {editorial} ({anio})\n"
            f"🔢 ISBN: {isbn}\n"
        )

        boton = InlineKeyboardMarkup([[InlineKeyboardButton("📥 Reservar", callback_data=f"reservar_{id_libro}")]])
        await update.message.reply_text(mensaje, reply_markup=boton)

async def handle_reserva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    if not usuario_autenticado(telegram_id):
        await query.edit_message_text("🚫 Debes iniciar sesión para reservar un libro.")
        return

    id_libro = int(query.data.split("_")[1])

    context.user_data["reserva_libro_id"] = id_libro
    context.user_data["esperando_dias"] = True

    await query.edit_message_text("📆 ¿Por cuántos días deseas reservar este libro? (1 a 31)")

async def recibir_dias_reserva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    texto_usuario = update.message.text.strip()

    # 🚫 Si mandó otro comando, cancela la espera
    if texto_usuario.startswith("/"):
        context.user_data["esperando_dias"] = False
        context.user_data["reserva_libro_id"] = None
        await update.message.reply_text("🚫 La reserva ha sido cancelada.")
        return

    if not context.user_data.get("esperando_dias"):
        return  # ignorar si no se pidió

    try:
        dias = int(texto_usuario)
        if dias < 1 or dias > 31:
            await update.message.reply_text("⚠️ Ingresa un número entre 1 y 31.")
            return
    except ValueError:
        await update.message.reply_text("❌ Por favor, escribe un número válido.")
        return

    id_libro = context.user_data.get("reserva_libro_id")
    if not id_libro:
        await update.message.reply_text("❌ Hubo un error. Intentá reservar de nuevo.")
        return

    # limpiar contexto
    context.user_data["esperando_dias"] = False
    context.user_data["reserva_libro_id"] = None

    conn = get_db_connection()
    cursor = conn.cursor()

    # Buscar ejemplar disponible
    cursor.execute("""
        SELECT TOP 1 IdEjemplar
        FROM Ejemplares
        WHERE IdLibro = ?
          AND NOT EXISTS (
            SELECT 1 FROM Prestamos
            WHERE Prestamos.IdEjemplar = Ejemplares.IdEjemplar
              AND FechaDevolucion IS NULL
          )
    """, (id_libro,))
    ejemplar = cursor.fetchone()

    if not ejemplar:
        await update.message.reply_text("❌ No hay ejemplares disponibles.")
        return

    id_ejemplar = ejemplar[0]

    cursor.execute("SELECT IdUsuario FROM Usuarios WHERE TelegramId = ?", (telegram_id,))
    id_usuario = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO Prestamos (
            IdUsuario, IdEjemplar, DiasPrestamo,
            FechaPrestamo, Entregado, Finalizado, IdUsuarioEntrego
        )
        VALUES (?, ?, ?, NULL, 0, 0, NULL)
    """, (id_usuario, id_ejemplar, dias))
    conn.commit()

    await update.message.reply_text(f"✅ ¡Reserva registrada por {dias} día(s)!")