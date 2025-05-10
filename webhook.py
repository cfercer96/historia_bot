from flask import Flask, request, Response
from openai import OpenAI
import os
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import dialogflow_v2 as dialogflow
from google.oauth2 import service_account
import json

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Cargar credenciales de Dialogflow desde variable de entorno JSON
service_account_info = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
dialogflow_credentials = service_account.Credentials.from_service_account_info(service_account_info)
dialogflow_client = dialogflow.SessionsClient(credentials=dialogflow_credentials)
project_id = os.getenv("DIALOGFLOW_PROJECT_ID")
session_id = "unique-session-id"

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

        # Llamada a Dialogflow
        dialogflow_response = query_dialogflow(user_message)

        # Si Dialogflow responde, usar esa respuesta
        if dialogflow_response:
            reply = dialogflow_response
        else:
            # Si Dialogflow no responde, usar OpenAI (ChatGPT)
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

# Función para consultar Dialogflow
def query_dialogflow(text):
    try:
        session = dialogflow_client.session_path(project_id, session_id)
        text_input = dialogflow.TextInput(text=text, language_code="es")
        query_input = dialogflow.QueryInput(text=text_input)

        response = dialogflow_client.detect_intent(session=session, query_input=query_input)
        
        # Si Dialogflow tiene una respuesta, devolverla
        if response.query_result.fulfillment_text:
            return response.query_result.fulfillment_text
        else:
            return None
    except Exception as e:
        print(f"❌ Error en Dialogflow: {e}")
        return None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

