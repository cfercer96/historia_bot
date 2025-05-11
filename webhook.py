from flask import Flask, request, Response
from openai import OpenAI
import os
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import dialogflow_v2 as dialogflow
from google.oauth2 import service_account
import json
import logging

# Configurar logging para que los prints aparezcan en los logs de Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Cargar credenciales de Dialogflow desde variable de entorno JSON
service_account_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
service_account_info = json.loads(service_account_json)
service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

# Crear las credenciales de Dialogflow
dialogflow_credentials = service_account.Credentials.from_service_account_info(service_account_info)
dialogflow_client = dialogflow.SessionsClient(credentials=dialogflow_credentials)

project_id = os.getenv("DIALOGFLOW_PROJECT_ID")

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        user_message = request.form.get("Body", "").strip()
        sender = request.form.get("From", "").strip()

        logger.info(f"📨 MENSAJE: {user_message}")
        logger.info(f"👤 DE: {sender}")

        if not user_message:
            return "No message received", 400

        session_id = sender.replace("whatsapp:", "")
        dialogflow_response = query_dialogflow(user_message, session_id)

        if dialogflow_response:
            logger.info(f"🔍 Respuesta desde Dialogflow: {dialogflow_response}")
            reply = dialogflow_response
        else:
            logger.info("📝 Usando ChatGPT para respuesta")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en historia de Costa Rica."},
                    {"role": "user", "content": user_message}
                ]
            )
            reply = response.choices[0].message.content.strip()

        logger.info(f"🤖 RESPUESTA: {reply}")

        twilio_response = MessagingResponse()
        twilio_response.message(reply)

        return Response(str(twilio_response), mimetype="application/xml")

    except Exception as e:
        logger.error(f"❌ ERROR en webhook: {str(e)}")
        return "Internal Server Error", 500

# Función para consultar Dialogflow
def query_dialogflow(text, session_id):
    try:
        session = dialogflow_client.session_path(project_id, session_id)
        text_input = dialogflow.TextInput(text=text, language_code="es")
        query_input = dialogflow.QueryInput(text=text_input)
        response = dialogflow_client.detect_intent(session=session, query_input=query_input)

        intent = response.query_result.intent
        fulfillment = response.query_result.fulfillment_text.strip() if response.query_result.fulfillment_text else ""

        logger.info(f"✅ Intent detectado: {intent.display_name}")
        logger.info(f"💬 fulfillment_text: {fulfillment}")

        # Si es fallback o no tiene respuesta, usar ChatGPT
        if intent.is_fallback or not fulfillment:
            logger.warning("⚠️ Intent sin respuesta útil. Usando ChatGPT.")
            return None

        return fulfillment

    except Exception as e:
        logger.error(f"❌ Error en Dialogflow: {e}")
        return None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
