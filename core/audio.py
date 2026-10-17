"""
Sonido de navegacion al moverse por las listas. El usuario pone su propio
archivo de audio en la carpeta sounds/ (ver sounds/README.md) -- si no hay
ninguno, o si el audio no esta disponible en el dispositivo, simplemente
no suena nada (nunca rompe el programa).
"""

import os
import pygame

RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_SONIDOS = os.path.join(RAIZ_PROYECTO, "sounds")
EXTENSIONES_SOPORTADAS = (".wav", ".ogg", ".mp3")

_sonido_navegacion = None
_audio_disponible = False


def _buscar_archivo_navegacion():
    for ext in EXTENSIONES_SOPORTADAS:
        ruta = os.path.join(CARPETA_SONIDOS, f"navegar{ext}")
        if os.path.isfile(ruta):
            return ruta
    return None


def inicializar():
    """Llamar una vez al arrancar, despues de pygame.init()."""
    global _audio_disponible
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        _audio_disponible = True
    except Exception as e:
        print(f"[R36ARIA] Audio no disponible: {e}")
        _audio_disponible = False
        return

    cargar_sonido_navegacion()


def cargar_sonido_navegacion():
    """Vuelve a buscar y cargar sounds/navegar.(wav|ogg|mp3). Se puede
    llamar de nuevo en caliente si el usuario cambia el archivo."""
    global _sonido_navegacion
    if not _audio_disponible:
        return

    ruta = _buscar_archivo_navegacion()
    if ruta is None:
        _sonido_navegacion = None
        return

    try:
        _sonido_navegacion = pygame.mixer.Sound(ruta)
    except Exception as e:
        print(f"[R36ARIA] No se pudo cargar el sonido de navegacion '{ruta}': {e}")
        _sonido_navegacion = None


def reproducir_navegacion():
    if _sonido_navegacion is not None:
        try:
            _sonido_navegacion.play()
        except Exception:
            pass
