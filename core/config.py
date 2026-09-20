"""
Carga y guardado de config/options.json, compartido por main.py y por el
flujo de "agregar torrents nuevos" (que necesita reescribir el archivo
cuando el usuario agrega una categoria nueva).
"""

import json
import os

RUTA_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "options.json"
)


def cargar_opciones():
    with open(RUTA_CONFIG, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("opciones", [])


def guardar_opciones(opciones):
    with open(RUTA_CONFIG, "w", encoding="utf-8") as f:
        json.dump({"opciones": opciones}, f, ensure_ascii=False, indent=2)
