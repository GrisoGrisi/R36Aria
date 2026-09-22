import os
import sys

# ----------------------------------------------------------------------
# Bootstrap: se intenta primero el pygame del sistema (instalado via apt),
# ya que viene compilado contra las librerias reales del dispositivo
# (incluye soporte kmsdrm). El vendor/ empaquetado via pip solo se usa
# como fallback si el sistema no tiene pygame instalado, porque los wheels
# genericos de PyPI no siempre incluyen kmsdrm. Ver vendor/README.md.
# ----------------------------------------------------------------------
_RAIZ_PROYECTO = os.path.dirname(os.path.abspath(__file__))
_VENDOR_DIR = os.path.join(_RAIZ_PROYECTO, "vendor")

try:
    import pygame  # primero intenta la version del sistema
except ImportError:
    if os.path.isdir(_VENDOR_DIR):
        sys.path.insert(0, _VENDOR_DIR)
    import pygame

from core import aria2_client, fbdev, config
from core.input_handler import (
    inicializar_joystick, BOTON_SELECT, BOTON_START,
    registrar_evento_direccion, verificar_repeticion, limpiar_repeticion,
)
from core.state_manager import (
    estado, MENU_PRINCIPAL, RESOLVIENDO_METADATA, LISTA_ARCHIVOS,
    DESCARGANDO, ELEGIR_ACCION_ARCHIVO, EXTRAYENDO, DESCARGA_COMPLETA,
    CONFIRMAR_CANCELAR, NUEVOS_TORRENTS_LISTA, ENTRADA_TEXTO,
    OPCIONES, SELECCIONAR_CATEGORIA, ERROR_POPUP,
)

from ui import theme
from ui.menu_screen import construir_menu_principal, manejar_input_menu, dibujar_menu, mover_cursor_menu
from ui.resolving_screen import actualizar_resolviendo_metadata, dibujar_resolviendo_metadata
from ui.file_list_screen import manejar_input_lista_archivos, dibujar_lista_archivos, mover_cursor_lista
from ui.keyboard import mover_cursor_teclado
from ui.agregar_torrent_screen import (
    manejar_input_lista_nuevos, dibujar_lista_nuevos, mover_cursor_lista_nuevos,
    manejar_input_entrada_texto, dibujar_entrada_texto,
)
from ui.options_screen import (
    manejar_input_opciones, dibujar_opciones, mover_cursor_opciones,
    manejar_input_seleccionar_categoria, dibujar_seleccionar_categoria, mover_cursor_seleccionar_categoria,
)
from ui.extraction_screen import (
    manejar_input_eleccion_archivo, dibujar_eleccion_archivo,
    actualizar_extrayendo, dibujar_extrayendo,
)
from ui.download_screen import (
    manejar_input_descargando, manejar_input_confirmar_cancelar_descarga,
    manejar_input_descarga_completa,
    actualizar_descargando, dibujar_descargando, dibujar_descarga_completa,
    cancelar_y_limpiar_si_hay_descarga_activa,
)
from ui.popups import manejar_input_error_popup, dibujar_error_popup

FPS = 30


def salir_programa():
    cancelar_y_limpiar_si_hay_descarga_activa()
    aria2_client.detener_aria2()
    pygame.quit()
    sys.exit(0)


