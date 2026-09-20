import os
import pygame
from ui import theme
from core import config, aria2_client
from core.state_manager import (
    estado, MENU_PRINCIPAL, NUEVOS_TORRENTS_LISTA, ENTRADA_TEXTO,
)
from core.input_handler import BOTON_A, BOTON_B, BOTON_X, BOTON_Y, BOTON_START, BOTON_L, obtener_direccion_input
from ui.keyboard import dibujar_grilla_teclado, mover_cursor_teclado, letra_con_caso_actual
from ui.popups import mostrar_error_popup


def _escanear_torrents_nuevos():
    carpeta = aria2_client.CARPETA_TORRENTS
    if not os.path.isdir(carpeta):
        return []

    ya_usados = {
        opcion["torrent_path"] for opcion in estado["opciones_categorias"] if "torrent_path" in opcion
    }

    encontrados = []
    for nombre_archivo in sorted(os.listdir(carpeta)):
        if nombre_archivo.lower().endswith(".torrent") and nombre_archivo not in ya_usados:
            encontrados.append(nombre_archivo)
    return encontrados


def iniciar_flujo_agregar_torrents():
    encontrados = _escanear_torrents_nuevos()
    estado["torrents_nuevos_encontrados"] = encontrados
    estado["torrents_nuevos_indice_cursor"] = 0

    if not encontrados:
        mostrar_error_popup("No se encontraron torrents nuevos en torrents/", MENU_PRINCIPAL)
        return

    estado["pantalla"] = NUEVOS_TORRENTS_LISTA


# ---------- Pantalla: lista de torrents nuevos encontrados ----------

def _calcular_offset_scroll(indice_cursor, total_items):
    if indice_cursor < theme.ITEMS_VISIBLES:
        return 0
    return min(indice_cursor - theme.ITEMS_VISIBLES + 1, max(0, total_items - theme.ITEMS_VISIBLES))


def mover_cursor_lista_nuevos(direccion):
    _, y = direccion
    total = len(estado["torrents_nuevos_encontrados"])
    if total == 0:
        return
    if y == 1:
        estado["torrents_nuevos_indice_cursor"] = max(0, estado["torrents_nuevos_indice_cursor"] - 1)
    elif y == -1:
        estado["torrents_nuevos_indice_cursor"] = min(total - 1, estado["torrents_nuevos_indice_cursor"] + 1)


def manejar_input_lista_nuevos(event):
    direccion = obtener_direccion_input(event)
    if direccion:
        mover_cursor_lista_nuevos(direccion)
        return

    if event.type == pygame.JOYBUTTONDOWN:
        if event.button == BOTON_A:
            lista = estado["torrents_nuevos_encontrados"]
            if lista:
                archivo = lista[estado["torrents_nuevos_indice_cursor"]]
                estado["torrent_actual_nuevo"] = archivo
                estado["modo_entrada_texto"] = "nombre"
                # Sugerencia inicial: el nombre del archivo sin la extension
                # .torrent. El usuario puede aceptarlo tal cual (START) o
                # editarlo/borrarlo y escribir otro.
                estado["valor_entrada_texto"] = os.path.splitext(archivo)[0]
                estado["fila_teclado"] = 0
                estado["col_teclado"] = 0
                estado["pantalla"] = ENTRADA_TEXTO

        elif event.button == BOTON_B:
            estado["pantalla"] = MENU_PRINCIPAL


