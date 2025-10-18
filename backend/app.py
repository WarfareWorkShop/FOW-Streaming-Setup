from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from backend.config import Config
from backend.models import db, bcrypt
from backend.routes import auth_bp

jwt = JWTManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/chat', methods=['POST'])
    def chat():
        user_message = request.json.get('message')
        # TODO: integrar con OpenAI y reemplazar la respuesta simulada.
        # response = openai.ChatCompletion.create(...)
        return jsonify({"response": "This is a placeholder response from the AI"})

    app.register_blueprint(auth_bp)

    return app


if __name__ == '__main__':
    application = create_app()
    application.run(debug=True)
