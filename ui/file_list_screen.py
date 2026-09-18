import os
import pygame
from ui import theme
from core.state_manager import estado, MENU_PRINCIPAL, DESCARGANDO
from core.input_handler import BOTON_A, BOTON_B, BOTON_X, BOTON_SELECT, obtener_direccion_input
from core import aria2_client
from ui.keyboard import obtener_archivos_filtrados, manejar_input_teclado, dibujar_overlay_busqueda
from core.state_manager import resetear_para_menu


def _calcular_offset_scroll(indice_cursor, total_items):
    if indice_cursor < theme.ITEMS_VISIBLES:
        return 0
    return min(indice_cursor - theme.ITEMS_VISIBLES + 1, max(0, total_items - theme.ITEMS_VISIBLES))


def mover_cursor_lista(direccion):
    archivos_filtrados = obtener_archivos_filtrados()
    _, y = direccion
    if y == 1:
        estado["indice_cursor"] = max(0, estado["indice_cursor"] - 1)
    elif y == -1:
        estado["indice_cursor"] = min(len(archivos_filtrados) - 1, estado["indice_cursor"] + 1)


def manejar_input_lista_archivos(event):
    if event.type == pygame.JOYBUTTONDOWN and event.button == BOTON_SELECT:
        estado["buscando"] = not estado["buscando"]
        if estado["buscando"]:
            estado["fila_teclado"] = 0
            estado["col_teclado"] = 0
        return

    if estado["buscando"]:
        manejar_input_teclado(event)
        return

    archivos_filtrados = obtener_archivos_filtrados()

    direccion = obtener_direccion_input(event)
    if direccion:
        mover_cursor_lista(direccion)
        return

    if event.type == pygame.JOYBUTTONDOWN:
        if event.button == BOTON_A:
            if archivos_filtrados:
                archivo = archivos_filtrados[estado["indice_cursor"]]
                estado["indice_elegido"] = archivo["index"]  # index real de aria2, no posicion

        elif event.button == BOTON_X:
            if estado["indice_elegido"] is not None:
                _entrar_descargando()

        elif event.button == BOTON_B:
            resetear_para_menu()


def _entrar_descargando():
    aria2_client.iniciar_descarga_archivo(estado["gid"], estado["indice_elegido"])
    estado["ultimo_completado"] = 0
    estado["ultimo_avance_ts"] = pygame.time.get_ticks() / 1000.0
    estado["progreso"] = 0.0
    estado["pantalla"] = DESCARGANDO


def dibujar_lista_archivos(pantalla):
    archivos_filtrados = obtener_archivos_filtrados()

    pantalla.fill(theme.COLOR_FONDO)
    nombre = estado["opcion_actual"]["nombre"] if estado["opcion_actual"] else ""
    theme.dibujar_header(pantalla, nombre)

    offset = _calcular_offset_scroll(estado["indice_cursor"], len(archivos_filtrados))
    visibles = archivos_filtrados[offset:offset + theme.ITEMS_VISIBLES]

    for i, archivo in enumerate(visibles):
        idx_real_lista = offset + i
        y = theme.Y_INICIO_LISTA + i * theme.ALTURA_ITEM

        es_cursor = idx_real_lista == estado["indice_cursor"]
        es_elegido = archivo["index"] == estado["indice_elegido"]

        if es_cursor:
            pygame.draw.rect(pantalla, theme.COLOR_CURSOR,
                              (10, y, theme.ANCHO - 20, theme.ALTURA_ITEM - 4), border_radius=6)

        nombre_archivo = os.path.basename(archivo["path"])
        color_texto = theme.COLOR_ACENTO if es_elegido else theme.COLOR_TEXTO
        texto = theme.fuente_item.render(nombre_archivo, True, color_texto)
        pantalla.blit(texto, (26, y + 6))

        if es_elegido:
            marca = theme.fuente_item.render("OK", True, theme.COLOR_OK)
            pantalla.blit(marca, (theme.ANCHO - 50, y + 6))

    if not archivos_filtrados:
        texto = theme.fuente_item.render("Sin resultados", True, theme.COLOR_TEXTO_APAGADO)
        pantalla.blit(texto, texto.get_rect(center=(theme.ANCHO // 2, theme.ALTO // 2)))

    theme.dibujar_footer(pantalla, "A: Elegir  X: Descargar  SELECT: Buscar  B: Volver")

    if estado["buscando"]:
        dibujar_overlay_busqueda(pantalla)
