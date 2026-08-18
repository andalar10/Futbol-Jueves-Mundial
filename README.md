# Fútbol Jueves Mundial

App para gestionar convocatorias y alineaciones del grupo: lee la foto de la alineación con IA (visión de Claude), detecta automáticamente bajas y sustituciones entre versiones, y guarda todo en Supabase (Postgres).

## Archivos

- `index.html` — la aplicación. Un único fichero HTML/CSS/JS, sin build ni dependencias que instalar. Se abre directamente en el navegador o se sirve como página estática.
- `procesar_export_whatsapp.py` — script de un solo uso para cargar el histórico de partidos a partir de una exportación completa de WhatsApp (chat + multimedia). Genera un JSON importable desde la app (pestaña Historial → Importar JSON).

## Base de datos

La app usa un proyecto de Supabase (Postgres) con 4 tablas: `partidos`, `alineaciones`, `jugadores_alineacion`, `cambios`. Un trigger en la propia base de datos invalida automáticamente la versión anterior de una alineación cuando se guarda una nueva para el mismo partido.

## Despliegue

Pensada para servirse como página estática (GitHub Pages, Netlify, Vercel...). No necesita servidor propio: toda la lógica corre en el navegador y habla directamente con la API REST de Supabase.
