from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Cargar tu API key de OpenAI desde variable de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/', methods=['GET'])
def home():
    return "Webhook para WhatsApp + Dialogflow + ChatGPT activo."

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()

    # Extrae la pregunta del intent de Dialogflow
    user_query = req.get("queryResult", {}).get("queryText", "")
    
    # Procesa con ChatGPT
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_query}]
    )
    
    answer = response['choices'][0]['message']['content']

    # Responde a Dialogflow
    return jsonify({
        "fulfillmentText": answer
    })

if __name__ == '__main__':
    app.run(debug=True)
