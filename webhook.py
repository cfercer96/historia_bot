from flask import Flask, request, jsonify
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # Extraer mensaje del cuerpo x-www-form-urlencoded
        user_message = request.form.get("Body", "").strip()
        sender = request.form.get("From", "")

        print("📨 MENSAJE:", user_message)
        print("👤 DE:", sender)

        # Verifica si hay mensaje
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

        # Retorna respuesta simple para Twilio
        return reply, 200

    except Exception as e:
        print("❌ ERROR:", str(e))
        return "Internal Server Error", 500

if __name__ == "__main__":
    app.run(port=5000)
