from flask import Flask, request, Response
from openai import OpenAI
import os
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # Extraer mensaje del cuerpo x-www-form-urlencoded (como Twilio lo manda)
        user_message = request.form.get("Body", "").strip()
        sender = request.form.get("From", "")

        print("📨 MENSAJE:", user_message)
        print("👤 DE:", sender)

        if not user_message:
            return "No message received", 400

        # Procesar con OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un experto en historia de Costa Rica."},
                {"role": "user", "content": user_message}
            ]
        )

        reply = response.choices[0].message.content.strip()
        print("🤖 RESPUESTA:", reply)

        # Crear respuesta en formato TwiML (XML que Twilio espera)
        twilio_response = MessagingResponse()
        twilio_response.message(reply)

        return Response(str(twilio_response), mimetype="application/xml")

    except Exception as e:
        print("❌ ERROR:", str(e))
        return "Internal Server Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
