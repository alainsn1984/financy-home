# Automatización Financiera Familiar y Gestión Multimodal de Gastos

## Problema

Gestión finanzas hogar → fricción recurrente matrimonio. Herramientas presupuesto existentes fallan: requieren entrada manual cada compra en interfaz dedicada. Genera pereza gastos pequeños/cotidianos que representan mayor fuga capital familiar.

## Solución

Bot financiero WhatsApp/Telegram elimina necesidad alternar apps o abrir hojas cálculo. Usuario envía:
- Mensaje texto plano
- Nota voz breve
- Foto recibo físico

Momento exacto transacción. Backend procesa mediante 3 canales paralelos.

---

## Canales de Procesamiento

### 1. Canal Texto Natural

Sistema analiza cadenas tipo `"gasté 15 en taxi"`.

**Proceso:**
- Modelos lenguaje ligeros integrados vía FastAPI
- Extrae importe (15.00), divisa
- Clasifica gasto automáticamente (ej: categoría transporte)

### 2. Canal Audio Voz

Ideal uso en movimiento esposa/esposo/madre/padre.

**Proceso:**
- Bot recibe archivo voz
- Envía a servicio transcripción alto rendimiento
- Procesa texto resultante
- **Precisión categorización inicial: 92%**

### 3. Canal Visión (OCR)

Usuario fotografía recibo compra supermercado/gasolinera.

**Proceso:**
- Extrae total factura, fecha emisión, nombre comercio
- Guarda imagen como respaldo digital seguro en servidor

---

## Beneficios

### Ahorro Tiempo
**5-7 horas mensuales** por usuario en conciliación manual cuentas.

### Funcionalidades Avanzadas
- Reglas negocio para consolidar metas ahorro familiar
- Alertas desvío presupuesto tiempo real
- Historial acumulado PostgreSQL

### Análisis Visual
Paneles enriquecidos Next.js permiten:
- Analizar patrones consumo mensuales conjuntamente
- Identificar suscripciones inactivas
- Proyectar salud financiera hogar

---

## Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| **Frontend** | Next.js |
| **Backend** | FastAPI |
| **Base Datos** | PostgreSQL |
| **NLP/ML** | Modelos lenguaje ligeros |
| **Transcripción** | Servicio alto rendimiento |
| **OCR** | Visión computacional |
| **Interfaz** | Bot WhatsApp | Bot Telegram 
| **Cloud** | Docker
| **Version** | Git

---

## Backend — desarrollo local

Requiere [`uv`](https://docs.astral.sh/uv/) (instalar: `curl -LsSf https://astral.sh/uv/install.sh | sh`).

Instalar dependencias:

```bash
uv sync
```

Arrancar servidor (recarga en caliente):

```bash
uv run uvicorn app.main:app --reload
```

Healthcheck: `GET http://127.0.0.1:8000/api/v1/health` → `{"status":"ok","service":"financiera-hogar","version":"0.1.0"}`

Lint / format / tests:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

---

## Flujo Asíncrono

Reduce drásticamente carga administrativa gestión doméstica mediante procesamiento paralelo 3 canales entrada datos.
