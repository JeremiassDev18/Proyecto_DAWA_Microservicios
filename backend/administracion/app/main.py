import os
from flask import Flask, jsonify
from dotenv import load_dotenv

from app.database import Base, engine
from app.routes.facultades import facultades_bp
from app.routes.carreras import carreras_bp
from app.routes.asignaturas import asignaturas_bp
from app.routes.periodos import periodos_bp
from app.routes.docentes import docentes_bp
from app.routes.estudiantes import estudiantes_bp
from app.routes.paralelos import paralelos_bp
from app.routes.horarios import horarios_bp
from app.routes.dashboard import dashboard_bp
from app.routes.reportes import reportes_bp
from app.routes.internos import internos_bp

load_dotenv()

Base.metadata.create_all(bind=engine)

app = Flask(__name__)

app.register_blueprint(facultades_bp, url_prefix="/api/administracion/facultades")
app.register_blueprint(carreras_bp, url_prefix="/api/administracion/carreras")
app.register_blueprint(asignaturas_bp, url_prefix="/api/administracion/asignaturas")
app.register_blueprint(periodos_bp, url_prefix="/api/administracion/periodos")
app.register_blueprint(docentes_bp, url_prefix="/api/administracion/docentes")
app.register_blueprint(estudiantes_bp, url_prefix="/api/administracion/estudiantes")
app.register_blueprint(paralelos_bp, url_prefix="/api/administracion/paralelos")
app.register_blueprint(horarios_bp, url_prefix="/api/administracion/horarios")
app.register_blueprint(dashboard_bp, url_prefix="/api/administracion/dashboard")
app.register_blueprint(reportes_bp, url_prefix="/api/administracion/reportes")
app.register_blueprint(internos_bp, url_prefix="/api/administracion/internos")


@app.route("/")
def home():
    return jsonify({
        "mensaje": "Microservicio de Administracion Academica funcionando correctamente"
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True)