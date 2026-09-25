import pygame
from ui import theme
from core.state_manager import (
    estado, MENU_PRINCIPAL, OPCIONES, SELECCIONAR_CATEGORIA, ENTRADA_TEXTO,
)
from core.input_handler import BOTON_A, BOTON_B, obtener_direccion_input
from core.i18n import t
from core import settings


def _opciones_menu():
    """Se arma en cada frame (no como lista fija) para que los titulos
    reflejen el idioma actual, incluido el de la propia entrada de idioma."""
    return [
        {"titulo": t("renombrar_torrent"), "modo": "nombre"},
        {"titulo": t("cambiar_carpeta_descarga"), "modo": "carpeta"},
        {"titulo": t("idioma_entrada"), "modo": "idioma"},
    ]


# ---------- Submenu de Opciones ----------

def mover_cursor_opciones(direccion):
    _, y = direccion
    total = len(_opciones_menu())
    if y == 1:
        estado["opciones_menu_cursor"] = max(0, estado["opciones_menu_cursor"] - 1)
    elif y == -1:
        estado["opciones_menu_cursor"] = min(total - 1, estado["opciones_menu_cursor"] + 1)


def manejar_input_opciones(event):
    direccion = obtener_direccion_input(event)
    if direccion:
        mover_cursor_opciones(direccion)
        return

    if event.type == pygame.JOYBUTTONDOWN:
        if event.button == BOTON_A:
            entrada = _opciones_menu()[estado["opciones_menu_cursor"]]

            if entrada["modo"] == "idioma":
                estado["idioma"] = "en" if estado["idioma"] == "es" else "es"
                settings.guardar_idioma(estado["idioma"])
                return  # se queda en Opciones, el titulo ya cambia solo

            estado["editar_categoria_modo"] = entrada["modo"]
            estado["editar_categoria_indice_cursor"] = 0
            estado["pantalla"] = SELECCIONAR_CATEGORIA

        elif event.button == BOTON_B:
            estado["pantalla"] = MENU_PRINCIPAL


def dibujar_opciones(pantalla):
    pantalla.fill(theme.COLOR_FONDO)
    theme.dibujar_header(pantalla, t("opciones_titulo"))

    for i, entrada in enumerate(_opciones_menu()):
        y = theme.Y_INICIO_LISTA + i * theme.ALTURA_ITEM
        es_actual = i == estado["opciones_menu_cursor"]

        if es_actual:
            pygame.draw.rect(pantalla, theme.COLOR_CURSOR,
                              (10, y, theme.ANCHO - 20, theme.ALTURA_ITEM - 4), border_radius=6)

        color = theme.COLOR_ACENTO if es_actual else theme.COLOR_TEXTO
        texto = theme.fuente_item.render(entrada["titulo"], True, color)
        pantalla.blit(texto, (26, y + 6))

    theme.dibujar_footer(pantalla, t("opciones_footer"))


# ---------- Lista de categorias existentes para elegir cual editar ----------

def _calcular_offset_scroll(indice_cursor, total_items):
    if indice_cursor < theme.ITEMS_VISIBLES:
        return 0
    return min(indice_cursor - theme.ITEMS_VISIBLES + 1, max(0, total_items - theme.ITEMS_VISIBLES))


def mover_cursor_seleccionar_categoria(direccion):
    _, y = direccion
    total = len(estado["opciones_categorias"])
    if total == 0:
        return
    if y == 1:
        estado["editar_categoria_indice_cursor"] = max(0, estado["editar_categoria_indice_cursor"] - 1)
    elif y == -1:
        estado["editar_categoria_indice_cursor"] = min(total - 1, estado["editar_categoria_indice_cursor"] + 1)


def manejar_input_seleccionar_categoria(event):
    direccion = obtener_direccion_input(event)
    if direccion:
        mover_cursor_seleccionar_categoria(direccion)
        return

    if event.type == pygame.JOYBUTTONDOWN:
        if event.button == BOTON_A:
            categorias = estado["opciones_categorias"]
            if not categorias:
                return
            idx = estado["editar_categoria_indice_cursor"]
            estado["editar_categoria_indice_actual"] = idx

            if estado["editar_categoria_modo"] == "nombre":
                estado["modo_entrada_texto"] = "editar_nombre"
                estado["valor_entrada_texto"] = categorias[idx]["nombre"]
            else:
                estado["modo_entrada_texto"] = "editar_carpeta"
                estado["valor_entrada_texto"] = categorias[idx].get("carpeta_destino", "")

            estado["fila_teclado"] = 0
            estado["col_teclado"] = 0
            estado["pantalla"] = ENTRADA_TEXTO

        elif event.button == BOTON_B:
            estado["pantalla"] = OPCIONES


def dibujar_seleccionar_categoria(pantalla):
    pantalla.fill(theme.COLOR_FONDO)
    titulo = t("renombrar_elegir_torrent") if estado["editar_categoria_modo"] == "nombre" else t("cambiar_carpeta_elegir_torrent")
    theme.dibujar_header(pantalla, titulo)

    categorias = estado["opciones_categorias"]
    offset = _calcular_offset_scroll(estado["editar_categoria_indice_cursor"], len(categorias))
    visibles = categorias[offset:offset + theme.ITEMS_VISIBLES]

    for i, categoria in enumerate(visibles):
        idx_real = offset + i
        y = theme.Y_INICIO_LISTA + i * theme.ALTURA_ITEM

        es_actual = idx_real == estado["editar_categoria_indice_cursor"]
        if es_actual:
            pygame.draw.rect(pantalla, theme.COLOR_CURSOR,
                              (10, y, theme.ANCHO - 20, theme.ALTURA_ITEM - 4), border_radius=6)

        color = theme.COLOR_ACENTO if es_actual else theme.COLOR_TEXTO
        texto = theme.fuente_item.render(categoria["nombre"], True, color)
        pantalla.blit(texto, (26, y + 6))

    if not categorias:
        texto = theme.fuente_item.render(t("no_hay_torrents_cargados"), True, theme.COLOR_TEXTO_APAGADO)
        pantalla.blit(texto, texto.get_rect(center=(theme.ANCHO // 2, theme.ALTO // 2)))

    theme.dibujar_footer(pantalla, t("seleccionar_categoria_footer"))
