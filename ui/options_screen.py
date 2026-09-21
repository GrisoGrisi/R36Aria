import pygame
from ui import theme
from core.state_manager import estado, MENU_PRINCIPAL
from core.input_handler import BOTON_B


def manejar_input_opciones(event):
    if event.type == pygame.JOYBUTTONDOWN and event.button == BOTON_B:
        estado["pantalla"] = MENU_PRINCIPAL


def dibujar_opciones(pantalla):
    pantalla.fill(theme.COLOR_FONDO)
    theme.dibujar_header(pantalla, "Opciones")

    texto = theme.fuente_item.render("(todavia no hay nada aca)", True, theme.COLOR_TEXTO_APAGADO)
    pantalla.blit(texto, texto.get_rect(center=(theme.ANCHO // 2, theme.ALTO // 2)))

    theme.dibujar_footer(pantalla, "B: Volver al menu")
