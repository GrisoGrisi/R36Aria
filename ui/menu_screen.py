import pygame
from ui import theme
from core.state_manager import estado, RESOLVIENDO_METADATA, LISTA_ARCHIVOS, MENU_PRINCIPAL, OPCIONES
from core.input_handler import BOTON_A, BOTON_SELECT, BOTON_START, obtener_direccion_input
from core import aria2_client
from core.i18n import t
from ui.popups import mostrar_error_popup


def construir_menu_principal(opciones_config):
    opciones_menu = list(opciones_config)
    opciones_menu.append({"nombre": "Salir", "tipo": "salir"})
    return opciones_menu


def mover_cursor_menu(direccion):
    _, y = direccion
    if y == 1:
        estado["indice_menu"] = max(0, estado["indice_menu"] - 1)
    elif y == -1:
        estado["indice_menu"] = min(len(estado["opciones_menu"]) - 1, estado["indice_menu"] + 1)


def manejar_input_menu(event, on_salir):
    direccion = obtener_direccion_input(event)
    if direccion:
        mover_cursor_menu(direccion)
        return

    if event.type == pygame.JOYBUTTONDOWN:
        if event.button == BOTON_A:
            opcion = estado["opciones_menu"][estado["indice_menu"]]
            if opcion.get("tipo") == "salir":
                on_salir()
            elif "torrent_path" in opcion:
                _entrar_con_torrent_local(opcion)
            else:
                _entrar_resolviendo_metadata(opcion)

        elif event.button == BOTON_START:
            from ui.agregar_torrent_screen import iniciar_flujo_agregar_torrents
            iniciar_flujo_agregar_torrents()

        elif event.button == BOTON_SELECT:
            estado["pantalla"] = OPCIONES


def _entrar_resolviendo_metadata(opcion_elegida):
    gid = aria2_client.agregar_magnet_en_pausa(opcion_elegida["magnet"])
    estado["gid"] = gid
    estado["opcion_actual"] = opcion_elegida
    estado["inicio_resolucion"] = pygame.time.get_ticks() / 1000.0
    estado["pantalla"] = RESOLVIENDO_METADATA


def _entrar_con_torrent_local(opcion_elegida):
    """Un .torrent local ya trae toda la metadata: se salta la pantalla
    de resolucion y se va directo a la lista de archivos."""
    ruta = aria2_client.resolver_ruta_torrent(opcion_elegida["torrent_path"])
    try:
        gid = aria2_client.agregar_torrent_en_pausa(ruta)
    except Exception as e:
        print(f"[R36ARIA] Error al leer/agregar torrent local '{ruta}': {e}")
        mostrar_error_popup("error_leer_torrent", MENU_PRINCIPAL)
        return

    estado["gid"] = gid
    estado["opcion_actual"] = opcion_elegida
    estado["archivos"] = aria2_client.obtener_archivos(gid)
    estado["indice_cursor"] = 0
    estado["indices_elegidos"] = set()
    estado["pantalla"] = LISTA_ARCHIVOS


def _calcular_offset_scroll(indice_cursor, total_items):
    if indice_cursor < theme.ITEMS_VISIBLES:
        return 0
    return min(indice_cursor - theme.ITEMS_VISIBLES + 1, max(0, total_items - theme.ITEMS_VISIBLES))


def dibujar_menu(pantalla):
    pantalla.fill(theme.COLOR_FONDO)
    theme.dibujar_header(pantalla, "R36ARIA")

    opciones = estado["opciones_menu"]
    offset = _calcular_offset_scroll(estado["indice_menu"], len(opciones))
    visibles = opciones[offset:offset + theme.ITEMS_VISIBLES]

    for i, opcion in enumerate(visibles):
        idx_real = offset + i
        y = theme.Y_INICIO_LISTA + i * theme.ALTURA_ITEM

        if idx_real == estado["indice_menu"]:
            pygame.draw.rect(pantalla, theme.COLOR_CURSOR,
                              (10, y, theme.ANCHO - 20, theme.ALTURA_ITEM - 4), border_radius=6)

        if opcion.get("tipo") == "salir":
            pygame.draw.line(pantalla, (100, 100, 100), (20, y - 4), (theme.ANCHO - 20, y - 4))
            color = theme.COLOR_SALIR
        else:
            color = theme.COLOR_TEXTO

        if idx_real == estado["indice_menu"]:
            color = theme.COLOR_ACENTO

        nombre_mostrado = t("salir") if opcion.get("tipo") == "salir" else opcion["nombre"]
        texto = theme.fuente_item.render(nombre_mostrado, True, color)
        pantalla.blit(texto, (26, y + 6))

    theme.dibujar_footer(pantalla, t("menu_footer"))
