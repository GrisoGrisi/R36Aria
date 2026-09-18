import pygame
from ui import theme
from core.state_manager import estado, ERROR_POPUP, CONFIRMAR_CANCELAR
from core.input_handler import BOTON_A, BOTON_B, obtener_direccion_input
from core import aria2_client


# ---------- Popup de error (reutilizado por metadata y descarga) ----------

def mostrar_error_popup(mensaje, pantalla_retorno):
    if estado.get("gid"):
        aria2_client.cancelar_gid(estado["gid"])

    estado["pantalla_anterior"] = pantalla_retorno
    estado["mensaje_error"] = mensaje
    estado["pantalla"] = ERROR_POPUP
    estado["gid"] = None


def manejar_input_error_popup(event):
    if event.type == pygame.JOYBUTTONDOWN:
        if event.button in (BOTON_A, BOTON_B):
            estado["pantalla"] = estado["pantalla_anterior"]
            estado["mensaje_error"] = ""


def dibujar_error_popup(pantalla):
    overlay = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    pantalla.blit(overlay, (0, 0))

    caja = pygame.Rect(40, 100, theme.ANCHO - 80, 100)
    pygame.draw.rect(pantalla, (30, 30, 30), caja, border_radius=10)
    pygame.draw.rect(pantalla, theme.COLOR_ERROR, caja, width=2, border_radius=10)

    texto = theme.fuente_item.render(estado["mensaje_error"], True, (255, 255, 255))
    pantalla.blit(texto, texto.get_rect(center=caja.center))

    ayuda = theme.fuente_footer.render("Presiona A o B para cerrar", True, theme.COLOR_TEXTO_APAGADO)
    pantalla.blit(ayuda, ayuda.get_rect(centerx=caja.centerx, top=caja.bottom + 10))


# ---------- Popup de confirmar cancelacion de descarga ----------

def manejar_input_confirmar_cancelar(event, on_confirmar_si):
    direccion = obtener_direccion_input(event)
    if direccion:
        x, _ = direccion
        if x != 0:
            estado["confirmar_indice"] = 1 - estado["confirmar_indice"]
        return

    if event.type == pygame.JOYBUTTONDOWN:
        if event.button == BOTON_A:
            if estado["confirmar_indice"] == 0:
                on_confirmar_si()
            else:
                estado["pantalla"] = estado["pantalla_previa"]
        elif event.button == BOTON_B:
            estado["pantalla"] = estado["pantalla_previa"]


def dibujar_confirmar_cancelar(pantalla):
    overlay = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    pantalla.blit(overlay, (0, 0))

    caja = pygame.Rect(40, 90, theme.ANCHO - 80, 120)
    pygame.draw.rect(pantalla, (30, 30, 30), caja, border_radius=10)
    pygame.draw.rect(pantalla, theme.COLOR_ADVERTENCIA, caja, width=2, border_radius=10)

    texto = theme.fuente_item.render("¿Cancelar la descarga?", True, (255, 255, 255))
    pantalla.blit(texto, texto.get_rect(centerx=caja.centerx, top=caja.top + 15))

    opciones = ["Si", "No"]
    for i, op in enumerate(opciones):
        color = theme.COLOR_ACENTO if i == estado["confirmar_indice"] else theme.COLOR_TEXTO
        x = caja.centerx - 60 + i * 120
        texto_op = theme.fuente_item.render(op, True, color)
        pantalla.blit(texto_op, texto_op.get_rect(center=(x, caja.bottom - 30)))
