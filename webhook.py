from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os

# Inicializar cliente de OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Mostrar cabeceras y cuerpo para depuración
    print("🧾 HEADERS:", dict(request.headers))
    try:
        raw_body = request.get_data()
        print("📦 RAW BODY:", raw_body.decode("utf-8"))
    except Exception as e:
        print("❌ Error al leer el cuerpo:", e)

    # Verificamos si el contenido es JSON
    if not request.is_json:
        return jsonify({'fulfillmentText': 'Formato no soportado. Se esperaba JSON.'}), 415

    req = request.get_json(silent=True)
    if not req or 'queryResult' not in req:
        return jsonify({'fulfillmentText': 'Estructura del mensaje no válida.'}), 400

    user_message = req['queryResult'].get('queryText', '')

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un experto en historia de Costa Rica."},
                {"role": "user", "content": user_message}
            ]
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({'fulfillmentText': reply})

    except Exception as e:
        print("❌ Error al procesar la solicitud:", e)
        return jsonify({'fulfillmentText': 'Hubo un error al generar la respuesta.'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

