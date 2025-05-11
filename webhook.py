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
service_account_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
service_account_info = json.loads(service_account_json)

# Corregir el formato del private_key reemplazando '\n' por saltos reales
service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

# Crear las credenciales de Dialogflow
dialogflow_credentials = service_account.Credentials.from_service_account_info(service_account_info)
dialogflow_client = dialogflow.SessionsClient(credentials=dialogflow_credentials)

project_id = os.getenv("DIALOGFLOW_PROJECT_ID")

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # Extraer mensaje y número del remitente
        user_message = request.form.get("Body", "").strip()
        sender = request.form.get("From", "").strip()  # Ej: "whatsapp:+50687354933"

        print("📨 MENSAJE:", user_message)
        print("👤 DE:", sender)

        if not user_message:
            return "No message received", 400

        # Usar el número como session_id (sin el prefijo "whatsapp:")
        session_id = sender.replace("whatsapp:", "")

        # Llamada a Dialogflow
        dialogflow_response = query_dialogflow(user_message, session_id)

        # Si Dialogflow responde con algo válido, usar esa respuesta
        if dialogflow_response:
            print("🔍 Respuesta desde Dialogflow:", dialogflow_response)
            reply = dialogflow_response
        else:
            # Si Dialogflow no tiene respuesta válida, usar OpenAI
            print("📝 Usando ChatGPT para respuesta")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages

