import os
import pygame
from ui import theme
from core.state_manager import estado, FILAS_TECLADO
from core.input_handler import BOTON_A, BOTON_B, BOTON_X, BOTON_Y, BOTON_START, obtener_direccion_input


def obtener_archivos_filtrados():
    if not estado["texto_busqueda"]:
        return estado["archivos"]
    q = estado["texto_busqueda"].lower()
    return [a for a in estado["archivos"] if q in os.path.basename(a["path"]).lower()]


def mover_cursor_teclado(direccion):
    x, y = direccion
    if y == 1:
        estado["fila_teclado"] = max(0, estado["fila_teclado"] - 1)
    elif y == -1:
        estado["fila_teclado"] = min(len(FILAS_TECLADO) - 1, estado["fila_teclado"] + 1)

    fila_actual = FILAS_TECLADO[estado["fila_teclado"]]
    if x == -1:
        estado["col_teclado"] = max(0, estado["col_teclado"] - 1)
    elif x == 1:
        estado["col_teclado"] = min(len(fila_actual) - 1, estado["col_teclado"] + 1)

    estado["col_teclado"] = min(estado["col_teclado"], len(fila_actual) - 1)


def manejar_input_teclado(event):
    direccion = obtener_direccion_input(event)
    if direccion:
        mover_cursor_teclado(direccion)
        return

    if event.type == pygame.JOYBUTTONDOWN:
        if event.button == BOTON_A:
            letra = FILAS_TECLADO[estado["fila_teclado"]][estado["col_teclado"]]
            estado["texto_busqueda"] += letra
            _clamp_cursor()

        elif event.button == BOTON_Y:
            estado["texto_busqueda"] = estado["texto_busqueda"][:-1]
            _clamp_cursor()

        elif event.button == BOTON_X:
            estado["texto_busqueda"] += " "
            _clamp_cursor()

        elif event.button == BOTON_START:
            estado["buscando"] = False

        elif event.button == BOTON_B:
            estado["texto_busqueda"] = ""
            estado["buscando"] = False
            _clamp_cursor()


def _clamp_cursor():
    """Evita que el cursor de la lista quede fuera de rango cuando el filtro cambia."""
    filtrados = obtener_archivos_filtrados()
    estado["indice_cursor"] = min(estado["indice_cursor"], max(0, len(filtrados) - 1))


def dibujar_overlay_busqueda(pantalla):
    overlay = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    pantalla.blit(overlay, (0, 0))

    caja_texto = pygame.Rect(30, 20, theme.ANCHO - 60, 34)
    pygame.draw.rect(pantalla, (30, 30, 30), caja_texto, border_radius=6)
    pygame.draw.rect(pantalla, theme.COLOR_ACENTO, caja_texto, width=2, border_radius=6)

    texto_mostrado = estado["texto_busqueda"] or "Buscar..."
    color = (255, 255, 255) if estado["texto_busqueda"] else theme.COLOR_TEXTO_APAGADO
    texto = theme.fuente_item.render(texto_mostrado, True, color)
    pantalla.blit(texto, (caja_texto.x + 10, caja_texto.y + 6))

    y_inicio = 70
    alto_tecla = 34
    for fi, fila in enumerate(FILAS_TECLADO):
        ancho_tecla = (theme.ANCHO - 40) // len(fila)
        for ci, letra in enumerate(fila):
            x = 20 + ci * ancho_tecla
            y = y_inicio + fi * (alto_tecla + 6)
            rect = pygame.Rect(x, y, ancho_tecla - 4, alto_tecla)

            es_actual = (fi == estado["fila_teclado"] and ci == estado["col_teclado"])
            color_fondo = theme.COLOR_CURSOR if es_actual else (45, 45, 55)
            pygame.draw.rect(pantalla, color_fondo, rect, border_radius=4)

            txt_mostrado = "ESPACIO" if letra == " " else letra
            txt = theme.fuente_item.render(txt_mostrado, True, (255, 255, 255))
            pantalla.blit(txt, txt.get_rect(center=rect.center))

    ayuda = theme.fuente_footer.render(
        "A: Escribir  Y: Borrar  X: Espacio  START: Cerrar  B: Cancelar",
        True, theme.COLOR_TEXTO_APAGADO
    )
    pantalla.blit(ayuda, (16, theme.ALTO - theme.ALTO_FOOTER + 9))
