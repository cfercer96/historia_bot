from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Carga la API Key desde variables de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()

    # Extrae el texto del usuario desde Dialogflow
    user_message = req.get('queryResult', {}).get('queryText', '')

    if not user_message:
        return jsonify({'fulfillmentText': "No se recibió mensaje válido."})

    try:
        # Llamada a OpenAI (GPT-3.5)
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un experto en historia de Costa Rica."},
                {"role": "user", "content": user_message}
            ]
        )

        reply = completion.choices[0].message.content.strip()

        # Enviar respuesta a Dialogflow
        return jsonify({'fulfillmentText': reply})

    except Exception as e:
        print("Error:", e)
        return jsonify({'fulfillmentText': "Ocurrió un error al generar la respuesta."})


# Configuración para Render (0.0.0.0 y puerto dinámico)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
