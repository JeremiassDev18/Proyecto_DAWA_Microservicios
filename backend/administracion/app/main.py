from flask import Flask, jsonify
from flask_cors import CORS

from app.database import Base, engine
from app.routes.restaurantes import restaurantes_bp
from app.routes.sucursales import sucursales_bp
from app.routes.mesas import mesas_bp
from app.routes.horarios import horarios_bp
from app.routes.promociones import promociones_bp

Base.metadata.create_all(bind=engine)

app = Flask(__name__)
CORS(app)

app.register_blueprint(restaurantes_bp, url_prefix="/api/administracion/restaurantes")
app.register_blueprint(sucursales_bp, url_prefix="/api/administracion/sucursales")
app.register_blueprint(mesas_bp, url_prefix="/api/administracion/mesas")
app.register_blueprint(horarios_bp, url_prefix="/api/administracion/horarios")
app.register_blueprint(promociones_bp, url_prefix="/api/administracion/promociones")


@app.route("/")
def home():
    return jsonify({
        "mensaje": "Microservicio de Administracion funcionando correctamente"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)