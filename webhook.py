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

        # Si Dialogflow responde con un mensaje vacío o no relevante, usar ChatGPT
        if not dialogflow_response or dialogflow_response.strip() == "":
            print("📝 Usando ChatGPT para respuesta")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system", 
                    "content": "Eres un experto en historia de Costa Rica."
                },
                {
                    "role": "user", 
                    "content": user_message
                }]
            )
            reply = response.choices[0].message.content.strip()
        else:
            print("🔍 Respuesta desde Dialogflow:", dialogflow_response)
            reply = dialogflow_response

        print("🤖 RESPUESTA:", reply)

        # Crear respuesta en formato TwiML
        twilio_response = MessagingResponse()
        twilio_response.message(reply)

        return Response(str(twilio_response), mimetype="application/xml")

    except Exception as e:
        print("❌ ERROR:", str(e))
        return "Internal Server Error", 500

# Función para consultar Dialogflow
def query_dialogflow(text, session_id):
    try:
        session = dialogflow_client.session_path(project_id, session_id)
        text_input = dialogflow.TextInput(text=text, language_code="es")
        query_input = dialogflow.QueryInput(text=text_input)

        # Realizar la consulta a Dialogflow
        response = dialogflow_client.detect_intent(session=session, query_input=query_input)

        print("✅ Intent detectado:", response.query_result.intent.display_name)
        print("💬 fulfillment_text:", response.query_result.fulfillment_text)

        # Verificar si Dialogflow proporciona una respuesta válida
        if response.query_result.fulfillment_text:
            return response.query_result.fulfillment_text

        # Si no hay fulfillment_text, buscar en response_messages
        for message in response.query_result.response_messages:
            if message.text and message.text.text:
                return message.text.text[0]

        print("🔴 No se encontró texto de respuesta en fulfillment_text ni en response_messages.")
        return None
    except Exception as e:
        print(f"❌ Error en Dialogflow: {e}")
        return None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
