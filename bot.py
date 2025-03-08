import os
import stripe
import requests
import random
import threading
import time
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Configuración de API
FORTNITE_API_KEY = os.getenv("FORTNITE_API_KEY")
FORTNITE_API_URL = "https://fortniteapi.io/v2/shop?lang=es"

# Configuración de Stripe
stripe.api_key = os.getenv("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")
WEBHOOK_SECRET = os.getenv("whsec_MHxLNtkVgtZBBJVEcbNGei2uoktiSQdD")

# Configuración de Telegram
BOT_TOKEN = os.getenv("7779693447:AAES3qtISilvtOKjQ9oonph918LBQ7odt_I")

# Lista de cuentas de entrega en Fortnite
FORTNITE_ACCOUNTS = [f"BerlinGonzalez{i}" for i in range(1, 46)]

# Servidor Flask para recibir webhooks de Stripe
app = Flask(__name__)

def obtener_items_fortnite():
    headers = {"Authorization": FORTNITE_API_KEY}
    response = requests.get(FORTNITE_API_URL, headers=headers)
    if response.status_code == 200:
        return response.json().get("shop", [])
    return []

@app.route("/stripe_webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception as e:
        return jsonify(success=False)
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]
        product_name = session["metadata"]["product_name"]
        
        delivery_account = random.choice(FORTNITE_ACCOUNTS)
        
        application.bot.send_message(chat_id=user_id, text=f"✅ Pago recibido para {product_name}. \nTu regalo será enviado desde la cuenta: {delivery_account}. \nAsegúrate de haber aceptado la solicitud de amistad en Fortnite.")
    
    return jsonify(success=True)

# Inicializar aplicación de Telegram
application = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = obtener_items_fortnite()
    keyboard = []
    
    for item in items[:10]:  # Mostrar solo los primeros 10 ítems
        nombre = item.get("displayName", "Sin nombre")
        precio = item.get("price", {}).get("finalPrice", "N/A")
        key = item.get("mainId", "0")  # ID único del ítem
        keyboard.append([InlineKeyboardButton(f"{nombre} - {precio} V-Bucks", callback_data=key)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Elige un producto de la tienda Fortnite:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Responde inmediatamente para evitar que Telegram quede cargando
    item_id = query.data  # ID del ítem seleccionado
    items = obtener_items_fortnite()
    
    item = next((i for i in items if i.get("mainId") == item_id), None)
    
    if not item:
        await query.message.reply_text("Este ítem ya no está disponible.")
        return
    
    nombre = item.get("displayName", "Sin nombre")
    precio_vbucks = item.get("price", {}).get("finalPrice", 0)
    precio_usd = precio_vbucks * 0.01  # Convertimos V-Bucks a dólares (ejemplo)
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": nombre},
                    "unit_amount": int(precio_usd * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://tu-web.com/success",
            cancel_url="https://tu-web.com/cancel",
            metadata={"user_id": query.message.chat_id, "product_name": nombre},
        )
        
        await query.message.reply_text(f"Compra {nombre} aquí: {session.url}")
    except Exception as e:
        await query.message.reply_text("⚠️ Error al generar el pago. Inténtalo de nuevo más tarde.")
        print("Error en Stripe:", e)

def keep_awake():
    while True:
        try:
            requests.get("https://tu-bot.railway.app")
        except Exception as e:
            print("Error manteniendo activo:", e)
        time.sleep(300)

threading.Thread(target=keep_awake, daemon=True).start()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))

if __name__ == "__main__":
    print("Bot iniciado...")
    application.run_polling()
