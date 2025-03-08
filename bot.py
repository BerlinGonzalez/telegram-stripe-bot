# Código para crear requirements.txt en Railway si no existe
with open("requirements.txt", "w") as f:
    f.write("python-telegram-bot\nflask\nstripe\nrequests\n")

import os
os.system("pip install -r requirements.txt")


import os
import stripe
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from flask import Flask, request, jsonify
import random
import time

# Configuración de Stripe
stripe.api_key = "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"
WEBHOOK_SECRET = "whsec_MHxLNtkVgtZBBJVEcbNGei2uoktiSQdD"

# Configuración de Telegram
BOT_TOKEN = "7779693447:AAES3qtISilvtOKjQ9oonph918LBQ7odt_I"
bot = telegram.Bot(token=BOT_TOKEN)

# Lista de cuentas de entrega en Fortnite
FORTNITE_ACCOUNTS = [f"BerlinGonzalez{i}" for i in range(1, 46)]

# Base de datos temporal de productos
PRODUCTS = {
    "skin1": {"name": "Skin Épica", "price": 5.99, "stripe_price_id": "stripe_price_id_1"},
    "emote1": {"name": "Emote Exclusivo", "price": 3.99, "stripe_price_id": "stripe_price_id_2"},
}

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
        
        # Seleccionar una cuenta de entrega aleatoria
        delivery_account = random.choice(FORTNITE_ACCOUNTS)
        
        # Simulación de entrega automática (esto debe ser manejado por un bot en Fortnite o manualmente)
        time.sleep(5)  # Simula tiempo de entrega
        
        # Enviar mensaje de confirmación en Telegram
        bot.send_message(chat_id=user_id, text=f"✅ Pago recibido para {product_name}. \nTu regalo será enviado desde la cuenta: {delivery_account}. \nAsegúrate de haber aceptado la solicitud de amistad en Fortnite.")
    
    return jsonify(success=True)

# Función para mostrar productos
def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton(f"{p['name']} - ${p['price']}", callback_data=k)]
        for k, p in PRODUCTS.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Elige un producto:", reply_markup=reply_markup)

# Función para manejar la selección de productos
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    product_key = query.data
    product = PRODUCTS[product_key]
    
    query.message.reply_text("Por favor, envíame tu nombre de usuario en Fortnite para continuar.")
    context.user_data["product"] = product
    context.user_data["awaiting_username"] = True
    query.answer()

# Capturar el nombre de usuario de Fortnite
def username_handler(update: Update, context: CallbackContext) -> None:
    if "awaiting_username" in context.user_data and context.user_data["awaiting_username"]:
        fortnite_username = update.message.text
        product = context.user_data["product"]
        
        # Crear sesión de pago en Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": product["stripe_price_id"],
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://tu-web.com/success",
            cancel_url="https://tu-web.com/cancel",
            metadata={"user_id": update.message.chat_id, "product_name": product["name"], "fortnite_username": fortnite_username},
        )
        
        update.message.reply_text(f"Compra {product['name']} aquí: {session.url}")
        context.user_data["awaiting_username"] = False

# Configurar el bot
def main():
    from telegram.ext import Application

updater = Application.builder().token(BOT_TOKEN).build()

    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.text & ~telegram.ext.Filters.command, username_handler))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

import time

while True:
    time.sleep(10)  # Evita que el proceso se cierre inmediatamente
