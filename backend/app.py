from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from config import Config
from models import bcrypt, db
from routes import auth_bp

migrate = Migrate()
jwt = JWTManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)  # Habilitar CORS para permitir peticiones desde el frontend

    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/chat', methods=['POST'])
    def chat():
        user_message = request.json.get('message')
        # Aquí llamamos a la API de OpenAI y retornamos la respuesta.
        # response = openai.ChatCompletion.create(...)
        return jsonify({"response": "This is a placeholder response from the AI"})

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)

