import os
import stripe
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler
from flask import Flask, request, jsonify
import random
import time
import requests
import json

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
        items = data.get("shop", [])
        return {item.get('displayName', 'Desconocido'): item for item in items}
    return {}

PRODUCTS = get_fortnite_items()

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
def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton(f"{name} - {item['finalPrice']} V-Bucks", callback_data=name)]
        for name, item in PRODUCTS.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Elige un producto de la tienda Fortnite:", reply_markup=reply_markup)

# Función para manejar la selección de productos
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    product_name = query.data
    product = PRODUCTS.get(product_name)
    
    query.message.reply_text("Por favor, envíame tu nombre de usuario en Fortnite para continuar.")
    context.user_data["product"] = product
    context.user_data["awaiting_username"] = True
    query.answer()

# Capturar el nombre de usuario de Fortnite
def username_handler(update: Update, context: CallbackContext) -> None:
    if "awaiting_username" in context.user_data and context.user_data["awaiting_username"]:
        fortnite_username = update.message.text
        product = context.user_data["product"]
        
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": product["displayName"]},
                    "unit_amount": product["finalPrice"] * 100,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://tu-web.com/success",
            cancel_url="https://tu-web.com/cancel",
            metadata={"user_id": update.message.chat_id, "product_name": product["displayName"], "fortnite_username": fortnite_username},
        )
        
        update.message.reply_text(f"Compra {product['displayName']} aquí: {session.url}")
        context.user_data["awaiting_username"] = False

# Configurar el bot
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(MessageEntity.TEXT, username_handler))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
