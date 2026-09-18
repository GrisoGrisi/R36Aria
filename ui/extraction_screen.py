import os
import pygame
from ui import theme
from core.state_manager import estado, DESCARGA_COMPLETA, EXTRAYENDO, MENU_PRINCIPAL
from core.input_handler import BOTON_A, obtener_direccion_input
from core import archivos
from ui.popups import mostrar_error_popup

OPCIONES = [
    "Mantener el archivo como esta",
    "Extraer y borrar el comprimido",
    "Extraer y mantener el comprimido",
]


# ---------- Pantalla de eleccion (3 opciones) ----------

def manejar_input_eleccion_archivo(event):
    direccion = obtener_direccion_input(event)
    if direccion:
        _, y = direccion
        if y == 1:
            estado["accion_archivo_indice"] = max(0, estado["accion_archivo_indice"] - 1)
        elif y == -1:
            estado["accion_archivo_indice"] = min(len(OPCIONES) - 1, estado["accion_archivo_indice"] + 1)
        return

    if event.type == pygame.JOYBUTTONDOWN and event.button == BOTON_A:
        _ejecutar_accion_elegida()


def _ejecutar_accion_elegida():
    idx = estado["accion_archivo_indice"]

    if idx == 0:
        # Mantener como esta: no hacemos nada mas.
        estado["pantalla"] = DESCARGA_COMPLETA
        return

    ruta = estado["ruta_descargada"]
    carpeta_destino = os.path.dirname(ruta)  # el comprimido se extrae en su misma carpeta

    try:
        estado["extractor"] = archivos.ExtractorIncremental(ruta, carpeta_destino)
    except Exception as e:
        print(f"[R36ARIA] Error al iniciar la extraccion de '{ruta}': {e}")
        mostrar_error_popup("No se pudo extraer el archivo", MENU_PRINCIPAL)
        return

    estado["progreso_extraccion"] = 0.0
    estado["borrar_comprimido_al_terminar"] = (idx == 1)
    estado["pantalla"] = EXTRAYENDO


def dibujar_eleccion_archivo(pantalla):
    pantalla.fill(theme.COLOR_FONDO)
    theme.dibujar_header(pantalla, "Archivo comprimido")

    texto_info = theme.fuente_footer.render(
        "Se detecto un archivo comprimido, que queres hacer?",
        True, theme.COLOR_TEXTO_APAGADO
    )
    pantalla.blit(texto_info, (20, theme.ALTO_HEADER + 16))

    y_inicio = theme.ALTO_HEADER + 60
    for i, opcion in enumerate(OPCIONES):
        y = y_inicio + i * theme.ALTURA_ITEM
        es_actual = i == estado["accion_archivo_indice"]

        if es_actual:
            pygame.draw.rect(pantalla, theme.COLOR_CURSOR,
                              (10, y, theme.ANCHO - 20, theme.ALTURA_ITEM - 4), border_radius=6)

        color = theme.COLOR_ACENTO if es_actual else theme.COLOR_TEXTO
        texto = theme.fuente_item.render(opcion, True, color)
        pantalla.blit(texto, (26, y + 6))

    theme.dibujar_footer(pantalla, "A: Elegir   Dpad: Navegar")


# ---------- Pantalla de extraccion (barra de progreso) ----------

def actualizar_extrayendo():
    """Se llama una vez por frame mientras estado['pantalla'] == EXTRAYENDO.
    Cada llamada procesa un bloque acotado (ver BYTES_POR_PASO), asi que
    no bloquea el loop principal aunque el comprimido sea grande."""
    extractor = estado["extractor"]
    if extractor is None:
        estado["pantalla"] = DESCARGA_COMPLETA
        return

    try:
        termino = extractor.paso()
    except Exception as e:
        print(f"[R36ARIA] Error durante la extraccion: {e}")
        extractor.cerrar()
        estado["extractor"] = None
        mostrar_error_popup("Error al extraer el archivo", MENU_PRINCIPAL)
        return

    if extractor.bytes_totales:
        estado["progreso_extraccion"] = extractor.bytes_hechos / extractor.bytes_totales
    else:
        estado["progreso_extraccion"] = 1.0 if termino else 0.0

    if termino:
        ruta_comprimido = estado["ruta_descargada"]
        if estado["borrar_comprimido_al_terminar"]:
            try:
                os.remove(ruta_comprimido)
            except OSError as e:
                print(f"[R36ARIA] No se pudo borrar el comprimido original: {e}")

        estado["extractor"] = None
        estado["pantalla"] = DESCARGA_COMPLETA


def dibujar_extrayendo(pantalla):
    pantalla.fill(theme.COLOR_FONDO)
    theme.dibujar_header(pantalla, "Extrayendo...")

    ancho_barra = theme.ANCHO - 80
    alto_barra = 30
    x = 40
    y = theme.ALTO // 2 - alto_barra // 2

    pygame.draw.rect(pantalla, (40, 40, 50), (x, y, ancho_barra, alto_barra), border_radius=6)
    ancho_relleno = int(ancho_barra * estado["progreso_extraccion"])
    pygame.draw.rect(pantalla, theme.COLOR_ACENTO, (x, y, ancho_relleno, alto_barra), border_radius=6)
    pygame.draw.rect(pantalla, (80, 80, 90), (x, y, ancho_barra, alto_barra), width=2, border_radius=6)

    porcentaje = theme.fuente_item.render(f"{int(estado['progreso_extraccion'] * 100)}%", True, (255, 255, 255))
    pantalla.blit(porcentaje, porcentaje.get_rect(center=(theme.ANCHO // 2, y - 24)))

    theme.dibujar_footer(pantalla, "Espera un momento...")
