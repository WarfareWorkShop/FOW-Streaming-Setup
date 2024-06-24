from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager

app = Flask(__name__)
CORS(app)  # Habilitar CORS para permitir peticiones desde el frontend
app.config['JWT_SECRET_KEY'] = 'your_secret_key'  # Cambia esto a algo seguro
jwt = JWTManager(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    # Aquí llamamos a la API de OpenAI y retornamos la respuesta.
    # response = openai.ChatCompletion.create(...)
    return jsonify({"response": "This is a placeholder response from the AI"})

if __name__ == '__main__':
    app.run(debug=True)

