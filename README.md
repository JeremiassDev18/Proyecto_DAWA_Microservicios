# Proyecto DAWA - Microservicios 🚀

Este repositorio contiene el proyecto **DAWA Microservicios**, diseñado para practicar arquitectura moderna con **Next.js**, **Python**, **PostgREST** y **SQL**.  
La idea es levantar un ecosistema de servicios independientes que se comuniquen entre sí.

---

## 📂 Estructura del proyecto
- frontend/ → Aplicación en Next.js (UI).
- backend/ → Servicios en Python.
- postgrest/ → Configuración de PostgREST para exponer la base de datos como API REST.
- database/ → Scripts y configuración SQL.
- docs/ → Diagramas y documentación.

---

## 🔧 Tecnologías utilizadas
- Next.js
- Python
- PostgREST
- SQL (PostgreSQL)
- Docker & Docker Compose
- Git & GitHub

---

## 🌱 Flujo de trabajo con ramas
1. Crear una nueva rama para cada funcionalidad:
   git checkout -b feature/nueva-funcionalidad
2. Subir cambios a la rama:
   git push origin feature/nueva-funcionalidad
3. Crear un Pull Request hacia main.
4. Revisar y aprobar antes de hacer el merge.

👉 Ramas iniciales recomendadas:
- feature/frontend
- feature/backend
- feature/postgrest
- feature/docs

---

## 👨‍💻 Autor
**Jeremy**
Estudiante de Ingeniería en Computación • Apasionado por Next.js, Python y arquitecturas modernas.

---

## Estado actual del microservicio de Tutorías (rama Reservas)

### Cumplimiento funcional
- El microservicio implementa los requisitos TUT-R01 a TUT-R12 en una versión funcional base.
- Se ejecuta dockerizado junto a RabbitMQ y consume/publica eventos.
- Las pruebas unitarias del servicio pasan correctamente.

### Integración con otros microservicios del repositorio
- Actualmente no existe integración directa con todos los microservicios del repositorio.
- En esta rama, la integración implementada es por mensajería con RabbitMQ (colas `tutorias.solicitudes` y `tutorias.eventos`).
- No hay llamadas HTTP activas desde Tutorías hacia Security, Administración o Chatbot en el código actual de la rama Reservas.

### Qué fue adicional (mejora de calidad)
- Se añadió `.gitignore` y se excluyeron artefactos compilados de Python (`__pycache__`, `*.pyc`).
- Esta mejora no cambia la lógica de negocio; solo mejora orden y mantenibilidad del repositorio.

### Si se requiere interacción completa entre microservicios
- Definir contratos (endpoints o eventos) entre Tutorías, Security, Administración y Chatbot.
- Unificar red de Docker Compose o usar un compose raíz para todos los servicios.
- Configurar variables de entorno con URLs/colas de cada servicio y agregar pruebas de integración.

