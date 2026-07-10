import requests, jwt, json

BASE = "http://localhost:5003"
SECRET = "1a6790ea7aee933b903e74fcaa2804dfbf61387d6c4d7cb61206fd32b211958b"

eh = {"Authorization": f"Bearer {jwt.encode({'usuario_id': 3, 'roles': ['estudiante']}, SECRET, algorithm='HS256')}"}
dh = {"Authorization": f"Bearer {jwt.encode({'usuario_id': 4, 'roles': ['docente']}, SECRET, algorithm='HS256')}"}
ah = {"Authorization": f"Bearer {jwt.encode({'usuario_id': 1, 'roles': ['admin']}, SECRET, algorithm='HS256')}"}

tests = []

# 1
r = requests.get(f"{BASE}/api/tutorias/sesiones/abiertas", headers=eh)
tests.append(f"1. sesiones/abiertas: {r.status_code} - {r.json().get('cantidad', '?')} sesiones")

# 2
r = requests.get(f"{BASE}/api/tutorias/estudiantes/1/bitacoras", headers=eh)
tests.append(f"2. bitacoras: {r.status_code} - {r.json().get('cantidad', '?')} bitacoras")

# 3
r = requests.get(f"{BASE}/api/tutorias/solicitudes?estudiante_id=1", headers=eh)
tests.append(f"3. solicitudes: {r.status_code} - {r.json().get('cantidad', '?')} solicitudes")

# 4
r = requests.get(f"{BASE}/api/tutorias/sesiones/docente?docente_id=1", headers=dh)
tests.append(f"4. sesiones/docente: {r.status_code} - {r.json().get('cantidad', '?')} sesiones")

# 5
r = requests.get(f"{BASE}/api/tutorias/sesiones/solicitudes-pendientes?docente_id=1", headers=dh)
tests.append(f"5. solicitudes-pendientes: {r.status_code} - {r.json().get('cantidad', '?')} solicitudes")

# 6
r = requests.post(f"{BASE}/api/tutorias/sesiones/crear", headers=ah, json={
    "docente_id": 2, "tema": "Sesion de prueba admin", "asignatura_id": 10,
    "descripcion": "Creada por admin", "capacidad_maxima": 15
})
d = r.json()
tests.append(f"6. sesiones/crear: {r.status_code} - id={d.get('id', 'ERR')} estado={d.get('estado', d.get('error'))}")

# 7
new_sesion_id = d.get("id")
if new_sesion_id:
    r = requests.post(f"{BASE}/api/tutorias/sesiones/{new_sesion_id}/bitacora", headers=dh, json={
        "detalle": "Sesion completada exitosamente", "temas_detectados": "Prueba, QA"
    })
    tests.append(f"7. bitacora sesion: {r.status_code} - id={r.json().get('id', 'ERR')}")

    # 8
    r = requests.get(f"{BASE}/api/tutorias/sesiones/{new_sesion_id}/inscritos", headers=dh)
    tests.append(f"8. inscritos: {r.status_code} - {r.json().get('cantidad', '?')} inscritos")

# 9 - OPTIONS
r = requests.options(f"{BASE}/api/tutorias/sesiones/abiertas", headers={
    "Origin": "http://localhost:3008",
    "Access-Control-Request-Method": "GET",
    "Access-Control-Request-Headers": "Authorization,Content-Type",
})
tests.append(f"9. OPTIONS preflight: {r.status_code} - CORS={'OK' if r.headers.get('Access-Control-Allow-Origin') else 'FAIL'}")

print("\n".join(tests))