def dibujar_lista_nuevos(pantalla):
    pantalla.fill(theme.COLOR_FONDO)
    theme.dibujar_header(pantalla, "Torrents nuevos")

    lista = estado["torrents_nuevos_encontrados"]
    offset = _calcular_offset_scroll(estado["torrents_nuevos_indice_cursor"], len(lista))
    visibles = lista[offset:offset + theme.ITEMS_VISIBLES]

    for i, nombre_archivo in enumerate(visibles):
        idx_real = offset + i
        y = theme.Y_INICIO_LISTA + i * theme.ALTURA_ITEM

        es_actual = idx_real == estado["torrents_nuevos_indice_cursor"]
        if es_actual:
            pygame.draw.rect(pantalla, theme.COLOR_CURSOR,
                              (10, y, theme.ANCHO - 20, theme.ALTURA_ITEM - 4), border_radius=6)

        color = theme.COLOR_ACENTO if es_actual else theme.COLOR_TEXTO
        texto = theme.fuente_item.render(nombre_archivo, True, color)
        pantalla.blit(texto, (26, y + 6))

    if not lista:
        texto = theme.fuente_item.render("Sin torrents nuevos", True, theme.COLOR_TEXTO_APAGADO)
        pantalla.blit(texto, texto.get_rect(center=(theme.ANCHO // 2, theme.ALTO // 2)))

    theme.dibujar_footer(pantalla, "A: Configurar   B: Volver al menu")


# ---------- Pantalla: entrada de texto (nombre y luego carpeta destino) ----------

def manejar_input_entrada_texto(event):
    direccion = obtener_direccion_input(event)
    if direccion:
        mover_cursor_teclado(direccion)
        return

    if event.type != pygame.JOYBUTTONDOWN:
        return

    if event.button == BOTON_A:
        estado["valor_entrada_texto"] += letra_con_caso_actual()

    elif event.button == BOTON_L:
        estado["mayusculas"] = not estado["mayusculas"]

    elif event.button == BOTON_Y:
        estado["valor_entrada_texto"] = estado["valor_entrada_texto"][:-1]

    elif event.button == BOTON_X:
        estado["valor_entrada_texto"] += " "

    elif event.button == BOTON_START:
        _confirmar_entrada_texto()

    elif event.button == BOTON_B:
        _cancelar_entrada_texto()


def _confirmar_entrada_texto():
    valor = estado["valor_entrada_texto"].strip()
    if not valor:
        return  # no dejamos confirmar vacio

    if estado["modo_entrada_texto"] == "nombre":
        estado["nuevo_torrent_nombre"] = valor
        estado["modo_entrada_texto"] = "destino"
        estado["valor_entrada_texto"] = ""
        estado["fila_teclado"] = 0
        estado["col_teclado"] = 0
        return  # se queda en ENTRADA_TEXTO, solo cambia el modo/titulo

    # modo == "destino": ya tenemos nombre + torrent + carpeta, se guarda
    nueva_opcion = {
        "nombre": estado["nuevo_torrent_nombre"],
        "torrent_path": estado["torrent_actual_nuevo"],
        "carpeta_destino": valor,
    }
    estado["opciones_categorias"].append(nueva_opcion)

    try:
        config.guardar_opciones(estado["opciones_categorias"])
    except Exception as e:
        print(f"[R36ARIA] No se pudo guardar options.json: {e}")

    from ui.menu_screen import construir_menu_principal
    estado["opciones_menu"] = construir_menu_principal(estado["opciones_categorias"])

    if estado["torrent_actual_nuevo"] in estado["torrents_nuevos_encontrados"]:
        estado["torrents_nuevos_encontrados"].remove(estado["torrent_actual_nuevo"])
    estado["torrents_nuevos_indice_cursor"] = min(
        estado["torrents_nuevos_indice_cursor"],
        max(0, len(estado["torrents_nuevos_encontrados"]) - 1),
    )

    if estado["torrents_nuevos_encontrados"]:
        estado["pantalla"] = NUEVOS_TORRENTS_LISTA
    else:
        estado["pantalla"] = MENU_PRINCIPAL


def _cancelar_entrada_texto():
    if estado["torrents_nuevos_encontrados"]:
        estado["pantalla"] = NUEVOS_TORRENTS_LISTA
    else:
        estado["pantalla"] = MENU_PRINCIPAL


def dibujar_entrada_texto(pantalla):
    pantalla.fill(theme.COLOR_FONDO)
    titulo = "Nombre para el torrent" if estado["modo_entrada_texto"] == "nombre" else "Carpeta destino (ruta completa)"
    theme.dibujar_header(pantalla, titulo)

    caja_texto = pygame.Rect(20, theme.ALTO_HEADER + 10, theme.ANCHO - 40, 34)
    pygame.draw.rect(pantalla, (30, 30, 30), caja_texto, border_radius=6)
    pygame.draw.rect(pantalla, theme.COLOR_ACENTO, caja_texto, width=2, border_radius=6)

    valor = estado["valor_entrada_texto"]
    texto_mostrado = valor or "..."
    color = (255, 255, 255) if valor else theme.COLOR_TEXTO_APAGADO
    texto = theme.fuente_item.render(texto_mostrado, True, color)
    pantalla.blit(texto, (caja_texto.x + 10, caja_texto.y + 6))

    dibujar_grilla_teclado(pantalla, caja_texto.bottom + 10)

    theme.dibujar_footer(pantalla, "A: Escribir  L: Mayus/Minus  Y: Borrar  X: Espacio  START: Confirmar  B: Cancelar")
