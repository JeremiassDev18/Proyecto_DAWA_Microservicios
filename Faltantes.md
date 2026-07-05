# Faltantes por implementar

Este documento resume los requerimientos del `Alcance.md` que no están cubiertos o están parcialmente implementados en el código actual.

## 1. Requerimientos funcionales pendientes

### AIA-R04: Generación de resumen de solicitudes
- Estado actual: no hay función que genere resúmenes automáticos del historial de una solicitud.
- Falta implementar:
  - Generación de resumen de texto para una solicitud específica.
  - Consulta de historial asociado a una solicitud para consolidar su contexto.
  - Endpoint o servicio que devuelva el resumen al docente/coordinador.

### AIA-R05: Generación de resumen de bitácoras
- Estado actual: no existe consolidación automática de observaciones registradas en múltiples sesiones.
- Falta implementar:
  - Registro de bitácoras u observaciones de atención en múltiples sesiones.
  - Algoritmo o pipeline que sintetice esas observaciones.
  - Endpoint para obtener el resumen consolidado.

### AIA-R10: Configuración de FAQs y documentos base
- Estado actual: hay gestión de `chatbot_dataset` y dataset de intenciones, pero no existen endpoints administrativos para `documento_base`.
- Falta implementar:
  - CRUD para documentos RAG (`documento_base`).
  - Administración de categorías, fuentes y estado de los documentos.
  - Interfaz o endpoints destinados a usuarios administradores.

### AIA-R12: Panel de métricas de uso del agente
- Estado actual: existen endpoints de métricas de modelo e historial de predicciones, pero no hay dashboard completo ni condensado de uso.
- Falta implementar:
  - Indicadores clave: número de conversaciones, temas más consultados, tasa de escalamiento, satisfacción promedio.
  - Endpoint o UI que entregue métricas agregadas.
  - Control de acceso para coordinadores y administradores.

## 2. Requerimientos de seguridad y control

### AIA-R11: Validación de respuestas no autorizadas
- Estado actual: no hay filtro explícito para evitar exposición de datos sensibles o respuestas fuera de alcance.
- Falta implementar:
  - Validación de contenido generado y respuestas de la base de conocimiento.
  - Mecanismo que bloquee información sensible de terceros.
  - Reglas para restringir la respuesta a información institucional autorizada.

### Control de acceso y permisos administrativos
- Estado actual: no hay autorización de roles en los routers.
- Falta implementar:
  - Autenticación y autorización en endpoints administrativos y de dataset.
  - Validación de token/roles para acceder a métricas, administración y gestión de documentos.
  - Restricción de funciones administrativas a usuarios coordinadores/administradores.

## 3. Integración y orquestación de microservicios

### Comunicación con microservicios de administración y tutorías
- Estado actual: `app/services/microservice_client.py` usa datos mock en lugar de llamadas reales.
- Falta implementar:
  - Conexión real a Microservicio de Administración Académica para obtener asignaturas, docentes y disponibilidad.
  - Conexión real a Microservicio de Tutorías para el estado de solicitudes.
  - Mecanismo de mensajería REST o asíncrona actualizado según la arquitectura definida.

### Escalamiento automático basado en umbral de confianza
- Estado actual: el flujo de `chat_orchestrator` envía la consulta a pendientes solamente cuando no encuentra respuesta.
- Falta implementar:
  - Umbral claro de confianza para decidir escalamiento.
  - Lógica que derive casos poco confiables a docente/coordinador según score.
  - Registro específico de motivo de escalamiento.

## 4. Cohesión de la base de conocimiento

### Versionado de documentos y FAQ
- Estado actual: no hay evidencia de versionado de la base de conocimiento.
- Falta implementar:
  - Versionado de `documento_base` y/o `chatbot_dataset`.
  - Auditoría de qué documentos estaban vigentes cuando se generó una respuesta.
  - Mecanismo para rastrear cambios históricos de la base de conocimiento.

## 5. Definición de tareas recomendadas

1. Añadir endpoints CRUD para `documento_base` con autorización.
2. Implementar resumen de solicitudes y bitácoras en servicios nuevos.
3. Crear un servicio de validación de respuestas sensible/out-of-scope.
4. Desarrollar un panel de métricas agregadas y endpoints de uso.
5. Reemplazar mocks de microservicios con integraciones reales o adaptadores de cliente.
6. Introducir gestión de roles y permisos en `app/core/dependencies.py` y en routers.
7. Añadir versionado y auditoría a la base de conocimiento.

## 6. Prioridad sugerida

- Alta
  - Seguridad / validación de respuestas
  - Control de accesos administrativos
  - Escalamiento automático
- Media
  - Endpoints administrativos de documentos RAG
  - Métricas de uso consolidadas
- Baja
  - Versionado de base de conocimiento
  - Resúmenes de bitácoras avanzados
