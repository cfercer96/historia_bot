from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Carga tu API Key desde variables de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/webhook', methods=['POST'])
def webhook():
    # 🔍 Imprime los headers y el body de la solicitud
    print("🧾 HEADERS:", dict(request.headers))
    
    # Cambié la forma de imprimir el body para evitar el error de decodificación
    print("📦 RAW BODY:", request.data)  # Imprime el cuerpo crudo de la solicitud (bytes)

    # Verificamos si el contenido es JSON
    if not request.is_json:
        return jsonify({'fulfillmentText': 'Formato no soportado. Se esperaba JSON.'}), 415

    try:
        # Intenta convertir el cuerpo de la solicitud a JSON
        req = request.get_json(silent=True)

        # Validación básica del contenido
        if not req or 'queryResult' not in req:
            return jsonify({'fulfillmentText': 'Estructura del mensaje no válida.'}), 400

        user_message = req['queryResult'].get('queryText', '')

        # Llamada a OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un experto en historia de Costa Rica."},
                {"role": "user", "content": user_message}
            ]
        )

        reply = response['choices'][0]['message']['content'].strip()

        return jsonify({'fulfillmentText': reply})

    except Exception as e:
        print("Error:", e)
        return jsonify({'fulfillmentText': 'Hubo un error al generar la respuesta.'}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