def procesar_input(event):
    # Salida de emergencia independiente del joystick (util si el mando no
    # responde por algun motivo, y como red de seguridad general). Si hay
    # un teclado conectado (por ejemplo via USB para depurar), ESC cierra.
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        salir_programa()
        return

    pantalla_actual = estado["pantalla"]

    if pantalla_actual == MENU_PRINCIPAL:
        manejar_input_menu(event, on_salir=salir_programa)

    elif pantalla_actual == LISTA_ARCHIVOS:
        manejar_input_lista_archivos(event)

    elif pantalla_actual == DESCARGANDO:
        manejar_input_descargando(event)

    elif pantalla_actual == CONFIRMAR_CANCELAR:
        manejar_input_confirmar_cancelar_descarga(event)

    elif pantalla_actual == DESCARGA_COMPLETA:
        manejar_input_descarga_completa(event)

    elif pantalla_actual == ELEGIR_ACCION_ARCHIVO:
        manejar_input_eleccion_archivo(event)

    elif pantalla_actual == NUEVOS_TORRENTS_LISTA:
        manejar_input_lista_nuevos(event)

    elif pantalla_actual == ENTRADA_TEXTO:
        manejar_input_entrada_texto(event)

    elif pantalla_actual == OPCIONES:
        manejar_input_opciones(event)

    elif pantalla_actual == SELECCIONAR_CATEGORIA:
        manejar_input_seleccionar_categoria(event)

    elif pantalla_actual == ERROR_POPUP:
        manejar_input_error_popup(event)

    # RESOLVIENDO_METADATA no procesa input: solo espera / puede errar por timeout


def actualizar_logica():
    pantalla_actual = estado["pantalla"]

    if pantalla_actual == RESOLVIENDO_METADATA:
        actualizar_resolviendo_metadata()
    elif pantalla_actual == DESCARGANDO:
        actualizar_descargando()
    elif pantalla_actual == EXTRAYENDO:
        actualizar_extrayendo()


def aplicar_repeticion_direccion():
    """Mientras se sostiene una direccion, mueve el cursor de forma
    continua (como el repeat de un teclado). Solo aplica en pantallas de
    navegacion por lista/grilla -- CONFIRMAR_CANCELAR queda afuera a
    proposito, porque ahi cada pulsacion alterna Si/No y repetirlo solo
    haria que vuelva a quedar en la misma opcion en cada tick."""
    direccion = verificar_repeticion()
    if direccion is None:
        return

    pantalla_actual = estado["pantalla"]
    if pantalla_actual == MENU_PRINCIPAL:
        mover_cursor_menu(direccion)
    elif pantalla_actual == LISTA_ARCHIVOS:
        if estado["buscando"]:
            mover_cursor_teclado(direccion)
        else:
            mover_cursor_lista(direccion)
    elif pantalla_actual == NUEVOS_TORRENTS_LISTA:
        mover_cursor_lista_nuevos(direccion)
    elif pantalla_actual == ENTRADA_TEXTO:
        mover_cursor_teclado(direccion)
    elif pantalla_actual == OPCIONES:
        mover_cursor_opciones(direccion)
    elif pantalla_actual == SELECCIONAR_CATEGORIA:
        mover_cursor_seleccionar_categoria(direccion)


def dibujar(pantalla_pygame):
    pantalla_actual = estado["pantalla"]

    if pantalla_actual == MENU_PRINCIPAL:
        dibujar_menu(pantalla_pygame)
    elif pantalla_actual == RESOLVIENDO_METADATA:
        dibujar_resolviendo_metadata(pantalla_pygame)
    elif pantalla_actual == LISTA_ARCHIVOS:
        dibujar_lista_archivos(pantalla_pygame)
    elif pantalla_actual in (DESCARGANDO, CONFIRMAR_CANCELAR):
        dibujar_descargando(pantalla_pygame)
    elif pantalla_actual == DESCARGA_COMPLETA:
        dibujar_descarga_completa(pantalla_pygame)
    elif pantalla_actual == ELEGIR_ACCION_ARCHIVO:
        dibujar_eleccion_archivo(pantalla_pygame)
    elif pantalla_actual == EXTRAYENDO:
        dibujar_extrayendo(pantalla_pygame)
    elif pantalla_actual == NUEVOS_TORRENTS_LISTA:
        dibujar_lista_nuevos(pantalla_pygame)
    elif pantalla_actual == ENTRADA_TEXTO:
        dibujar_entrada_texto(pantalla_pygame)
    elif pantalla_actual == OPCIONES:
        dibujar_opciones(pantalla_pygame)
    elif pantalla_actual == SELECCIONAR_CATEGORIA:
        dibujar_seleccionar_categoria(pantalla_pygame)
    elif pantalla_actual == ERROR_POPUP:
        # Redibuja la pantalla de fondo segun a donde se va a volver, y el popup encima
        if estado["pantalla_anterior"] == MENU_PRINCIPAL:
            dibujar_menu(pantalla_pygame)
        elif estado["pantalla_anterior"] == LISTA_ARCHIVOS:
            dibujar_lista_archivos(pantalla_pygame)
        dibujar_error_popup(pantalla_pygame)


