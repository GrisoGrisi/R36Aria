"""
Paleta y layout comun, pensado para pantallas de 640x480.
Un solo color de acento (amarillo) reservado para seleccion / elementos activos.
"""

import pygame

ANCHO, ALTO = 640, 480

ALTO_HEADER = 50
ALTO_FOOTER = 36
Y_INICIO_LISTA = ALTO_HEADER + 10
Y_FIN_LISTA = ALTO - ALTO_FOOTER - 10
ALTURA_ITEM = 34
ITEMS_VISIBLES = (Y_FIN_LISTA - Y_INICIO_LISTA) // ALTURA_ITEM

COLOR_FONDO = (15, 15, 20)
COLOR_HEADER = (35, 35, 45)
COLOR_FOOTER = (35, 35, 45)
COLOR_TEXTO = (230, 230, 230)
COLOR_TEXTO_APAGADO = (150, 150, 150)
COLOR_ACENTO = (255, 220, 80)
COLOR_CURSOR = (60, 60, 90)
COLOR_OK = (100, 220, 100)
COLOR_ERROR = (200, 50, 50)
COLOR_ADVERTENCIA = (200, 160, 50)
COLOR_SALIR = (200, 80, 80)

fuente_titulo = None
fuente_item = None
fuente_footer = None


def inicializar_fuentes():
    global fuente_titulo, fuente_item, fuente_footer
    fuente_titulo = pygame.font.Font(None, 30)
    fuente_item = pygame.font.Font(None, 24)
    fuente_footer = pygame.font.Font(None, 18)


def _truncar_texto(texto, fuente, ancho_max):
    if fuente.size(texto)[0] <= ancho_max:
        return texto
    while texto and fuente.size(texto + "...")[0] > ancho_max:
        texto = texto[:-1]
    return texto + "..." if texto else "..."


def dibujar_header(pantalla, titulo_texto, texto_derecha=None, color_derecha=None):
    """Header con el titulo a la izquierda y, opcionalmente, un texto
    alineado a la derecha (espacio libre, espacio a ocupar, etc.). Si no
    entran los dos, se recorta el titulo para que nunca se pisen."""
    pygame.draw.rect(pantalla, COLOR_HEADER, (0, 0, ANCHO, ALTO_HEADER))

    ancho_max_titulo = ANCHO - 32
    if texto_derecha:
        render_der = fuente_item.render(texto_derecha, True, color_derecha or COLOR_TEXTO)
        x_der = ANCHO - 16 - render_der.get_width()
        y_der = (ALTO_HEADER - render_der.get_height()) // 2
        pantalla.blit(render_der, (x_der, y_der))
        ancho_max_titulo = x_der - 16 - 12

    titulo_texto = _truncar_texto(titulo_texto, fuente_titulo, ancho_max_titulo)
    texto = fuente_titulo.render(titulo_texto, True, (255, 255, 255))
    pantalla.blit(texto, (16, 12))


def dibujar_footer(pantalla, texto_ayuda):
    pygame.draw.rect(pantalla, COLOR_FOOTER, (0, ALTO - ALTO_FOOTER, ANCHO, ALTO_FOOTER))
    texto = fuente_footer.render(texto_ayuda, True, (180, 180, 180))
    pantalla.blit(texto, (16, ALTO - ALTO_FOOTER + 9))
