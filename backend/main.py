from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from auth import auth_bp
from rag import rag_bp
from database import init_db

app = Flask(__name__)
app.config.from_envvar('FLASK_ENV', silent=True)
app.config['JWT_SECRET_KEY'] = 'replace-with-secret-key'

jwt = JWTManager(app)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(rag_bp, url_prefix='/api')

@app.route('/')
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
