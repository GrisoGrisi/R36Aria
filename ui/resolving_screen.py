import pygame
from ui import theme
from core.state_manager import estado, LISTA_ARCHIVOS, MENU_PRINCIPAL, TIMEOUT_METADATA
from core import aria2_client
from ui.popups import mostrar_error_popup


def actualizar_resolviendo_metadata():
    """Se llama una vez por frame mientras estado['pantalla'] == RESOLVIENDO_METADATA.
    No bloquea el loop: cada llamada RPC es rapida (localhost)."""
    ahora = pygame.time.get_ticks() / 1000.0
    transcurrido = ahora - estado["inicio_resolucion"]

    try:
        listo, gid_real, error = aria2_client.chequear_metadata(estado["gid"])
    except Exception:
        mostrar_error_popup("Error al cargar magnet, intentelo de nuevo", MENU_PRINCIPAL)
        return

    if error:
        mostrar_error_popup("Error al cargar magnet, intentelo de nuevo", MENU_PRINCIPAL)
        return

    if listo:
        estado["gid"] = gid_real
        estado["archivos"] = aria2_client.obtener_archivos(gid_real)
        estado["indice_cursor"] = 0
        estado["indice_elegido"] = None
        estado["pantalla"] = LISTA_ARCHIVOS
        return

    if transcurrido > TIMEOUT_METADATA:
        mostrar_error_popup("Error al cargar magnet, intentelo de nuevo", MENU_PRINCIPAL)


def dibujar_resolviendo_metadata(pantalla):
    pantalla.fill(theme.COLOR_FONDO)
    nombre = estado["opcion_actual"]["nombre"] if estado["opcion_actual"] else ""
    theme.dibujar_header(pantalla, nombre)

    texto = theme.fuente_item.render("Resolviendo informacion del magnet...", True, theme.COLOR_TEXTO)
    pantalla.blit(texto, texto.get_rect(center=(theme.ANCHO // 2, theme.ALTO // 2)))

    theme.dibujar_footer(pantalla, "Espera un momento")
