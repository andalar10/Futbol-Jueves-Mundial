"""
Procesa una exportación completa de WhatsApp (chat + multimedia) y genera
un JSON con el mismo modelo de datos que usa gestor-alineaciones.html,
listo para importar con el botón "Importar JSON" de la app.

USO
---
1. Descomprime el .zip exportado de WhatsApp en una carpeta, por ejemplo:
       export_whatsapp/
         _chat.txt
         IMG-20260820-WA0001.jpg
         IMG-20260820-WA0002.jpg
         ...

2. Instala las dependencias (una sola vez):
       pip install pytesseract pillow --break-system-packages
   y el binario de Tesseract OCR:
       - Ubuntu/Debian: sudo apt install tesseract-ocr tesseract-ocr-spa
       - macOS:         brew install tesseract tesseract-lang
       - Windows:       instalador desde https://github.com/UB-Mannheim/tesseract/wiki

3. Ejecuta:
       python procesar_export_whatsapp.py export_whatsapp/ salida.json

4. Abre gestor-alineaciones.html -> pestaña "Historial" -> "Importar JSON"
   y selecciona salida.json.

LIMITACIONES IMPORTANTES
-------------------------
- El reconocimiento de nombres en las imágenes usa Tesseract OCR (offline,
  gratuito), que es bastante menos fiable que el reconocimiento por IA que
  usa la app para partidos nuevos. Es NORMAL que algunos nombres salgan mal
  o incompletos: revísalos luego dentro de la app (pestaña Historial).
- No se asigna automáticamente equipo ni posición de cada jugador (queda en
  blanco): no se puede inferir con fiabilidad solo con OCR de texto.
- El "partido" se agrupa por la FECHA DEL MENSAJE en el chat, no por la fecha
  del partido mencionada en el texto (ej. "jueves 20 de agosto"). Si sueles
  enviar la convocatoria con antelación, revisa las fechas tras importar.
- El formato de fecha/hora de _chat.txt varía según el sistema operativo y
  la configuración regional del teléfono que exportó. El patrón de abajo
  cubre el formato más común de Android en español; si no detecta ningún
  mensaje, ajusta CHAT_LINE_PATTERN según el formato real de tu archivo.
"""

import sys
import re
import json
import unicodedata
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    import pytesseract
    from PIL import Image
    OCR_DISPONIBLE = True
except ImportError:
    OCR_DISPONIBLE = False

# Ajusta este patrón si tu _chat.txt tiene un formato distinto.
# Cubre: [17/8/26, 10:32:15] Juan Pérez: mensaje
CHAT_LINE_PATTERN = re.compile(
    r'^\[?(\d{1,2}/\d{1,2}/\d{2,4}),?\s(\d{1,2}:\d{2}(?::\d{2})?)\s?(?:[ap]\.?\s?m\.?)?\]?\s?-?\s?([^:]+):\s(.*)$',
    re.IGNORECASE
)

IMG_PATTERN = re.compile(r'([\w\-]+\.(?:jpg|jpeg|png|webp))', re.IGNORECASE)

CONVOCATORIA_KEYWORDS = ["convocatoria", "convocados", "concentraci"]

# Texto de marca de agua del generador de alineaciones a filtrar del OCR
RUIDO_OCR = {"clstudio.info", "football squad builder", "clstudio", "squad", "builder"}


