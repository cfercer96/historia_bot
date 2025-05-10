from flask import Flask, request, jsonify
from dotenv import load_dotenv
from twilio.rest import Client
from openai import OpenAI
import os

load_dotenv()

app = Flask(__name__)

# Twilio
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
twilio_client = Client(twilio_sid, twilio_token)

# OpenAI client (nuevo formato compatible con SDK >=1.0.0)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        body = request.get_json()
        print("📦 BODY:", body)

        user_message = body["queryResult"]["queryText"]
        fulfillment_text = body["queryResult"].get("fulfillmentText", "").strip()
        phone_number = body["originalDetectIntentRequest"]["payload"]["data"].get("From", "")

        print("📨 Mensaje del usuario:", user_message)
        print("🤖 Respuesta de Dialogflow:", fulfillment_text)

        # Si Dialogflow no tiene respuesta útil, usar ChatGPT
        if not fulfillment_text or "no entiendo" in fulfillment_text.lower():
            print("⚠️ Dialogflow sin respuesta válida. Consultando a OpenAI...")
            completion = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en historia de Costa Rica."},
                    {"role": "user", "content": user_message}
                ]
            )
            fulfillment_text = completion.choices[0].message.content.strip()

        # Enviar mensaje de vuelta por WhatsApp
        message = twilio_client.messages.create(
            body=fulfillment_text,
            from_=f"whatsapp:{twilio_phone_number}",
            to=phone_number
        )

        print("✅ Mensaje enviado:", message.sid)
        return "OK", 200

    except Exception as e:
        print("❌ ERROR:", str(e))
        return "Internal Server Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

