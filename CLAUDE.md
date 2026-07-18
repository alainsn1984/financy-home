# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Estado actual

Repo en fase inicial: solo existe `README.md`. **No hay código, dependencias, build ni tests todavía.** No hay comandos que ejecutar aún — al crear la primera estructura, actualizar este archivo con los comandos reales (instalar deps, arrancar backend/frontend, tests).

## Qué es

Bot financiero familiar multimodal. Usuario registra gastos vía WhatsApp/Telegram enviando **texto**, **nota de voz** o **foto de recibo** en el momento de la transacción. Backend procesa por 3 canales paralelos y persiste en PostgreSQL. Frontend Next.js muestra paneles de análisis.

## Arquitectura (planeada según README)

Tres canales de entrada convergen en el mismo pipeline de persistencia/categorización:

1. **Canal Texto** — parsea lenguaje natural (`"gasté 15 en taxi"`) con modelos de lenguaje ligeros vía FastAPI. Extrae importe, divisa; clasifica categoría.
2. **Canal Voz** — audio → servicio de transcripción → reusa el canal texto para parseo/categorización.
3. **Canal Visión (OCR)** — foto de recibo → extrae total, fecha, comercio; guarda imagen como respaldo.

Los 3 canales deben desembocar en la **misma lógica de extracción/categorización y el mismo modelo de transacción** — voz reusa texto; evitar duplicar el parseo por canal.

Sobre las transacciones: reglas de negocio (metas de ahorro), alertas de desvío de presupuesto en tiempo real, historial acumulado.

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | Next.js |
| Backend | FastAPI |
| BD | PostgreSQL |
| NLP/parseo | Modelos de lenguaje ligeros |
| Voz | Servicio de transcripción |
| Visión | OCR |
| Mensajería | Bots WhatsApp + Telegram |
| Deploy | Docker |

## Idioma

- **Código siempre en inglés** — nombres de variables, funciones, clases, archivos, comentarios, commits.
- **Contenido de cara al usuario según idioma configurado por el usuario** (i18n) — mensajes del bot, textos de UI, categorías visibles. A definir al trabajar la parte visual; no hardcodear strings de usuario.