def parsear_fecha(fecha_str):
    """Convierte dd/mm/aa o dd/mm/aaaa a date ISO."""
    for fmt in ("%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(fecha_str, fmt).date()
        except ValueError:
            continue
    return None


def parsear_chat(txt_path: Path):
    mensajes = []
    buffer = None
    with open(txt_path, encoding="utf-8-sig") as f:
        for linea in f:
            linea = linea.rstrip("\n")
            m = CHAT_LINE_PATTERN.match(linea)
            if m:
                if buffer:
                    mensajes.append(buffer)
                fecha_str, hora, autor, texto = m.groups()
                fecha = parsear_fecha(fecha_str)
                buffer = {
                    "fecha": fecha,
                    "hora": hora,
                    "autor": autor.strip(),
                    "texto": texto,
                }
            elif buffer:
                buffer["texto"] += "\n" + linea
        if buffer:
            mensajes.append(buffer)
    return mensajes


def es_convocatoria(texto: str) -> bool:
    t = texto.lower()
    return any(k in t for k in CONVOCATORIA_KEYWORDS)


def imagenes_en_mensaje(texto: str):
    return IMG_PATTERN.findall(texto)


def limpiar_linea_ocr(linea: str) -> str | None:
    linea = linea.strip()
    if len(linea) < 2:
        return None
    normal = unicodedata.normalize("NFKD", linea.lower())
    if any(r in normal for r in RUIDO_OCR):
        return None
    if linea.isdigit():
        return None
    # descarta líneas muy largas (probablemente ruido, no un nombre)
    if len(linea) > 25:
        return None
    return linea


def ocr_nombres(imagen_path: Path):
    if not OCR_DISPONIBLE:
        return []
    try:
        img = Image.open(imagen_path)
        texto = pytesseract.image_to_string(img, lang="spa+eng")
        candidatos = [limpiar_linea_ocr(l) for l in texto.splitlines()]
        return [c for c in candidatos if c]
    except Exception as e:
        print(f"  [!] OCR fallo en {imagen_path.name}: {e}")
        return []


def detectar_cambios(anterior: list[str], nueva: list[str]):
    set_ant, set_nueva = set(anterior), set(nueva)
    bajas = [n for n in anterior if n not in set_nueva]
    altas = [n for n in nueva if n not in set_ant]
    cambios = []
    for i, baja in enumerate(bajas):
        entra = altas[i] if i < len(altas) else None
        cambios.append({"jugador_baja": baja, "jugador_entra": entra})
    return cambios


def procesar(export_dir: Path):
    chat_files = list(export_dir.glob("*.txt"))
    if not chat_files:
        print("No se encontró ningún .txt en la carpeta indicada.")
        sys.exit(1)
    chat_path = chat_files[0]
    print(f"Leyendo {chat_path.name}...")
    mensajes = parsear_chat(chat_path)
    print(f"  {len(mensajes)} mensajes encontrados.")

    # Agrupa mensajes por fecha
    por_fecha = defaultdict(list)
    for m in mensajes:
        if m["fecha"]:
            por_fecha[m["fecha"]].append(m)

    partidos = []
    if not OCR_DISPONIBLE:
        print("\n[!] pytesseract/Pillow no están instalados: las imágenes se")
        print("    registrarán SIN nombres extraídos (jugadores vacío).")
        print("    Instala con: pip install pytesseract pillow --break-system-packages\n")

    for fecha, msgs in sorted(por_fecha.items()):
        texto_convocatoria = ""
        rutas_imagenes = []
        for m in msgs:
            if es_convocatoria(m["texto"]):
                texto_convocatoria = m["texto"].strip()
            for nombre_img in imagenes_en_mensaje(m["texto"]):
                candidato = export_dir / nombre_img
                if candidato.exists():
                    rutas_imagenes.append(candidato)

        if not texto_convocatoria and not rutas_imagenes:
            continue  # día sin nada relevante para el modelo

        alineaciones = []
        anterior_nombres = []
        for i, img_path in enumerate(rutas_imagenes, start=1):
            print(f"Procesando {img_path.name} ({fecha})...")
            nombres = ocr_nombres(img_path)
            cambios = detectar_cambios(anterior_nombres, nombres) if i > 1 else []
            alineaciones.append({
                "id": f"{fecha.isoformat()}-v{i}",
                "version": i,
                "valida": i == len(rutas_imagenes),
                "fecha_mensaje": fecha.isoformat(),
                "imagen_path": img_path.name,
                "imagen_thumb": None,  # no se incrusta la imagen para no inflar el JSON
                "jugadores": [{"nombre": n, "posicion": "", "equipo": ""} for n in nombres],
                "cambios_respecto_anterior": cambios,
            })
            anterior_nombres = nombres
            if i > 1:
                alineaciones[-2]["valida"] = False

        partidos.append({
            "id": fecha.isoformat(),
            "fecha": fecha.isoformat(),
            "convocatoria": {
                "texto": texto_convocatoria,
                "fecha_mensaje": fecha.isoformat(),
                "es_borrador": True,
            },
            "alineaciones": alineaciones,
        })

    return partidos


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python procesar_export_whatsapp.py <carpeta_export> <salida.json>")
        sys.exit(1)

    export_dir = Path(sys.argv[1])
    salida_path = Path(sys.argv[2])

    if not export_dir.is_dir():
        print(f"No existe la carpeta: {export_dir}")
        sys.exit(1)

    partidos = procesar(export_dir)
    salida_path.write_text(json.dumps(partidos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nListo. {len(partidos)} partidos escritos en {salida_path}")
    print("Importa este archivo desde la app: pestaña Historial -> Importar JSON")
    print("Revisa los nombres extraídos por OCR, pueden tener errores.")
