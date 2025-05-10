from flask import Flask, request, Response
from openai import OpenAI
import os
import requests
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DIALOGFLOW_URL = os.getenv("DIALOGFLOW_WEBHOOK_URL")  # Asegúrate de definir esto en tu .env

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        user_message = request.form.get("Body", "").strip()
        sender = request.form.get("From", "")

        print("📨 MENSAJE:", user_message)
        print("👤 DE:", sender)

        if not user_message:
            return "No message received", 400

        # Enviar a Dialogflow
        dialogflow_payload = {
            "queryInput": {
                "text": {
                    "text": user_message,
                    "languageCode": "es"
                }
            },
            "queryParams": {
                "timeZone": "America/Costa_Rica"
            }
        }

        dialogflow_headers = {
            "Content-Type": "application/json"
        }

        dialogflow_response = requests.post(
            DIALOGFLOW_URL,
            json=dialogflow_payload,
            headers=dialogflow_headers
        )

        reply_text = None
        if dialogflow_response.status_code == 200:
            data = dialogflow_response.json()
            fulfillment = data.get("fulfillmentText")
            if fulfillment and "no tengo una respuesta" not in fulfillment.lower():
                reply_text = fulfillment

        # Si Dialogflow no responde adecuadamente, usar OpenAI
        if not reply_text:
            openai_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en historia de Costa Rica."},
                    {"role": "user", "content": user_message}
                ]
            )
            reply_text = openai_response.choices[0].message.content.strip()

        print("🤖 RESPUESTA:", reply_text)

        # Formato Twilio
        twilio_response = MessagingResponse()
        twilio_response.message(reply_text)
        return Response(str(twilio_response), mimetype="application/xml")

    except Exception as e:
        print("❌ ERROR:", str(e))
        return "Internal Server Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

