import os
import asyncio
from telegram import Update
from dotenv import load_dotenv
from telegram.ext import MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

from handlers.que_leer import que_leer
from handlers.reservas import reservas
from handlers.prestamos import prestamos
from handlers.login import login, logout
from db.connection import get_db_connection
from handlers.menu import mostrar_menu_logeado
from handlers.notificaciones import notificar_prestamos
from handlers.buscar import buscar, handle_reserva, recibir_dias_reserva

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
app = ApplicationBuilder().token(TOKEN).read_timeout(60).write_timeout(60).build()

def usuario_autenticado(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Usuarios WHERE TelegramId = ?", (telegram_id,))
    return cursor.fetchone()[0] > 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    if usuario_autenticado(telegram_id):
        await mostrar_menu_logeado(update)
    else:
        await update.message.reply_text(
            "👋 ¡Hola! Soy el bot de BiblioTrack 📚\n\n"
            "Para comenzar a usar todas las funcionalidades, por favor inicia sesión con el comando /login.\n"
            "Puedes usar tus credenciales de la App Web para autenticarte aquí.\n\n"
            "¡Estoy listo para ayudarte a explorar la biblioteca! 📚✨"
        )

# Comandos
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("login", login))
app.add_handler(CommandHandler("logout", logout))
app.add_handler(CommandHandler("buscar", buscar))
app.add_handler(CommandHandler("prestamos", prestamos))
app.add_handler(CommandHandler("reservas", reservas))
app.add_handler(CommandHandler("que_leer", que_leer))

# Acciones con botones
app.add_handler(CallbackQueryHandler(handle_reserva, pattern="^reservar_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_dias_reserva))

# Envío de Notificaciones
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: notificar_prestamos(app), 'interval', hours=24)
scheduler.start()

print("✅🤖 ¡Bot de Telegram Corriendo Exitosamente! 🤖✅\n"
      "❌ 0 Errores \n"
      "⚠️ 0 Warnings")

app.run_polling()