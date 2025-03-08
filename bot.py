import os
import stripe
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes
from flask import Flask, request, jsonify
import random
import time
import requests
import json
import asyncio

# Cargar variables de entorno
BOT_TOKEN = os.getenv("BOT_TOKEN")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
FORTNITE_API_KEY = os.getenv("FORTNITE_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

if not BOT_TOKEN:
    raise ValueError("🚨 ERROR: BOT_TOKEN no está configurado en Railway.")
if not STRIPE_SECRET_KEY:
    raise ValueError("🚨 ERROR: STRIPE_SECRET_KEY no está configurado en Railway.")
if not FORTNITE_API_KEY:
    raise ValueError("🚨 ERROR: FORTNITE_API_KEY no está configurado en Railway.")
if not WEBHOOK_SECRET:
    raise ValueError("🚨 ERROR: WEBHOOK_SECRET no está configurado en Railway.")

# Configuración de Stripe
stripe.api_key = STRIPE_SECRET_KEY

# Configuración de Telegram
bot = telegram.Bot(token=BOT_TOKEN)

# Lista de cuentas de entrega en Fortnite
FORTNITE_ACCOUNTS = [f"BerlinGonzalez{i}" for i in range(1, 46)]

# Obtener ítems de la tienda de Fortnite
def get_fortnite_items():
    url = "https://fortniteapi.io/v2/shop?lang=es"
    headers = {"Authorization": FORTNITE_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("DEBUG: Datos recibidos de la API:", data)  # Debugging
        items = data.get("shop", [])
        print("DEBUG: Items extraídos:", items)  # Debugging
        return {
            item.get('displayName', 'Desconocido'): {
                'name': item.get('displayName', 'Desconocido'),
                'price': item.get('price', 'N/A')
            }
            for item in items
        }
    return {}

PRODUCTS = get_fortnite_items()
print("DEBUG: Productos cargados:", PRODUCTS)  # Debugging

# Obtener información de Fortnite Crew
def get_fortnite_crew():
    url = "https://fortniteapi.io/v2/crew?lang=es"
    headers = {"Authorization": FORTNITE_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {}

# Servidor Flask para recibir webhooks de Stripe
app = Flask(__name__)

@app.route("/stripe_webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception as e:
        return jsonify(success=False)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]
        product_name = session["metadata"]["product_name"]
        fortnite_username = session["metadata"]["fortnite_username"]
        
        delivery_account = random.choice(FORTNITE_ACCOUNTS)
        time.sleep(5)  # Simula tiempo de entrega
        
        bot.send_message(chat_id=user_id, text=f"✅ Pago recibido para {product_name}. \nTu regalo será enviado desde la cuenta: {delivery_account}. \nAsegúrate de haber aceptado la solicitud de amistad en Fortnite.")
    
    return jsonify(success=True)

# Función para mostrar productos
def chunk_list(lst, n):
    """Divide una lista en partes de tamaño n."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not PRODUCTS:
        await update.message.reply_text("No hay productos disponibles en la tienda en este momento.")
        return
    
    product_buttons = [
        InlineKeyboardButton(f"{item['name']} - {item['price']} V-Bucks", callback_data=name)
        for name, item in PRODUCTS.items()
    ]
    
    # Dividimos los botones en partes más pequeñas
    button_chunks = list(chunk_list(product_buttons, 5))  # Máximo 5 por fila
    
    for chunk in button_chunks:
        reply_markup = InlineKeyboardMarkup([chunk])
        await update.message.reply_text("Elige un producto de la tienda Fortnite:", reply_markup=reply_markup)

# Función para manejar botones de callback
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(f"Seleccionaste: {query.data}")

# Función para mostrar Fortnite Crew
async def fortnite_crew(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    crew_info = get_fortnite_crew()
    if crew_info:
        crew_data = crew_info.get('crew', {})
        message = f"🎮 Fortnite Crew:\n{crew_data.get('title', 'No disponible')}\n\n💰 Precio: {crew_data.get('price', 'No disponible')}\n🎁 Recompensas: {crew_data.get('description', 'No disponible')}"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("No se pudo obtener información sobre Fortnite Crew en este momento.")

# Configurar el bot
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("crew", fortnite_crew))
    application.add_handler(CallbackQueryHandler(button))
    
    application.run_polling()

if __name__ == "__main__":
    main()
