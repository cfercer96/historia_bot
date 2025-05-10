from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Carga tu API Key desde variables de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/webhook', methods=['POST'])
def webhook():
    # Verificamos si el contenido es 'application/x-www-form-urlencoded'
    if request.content_type != 'application/x-www-form-urlencoded':
        return jsonify({'fulfillmentText': 'Formato no soportado. Se esperaba application/x-www-form-urlencoded.'}), 415
    
    # Los datos vienen en el formato 'x-www-form-urlencoded', por lo tanto se accede de esta manera
    user_message = request.form.get('Body', '')  # 'Body' es el nombre del campo enviado por Twilio

    if not user_message:
        return jsonify({'fulfillmentText': 'Mensaje no recibido.'}), 400

    # Llamamos a OpenAI para generar una respuesta
    try:
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