def main():
    # SDL por defecto ignora eventos de joystick cuando la ventana no
    # tiene foco -- con el driver "offscreen" (sin ventana real / gestor
    # de ventanas) eso significa que nunca los procesa. Forzamos que los
    # tome igual, ANTES de pygame.init().
    os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

    pygame.init()

    # La GPU de este dispositivo no inicializa correctamente (fallo del
    # kernel al buscar su regulador de energia -- ver README). Como
    # R36ARIA es una interfaz 2D simple, no necesita GPU en absoluto:
    # dibujamos todo sobre una superficie normal de pygame y la volcamos
    # nosotros mismos directo al framebuffer (/dev/fb0), sin pasar por
    # SDL_VIDEODRIVER/KMSDRM/EGL para nada.
    #
    # Igual necesitamos que el modulo de video de SDL este inicializado
    # (para que el bucle de eventos y el joystick funcionen bien), asi que
    # forzamos el driver "offscreen" -- el unico que no requiere GPU y que
    # sabemos que siempre inicializa sin problema en este dispositivo.
    os.environ["SDL_VIDEODRIVER"] = "offscreen"
    pygame.display.set_mode((theme.ANCHO, theme.ALTO))
    pygame.mouse.set_visible(False)

    joy = inicializar_joystick()
    if joy is not None:
        print(f"[R36ARIA] Joystick detectado: {joy.get_name()} (ejes={joy.get_numaxes()} botones={joy.get_numbuttons()} hats={joy.get_numhats()})")
    else:
        print("[R36ARIA] No se detecto ningun joystick")

    fb = fbdev.FramebufferDirecto()
    try:
        fb.abrir()
        print(f"[R36ARIA] Framebuffer directo: {fb.ancho}x{fb.alto} @ {fb.bits_por_pixel}bpp, line_length={fb.line_length}")
    except Exception:
        import traceback
        print("[R36ARIA] No se pudo abrir el framebuffer directo:")
        traceback.print_exc()
        fb = None

    pantalla_pygame = pygame.Surface((theme.ANCHO, theme.ALTO))

    theme.inicializar_fuentes()

    aria2_client.iniciar_aria2()

    opciones = config.cargar_opciones()
    estado["opciones_categorias"] = opciones
    estado["opciones_menu"] = construir_menu_principal(opciones)

    reloj = pygame.time.Clock()
    pantalla_previa_frame = estado["pantalla"]

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    salir_programa()
                else:
                    registrar_evento_direccion(event)
                    procesar_input(event)

            # Combinacion de salida forzada SELECT+START, implementada
            # nosotros mismos (ya no usamos gptokeyb, que interceptaba
            # todo el joystick e impedia que R36ARIA leyera los botones).
            if joy is not None:
                if joy.get_button(BOTON_SELECT) and joy.get_button(BOTON_START):
                    salir_programa()

            # Si la pantalla cambio este frame (por ejemplo al confirmar
            # una opcion), no arrastramos un movimiento sostenido de la
            # pantalla anterior.
            if estado["pantalla"] != pantalla_previa_frame:
                limpiar_repeticion()
                pantalla_previa_frame = estado["pantalla"]

            aplicar_repeticion_direccion()

            actualizar_logica()
            dibujar(pantalla_pygame)
            if fb is not None:
                fb.presentar(pantalla_pygame)
            else:
                pygame.display.flip()
            reloj.tick(FPS)
    except KeyboardInterrupt:
        salir_programa()
    finally:
        if fb is not None:
            fb.cerrar()


if __name__ == "__main__":
    main()
