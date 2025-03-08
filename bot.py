import os
import stripe
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request, jsonify
import random
import threading
import requests
import time

# Configuración de Stripe
stripe.api_key = "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"
WEBHOOK_SECRET = "whsec_MHxLNtkVgtZBBJVEcbNGei2uoktiSQdD"

# Configuración de Telegram
BOT_TOKEN = "7779693447:AAES3qtISilvtOKjQ9oonph918LBQ7odt_I"

# Lista de cuentas de entrega en Fortnite
FORTNITE_ACCOUNTS = [f"BerlinGonzalez{i}" for i in range(1, 46)]

# Base de datos de productos
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
        
        delivery_account = random.choice(FORTNITE_ACCOUNTS)
        
        # Simulación de entrega automática
        time.sleep(5)
        
        # Enviar mensaje de confirmación en Telegram
        application.bot.send_message(chat_id=user_id, text=f"✅ Pago recibido para {product_name}. \nTu regalo será enviado desde la cuenta: {delivery_account}. \nAsegúrate de haber aceptado la solicitud de amistad en Fortnite.")
    
    return jsonify(success=True)

# Inicializar aplicación de Telegram
application = Application.builder().token(BOT_TOKEN).build()

# Manejar comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"{p['name']} - ${p['price']}", callback_data=k)]
        for k, p in PRODUCTS.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Elige un producto:", reply_markup=reply_markup)

# Manejar selección de productos
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    product_key = query.data
    product = PRODUCTS[product_key]
    
    await query.message.reply_text("Por favor, envíame tu nombre de usuario en Fortnite para continuar.")
    context.user_data["product"] = product
    context.user_data["awaiting_username"] = True
    await query.answer()

# Capturar nombre de usuario de Fortnite
async def username_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "awaiting_username" in context.user_data and context.user_data["awaiting_username"]:
        fortnite_username = update.message.text
        product = context.user_data["product"]
        
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
        
        await update.message.reply_text(f"Compra {product['name']} aquí: {session.url}")
        context.user_data["awaiting_username"] = False

# Mantener Railway despierto
RAILWAY_APP_URL = "https://tu-bot.railway.app"
def keep_awake():
    while True:
        try:
            requests.get(RAILWAY_APP_URL)
        except Exception as e:
            print("Error manteniendo activo:", e)
        time.sleep(300)
threading.Thread(target=keep_awake, daemon=True).start()

# Configurar manejadores de Telegram
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, username_handler))

# Ejecutar bot
if __name__ == "__main__":
    print("Bot iniciado...")
    application.run_polling()
