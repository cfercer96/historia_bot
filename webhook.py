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
service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

dialogflow_credentials = service_account.Credentials.from_service_account_info(service_account_info)
dialogflow_client = dialogflow.SessionsClient(credentials=dialogflow_credentials)
project_id = os.getenv("DIALOGFLOW_PROJECT_ID")

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        user_message = request.form.get("Body", "").strip()
        sender = request.form.get("From", "").strip()  # Ej: "whatsapp:+50687354933"

        print("📨 MENSAJE:", user_message, flush=True)
        print("👤 DE:", sender, flush=True)

        if not user_message:
            print("⚠️ Mensaje vacío recibido.", flush=True)
            return "No message received", 400

        session_id = sender.replace("whatsapp:", "")

        # Llamada a Dialogflow y retorno de intent + respuesta
        intent_name, dialogflow_response = query_dialogflow(user_message, session_id)

        if not dialogflow_response or intent_name == "Default Fallback Intent":
            print("📝 Usando ChatGPT para respuesta", flush=True)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "Eres un experto en historia de Costa Rica."},
                          {"role": "user", "content": user_message}]
            )
            reply = response.choices[0].message.content.strip()
        else:
            print("🔍 Respuesta desde Dialogflow:", dialogflow_response, flush=True)
            reply = dialogflow_response

        print("🤖 RESPUESTA:", reply, flush=True)

        twilio_response = MessagingResponse()
        twilio_response.message(reply)
        print("📤 XML enviado a Twilio:", str(twilio_response), flush=True)
        return Response(str(twilio_response), mimetype="application/xml")

    except Exception as e:
        print("❌ ERROR:", str(e), flush=True)
        return "Internal Server Error", 500

def query_dialogflow(text, session_id):
    try:
        session = dialogflow_client.session_path(project_id, session_id)
        text_input = dialogflow.TextInput(text=text, language_code="es")
        query_input = dialogflow.QueryInput(text=text_input)

        response = dialogflow_client.detect_intent(session=session, query_input=query_input)

        intent_name = response.query_result.intent.display_name
        fulfillment_text = response.query_result.fulfillment_text

        print("✅ Intent detectado:", intent_name, flush=True)
        print("💬 fulfillment_text:", fulfillment_text, flush=True)

        if fulfillment_text:
            return intent_name, fulfillment_text

        for message in response.query_result.response_messages:
            if message.text and message.text.text:
                return intent_name, message.text.text[0]

        print("🔴 No se encontró texto de respuesta.", flush=True)
        return intent_name, None

    except Exception as e:
        print(f"❌ Error en Dialogflow: {e}", flush=True)
        return "Default Fallback Intent", None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

