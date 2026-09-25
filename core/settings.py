"""
Carga y guardado de config/settings.json, donde se guarda la preferencia
de idioma (y a futuro, otras preferencias de la app).
"""

import json
import os

RUTA_SETTINGS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "settings.json"
)

IDIOMA_POR_DEFECTO = "es"


def cargar_idioma():
    try:
        with open(RUTA_SETTINGS, "r", encoding="utf-8") as f:
            data = json.load(f)
        idioma = data.get("idioma", IDIOMA_POR_DEFECTO)
        return idioma if idioma in ("es", "en") else IDIOMA_POR_DEFECTO
    except (OSError, json.JSONDecodeError):
        return IDIOMA_POR_DEFECTO


def guardar_idioma(idioma):
    try:
        with open(RUTA_SETTINGS, "w", encoding="utf-8") as f:
            json.dump({"idioma": idioma}, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[R36ARIA] No se pudo guardar settings.json: {e}")
