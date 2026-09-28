import pygame
from ui import theme
from core.state_manager import (
    estado, MENU_PRINCIPAL, OPCIONES, SELECCIONAR_CATEGORIA, ENTRADA_TEXTO,
    REORDENAR_TORRENTS, CONFIRMAR_CANCELAR,
)
from core.input_handler import BOTON_A, BOTON_B, BOTON_X, BOTON_Y, obtener_direccion_input
from core.i18n import t
from core import settings, config
from ui.popups import manejar_input_confirmar_cancelar


def _guardar_y_refrescar():
    try:
        config.guardar_opciones(estado["opciones_categorias"])
    except Exception as e:
        print(f"[R36ARIA] No se pudo guardar options.json: {e}")

    from ui.menu_screen import construir_menu_principal
    estado["opciones_menu"] = construir_menu_principal(estado["opciones_categorias"])


def _opciones_menu():
    """Se arma en cada frame (no como lista fija) para que los titulos
    reflejen el idioma actual, incluido el de la propia entrada de idioma."""
    return [
        {"titulo": t("renombrar_torrent"), "modo": "nombre"},
        {"titulo": t("cambiar_carpeta_descarga"), "modo": "carpeta"},
        {"titulo": t("reordenar_torrents"), "modo": "reordenar"},
        {"titulo": t("borrar_torrent"), "modo": "borrar"},
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

            if entrada["modo"] == "reordenar":
                estado["reordenar_indice_cursor"] = 0
                estado["pantalla"] = REORDENAR_TORRENTS
                return

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


# ---------- Lista de categorias existentes para elegir cual editar/borrar ----------

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

            if estado["editar_categoria_modo"] == "borrar":
                estado["pantalla_previa"] = SELECCIONAR_CATEGORIA
                estado["confirmar_indice"] = 1  # arranca en "No"
                estado["mensaje_confirmar"] = "confirmar_borrar_torrent"
                estado["pantalla"] = CONFIRMAR_CANCELAR
                return

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


def _borrar_categoria_actual():
    idx = estado["editar_categoria_indice_actual"]
    categorias = estado["opciones_categorias"]
    if idx is not None and 0 <= idx < len(categorias):
        del categorias[idx]
        _guardar_y_refrescar()
    estado["editar_categoria_indice_cursor"] = min(
        estado["editar_categoria_indice_cursor"], max(0, len(categorias) - 1)
    )
    estado["pantalla"] = SELECCIONAR_CATEGORIA


def manejar_input_confirmar_borrado(event):
    manejar_input_confirmar_cancelar(event, on_confirmar_si=_borrar_categoria_actual)


def dibujar_seleccionar_categoria(pantalla):
    pantalla.fill(theme.COLOR_FONDO)
    if estado["editar_categoria_modo"] == "nombre":
        titulo = t("renombrar_elegir_torrent")
    elif estado["editar_categoria_modo"] == "carpeta":
        titulo = t("cambiar_carpeta_elegir_torrent")
    else:
        titulo = t("borrar_elegir_torrent")
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


# ---------- Reordenar torrents ----------

def mover_cursor_reordenar(direccion):
    _, y = direccion
    total = len(estado["opciones_categorias"])
    if total == 0:
        return
    if y == 1:
        estado["reordenar_indice_cursor"] = max(0, estado["reordenar_indice_cursor"] - 1)
    elif y == -1:
        estado["reordenar_indice_cursor"] = min(total - 1, estado["reordenar_indice_cursor"] + 1)


def manejar_input_reordenar(event):
    direccion = obtener_direccion_input(event)
    if direccion:
        mover_cursor_reordenar(direccion)
        return

    if event.type != pygame.JOYBUTTONDOWN:
        return

    categorias = estado["opciones_categorias"]
    idx = estado["reordenar_indice_cursor"]

    if event.button == BOTON_X:  # subir
        if idx > 0:
            categorias[idx - 1], categorias[idx] = categorias[idx], categorias[idx - 1]
            estado["reordenar_indice_cursor"] -= 1
            _guardar_y_refrescar()

    elif event.button == BOTON_Y:  # bajar
        if idx < len(categorias) - 1:
            categorias[idx + 1], categorias[idx] = categorias[idx], categorias[idx + 1]
            estado["reordenar_indice_cursor"] += 1
            _guardar_y_refrescar()

    elif event.button == BOTON_B:
        estado["pantalla"] = OPCIONES


def dibujar_reordenar(pantalla):
    pantalla.fill(theme.COLOR_FONDO)
    theme.dibujar_header(pantalla, t("reordenar_titulo"))

    categorias = estado["opciones_categorias"]
    offset = _calcular_offset_scroll(estado["reordenar_indice_cursor"], len(categorias))
    visibles = categorias[offset:offset + theme.ITEMS_VISIBLES]

    for i, categoria in enumerate(visibles):
        idx_real = offset + i
        y = theme.Y_INICIO_LISTA + i * theme.ALTURA_ITEM

        es_actual = idx_real == estado["reordenar_indice_cursor"]
        if es_actual:
            pygame.draw.rect(pantalla, theme.COLOR_CURSOR,
                              (10, y, theme.ANCHO - 20, theme.ALTURA_ITEM - 4), border_radius=6)

        color = theme.COLOR_ACENTO if es_actual else theme.COLOR_TEXTO
        texto = theme.fuente_item.render(categoria["nombre"], True, color)
        pantalla.blit(texto, (26, y + 6))

    if not categorias:
        texto = theme.fuente_item.render(t("no_hay_torrents_cargados"), True, theme.COLOR_TEXTO_APAGADO)
        pantalla.blit(texto, texto.get_rect(center=(theme.ANCHO // 2, theme.ALTO // 2)))

    theme.dibujar_footer(pantalla, t("reordenar_footer"))
