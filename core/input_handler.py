"""
Mapeo de botones del mando.

IMPORTANTE: el numero de boton exacto puede variar segun la revision de
placa / firmware DarkOS instalado en tu R36S. Si los controles no responden
como esperas, corre este mismo archivo directamente:

    python3 core/input_handler.py

Esto imprime en consola el numero de cada boton/eje que toques, para que
ajustes las constantes de abajo.
"""

import pygame

BOTON_A = 1
BOTON_B = 0
BOTON_X = 2
BOTON_Y = 3
BOTON_SELECT = 12
BOTON_START = 13
BOTON_L = 4  # gatillo/hombro izquierdo -- se usa como alternador mayus/minus en el teclado virtual

# Algunos mandos (como el de este dispositivo) reportan la cruceta como
# botones sueltos en vez de un "hat" -- ver core/input_handler.py al
# correrlo directo para confirmar los numeros en tu mando especifico.
BOTON_DPAD_UP = 8
BOTON_DPAD_DOWN = 9
BOTON_DPAD_LEFT = 10
BOTON_DPAD_RIGHT = 11


def obtener_direccion_input(event):
    """Devuelve (dx, dy) con valores en {-1, 0, 1} para movimiento
    direccional, soportando tanto mandos con dpad como hat real
    (JOYHATMOTION) como mandos que reportan la cruceta como botones
    sueltos (JOYBUTTONDOWN). Devuelve None si el evento no es de
    movimiento direccional.

    Convencion: dy=1 es "arriba", dy=-1 es "abajo" (igual que un hat).
    """
    if event.type == pygame.JOYHATMOTION:
        return event.value

    if event.type == pygame.JOYBUTTONDOWN:
        if event.button == BOTON_DPAD_UP:
            return (0, 1)
        elif event.button == BOTON_DPAD_DOWN:
            return (0, -1)
        elif event.button == BOTON_DPAD_LEFT:
            return (-1, 0)
        elif event.button == BOTON_DPAD_RIGHT:
            return (1, 0)

    return None


# ----------------------------------------------------------------------
# Repeticion de direccion mientras se mantiene presionada (como el
# "key repeat" de un teclado): primer paso inmediato al presionar, y si
# se sigue sosteniendo, repite despues de un retraso inicial mas largo,
# y luego a intervalos regulares mas cortos.
# ----------------------------------------------------------------------
RETRASO_INICIAL = 0.35       # segundos antes del primer repeat
INTERVALO_REPETICION = 0.10  # segundos entre repeats sucesivos (velocidad normal)
UMBRAL_ACELERACION = 2.0     # segundos sosteniendo antes de acelerar
INTERVALO_ACELERADO = 0.03   # segundos entre repeats una vez acelerado

_repeticion = {
    "direccion": None,   # (dx, dy) actualmente sostenida, o None
    "boton": None,        # boton fisico que la origino (para detectar cuando se suelta)
    "proximo_tick": 0.0,
    "inicio_sostenido": 0.0,  # momento en que se empezo a sostener esta direccion
}


def _tiempo_actual():
    return pygame.time.get_ticks() / 1000.0


def registrar_evento_direccion(event):
    """Hay que llamar esto con TODOS los eventos (independientemente de la
    pantalla actual) para que el sistema de repeticion sepa que direccion
    se esta sosteniendo. No dispara movimiento por si solo -- eso lo hace
    verificar_repeticion(), llamada aparte una vez por frame."""
    if event.type == pygame.JOYBUTTONDOWN and event.button in (
        BOTON_DPAD_UP, BOTON_DPAD_DOWN, BOTON_DPAD_LEFT, BOTON_DPAD_RIGHT
    ):
        ahora = _tiempo_actual()
        _repeticion["direccion"] = obtener_direccion_input(event)
        _repeticion["boton"] = event.button
        _repeticion["proximo_tick"] = ahora + RETRASO_INICIAL
        _repeticion["inicio_sostenido"] = ahora

    elif event.type == pygame.JOYBUTTONUP and event.button == _repeticion["boton"]:
        _repeticion["direccion"] = None
        _repeticion["boton"] = None

    elif event.type == pygame.JOYHATMOTION:
        x, y = event.value
        if x == 0 and y == 0:
            _repeticion["direccion"] = None
            _repeticion["boton"] = None
        else:
            ahora = _tiempo_actual()
            _repeticion["direccion"] = (x, y)
            _repeticion["boton"] = None
            _repeticion["proximo_tick"] = ahora + RETRASO_INICIAL
            _repeticion["inicio_sostenido"] = ahora


def verificar_repeticion():
    """Llamar una vez por frame. Si hay una direccion sostenida y ya paso
    el tiempo de espera correspondiente, devuelve esa direccion (y
    programa el siguiente repeat). Pasado UMBRAL_ACELERACION segundos
    sosteniendo la misma direccion, los repeats pasan a ser mas seguidos
    (INTERVALO_ACELERADO) para poder recorrer listas largas mas rapido."""
    direccion = _repeticion["direccion"]
    if direccion is None:
        return None
    ahora = _tiempo_actual()
    if ahora >= _repeticion["proximo_tick"]:
        sosteniendo_desde = ahora - _repeticion["inicio_sostenido"]
        intervalo = INTERVALO_ACELERADO if sosteniendo_desde >= UMBRAL_ACELERACION else INTERVALO_REPETICION
        _repeticion["proximo_tick"] = ahora + intervalo
        return direccion
    return None


def limpiar_repeticion():
    """Util al cambiar de pantalla, para que un movimiento sostenido no se
    arrastre de la pantalla anterior a la nueva."""
    _repeticion["direccion"] = None
    _repeticion["boton"] = None


def inicializar_joystick():
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        return None
    joy = pygame.joystick.Joystick(0)
    joy.init()
    return joy


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((320, 240))
    joy = inicializar_joystick()
    print("Mando detectado:", joy.get_name() if joy else "NINGUNO")
    print("Toca botones / mueve el dpad para ver sus IDs. Ctrl+C para salir.")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                print(f"Boton presionado: {event.button}")
            elif event.type == pygame.JOYHATMOTION:
                print(f"Dpad (hat): {event.value}")
            elif event.type == pygame.JOYAXISMOTION and abs(event.value) > 0.5:
                print(f"Eje {event.axis}: {event.value:.2f}")
