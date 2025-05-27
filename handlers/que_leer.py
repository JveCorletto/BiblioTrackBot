import os
import random
from dotenv import load_dotenv
from telegram.ext import ContextTypes
from db.connection import get_db_connection
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
import google.generativeai as genai

# Cargar variables de entorno
load_dotenv()

# Inicializar Gemini con la API Key
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

def usuario_autenticado(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Usuarios WHERE TelegramId = ?", (telegram_id,))
    return cursor.fetchone()[0] > 0

async def que_leer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    
    if not usuario_autenticado(telegram_id):
        await update.message.reply_text("🚫 Debes iniciar sesión con /login [Usuario] [Contraseña]")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener usuario
    cursor.execute("SELECT IdUsuario FROM Usuarios WHERE TelegramId = ?", (telegram_id,))
    usuario = cursor.fetchone()
    if not usuario:
        await update.message.reply_text("🚫 Debes iniciar sesión para obtener recomendaciones.")
        return
    id_usuario = usuario[0]

    # Obtener historial de préstamos finalizados
    cursor.execute("""
        SELECT l.ISBN, l.Libro, g.Genero, e.Editorial
        FROM Prestamos p
        JOIN Ejemplares ej ON p.IdEjemplar = ej.IdEjemplar
        JOIN Libros l ON ej.IdLibro = l.IdLibro
        LEFT JOIN Editoriales e ON l.IdEditorial = e.IdEditorial
        LEFT JOIN GenerosLibros gl ON gl.IdLibro = l.IdLibro
        LEFT JOIN GenerosLiterarios g ON g.IdGenero = gl.IdGenero
        WHERE p.IdUsuario = ? AND p.Finalizado = 1
    """, (id_usuario,))
    historial = cursor.fetchall()
    historial_formateado = "\n".join(
        [f"- {libro} ({genero if genero else 'Género desconocido'}, {editorial if editorial else 'Editorial desconocida'})"
         for _, libro, genero, editorial in historial]
    ) if historial else "No hay historial disponible."

    # Obtener lista de libros no leídos con ejemplares disponibles
    cursor.execute("""
        SELECT DISTINCT l.ISBN, l.Libro, a.Autor, e.Editorial
        FROM Libros l
        LEFT JOIN Editoriales e ON l.IdEditorial = e.IdEditorial
        LEFT JOIN AutoresLibros al ON al.IdLibro = l.IdLibro
        LEFT JOIN Autores a ON a.IdAutor = al.IdAutor
        WHERE l.ISBN NOT IN (
            SELECT l2.ISBN
            FROM Prestamos p
            JOIN Ejemplares ej ON p.IdEjemplar = ej.IdEjemplar
            JOIN Libros l2 ON ej.IdLibro = l2.IdLibro
            WHERE p.IdUsuario = ? AND p.Finalizado = 1
        )
        AND EXISTS (
            SELECT 1
            FROM Ejemplares e2
            WHERE e2.IdLibro = l.IdLibro
              AND e2.IdEjemplar NOT IN (
                  SELECT p2.IdEjemplar
                  FROM Prestamos p2
                  WHERE p2.FechaDevolucion IS NULL
              )
        )
    """, (id_usuario,))
    disponibles = cursor.fetchall()

    if not disponibles:
        await update.message.reply_text("📭 No hay libros disponibles nuevos para recomendarte en este momento.")
        return

    # Elegir uno aleatoriamente
    isbn_elegido, titulo, autor, editorial = random.choice(disponibles)

    # Confirmar que aún hay ejemplares disponibles en tiempo real
    cursor.execute("""
        SELECT TOP 1 e.IdEjemplar
        FROM Ejemplares e
        JOIN Libros l ON e.IdLibro = l.IdLibro
        WHERE l.ISBN = ?
        AND e.IdEjemplar NOT IN (
            SELECT p.IdEjemplar
            FROM Prestamos p
            WHERE p.FechaDevolucion IS NULL
        )
    """, (isbn_elegido,))
    ejemplar_disponible = cursor.fetchone()
    if not ejemplar_disponible:
        # Reintentar con otro libro disponible
        disponibles = [d for d in disponibles if d[0] != isbn_elegido]
        if not disponibles:
            await update.message.reply_text("⚠️ No hay ejemplares disponibles en este momento. Intenta más tarde.")
            return
        isbn_elegido, titulo, autor, editorial = random.choice(disponibles)

    cursor.execute("SELECT IdLibro FROM Libros WHERE ISBN = ?", (isbn_elegido,))
    id_libro = cursor.fetchone()[0]

    # Avisar que está generando
    await update.message.reply_text("⏳ Estoy generando tu recomendación, por favor espera un momento...")

    # Prompt a Gemini para motivo y sinopsis
    prompt = f"""
El usuario ha leído antes:
{historial_formateado}

Este es el libro que se recomienda:
- ISBN: {isbn_elegido}
- Título: {titulo}
- Autor: {autor if autor else 'Desconocido'}
- Editorial: {editorial if editorial else 'Desconocida'}

Genera SOLO esto:
Motivo: Una breve frase explicando por qué le puede gustar.
Sinopsis: Una breve sinopsis atractiva.
"""
    response = model.generate_content(prompt)
    texto_respuesta = response.text.strip()

    # Parsear respuesta
    lineas = texto_respuesta.split("\n")
    motivo = None
    sinopsis = None
    for linea in lineas:
        if "Motivo:" in linea:
            motivo = linea.split("Motivo:")[1].strip()
        elif "Sinopsis:" in linea:
            sinopsis = linea.split("Sinopsis:")[1].strip()

    if not motivo or not sinopsis:
        await update.message.reply_text("⚠️ Hubo un problema generando la recomendación. Intentá de nuevo.")
        return

    # Mensaje final con botón de reservar
    mensaje = (
        f"🔎 _{motivo}_\n\n"
        f"📚 *Recomendación personalizada*:\n\n"
        f"📖 *{titulo}*\n"
        f"✍️ Autor: _{autor if autor else 'Desconocido'}_\n"
        f"🏢 Editorial: _{editorial if editorial else 'Desconocida'}_\n\n"
        f"📝 Sinopsis:\n_{sinopsis}_"
    )
    
    keyboard = [
        [InlineKeyboardButton("📚 Reservar este libro", callback_data=f"reservar_{id_libro}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mensaje, parse_mode="Markdown", reply_markup=reply_markup)