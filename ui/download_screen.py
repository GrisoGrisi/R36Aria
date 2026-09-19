import os
import pygame
from ui import theme
from core.state_manager import (
    estado, MENU_PRINCIPAL, CONFIRMAR_CANCELAR, DESCARGANDO, DESCARGA_COMPLETA,
    ELEGIR_ACCION_ARCHIVO, TIMEOUT_INACTIVIDAD_DESCARGA, resetear_para_menu
)
from core.input_handler import BOTON_A, BOTON_B
from core import aria2_client, archivos
from ui.popups import mostrar_error_popup, manejar_input_confirmar_cancelar, dibujar_confirmar_cancelar


def manejar_input_descargando(event):
    if event.type == pygame.JOYBUTTONDOWN and event.button == BOTON_B:
        estado["pantalla_previa"] = DESCARGANDO
        estado["confirmar_indice"] = 1  # arranca en "No"
        estado["pantalla"] = CONFIRMAR_CANCELAR


def manejar_input_confirmar_cancelar_descarga(event):
    manejar_input_confirmar_cancelar(event, on_confirmar_si=_cancelar_descarga_actual)


def manejar_input_descarga_completa(event):
    if event.type == pygame.JOYBUTTONDOWN and event.button in (BOTON_A, BOTON_B):
        resetear_para_menu()


def _cancelar_descarga_actual():
    gid = estado["gid"]
    rutas = aria2_client.rutas_seleccionadas(gid)
    aria2_client.cancelar_gid(gid)
    _borrar_archivos_incompletos(rutas)
    resetear_para_menu()


def _borrar_archivos_incompletos(rutas):
    for ruta in rutas:
        for candidato in (ruta, ruta + ".aria2"):
            if os.path.exists(candidato):
                try:
                    os.remove(candidato)
                except OSError:
                    pass


def cancelar_y_limpiar_si_hay_descarga_activa():
    """Se llama al salir del programa: si hay una descarga en curso (todavia
    no terminada), se cancela y se borra lo incompleto. Si ya esta en la
    pantalla de Descarga Completa, no se toca nada -- el archivo quedo bien."""
    if estado["pantalla"] == DESCARGANDO and estado.get("gid"):
        _cancelar_descarga_actual()


def actualizar_descargando():
    """Se llama una vez por frame mientras estado['pantalla'] == DESCARGANDO."""
    try:
        progreso, status, error = aria2_client.consultar_progreso(estado["gid"])
    except Exception:
        mostrar_error_popup("Error al descargar, intentelo de nuevo", MENU_PRINCIPAL)
        return

    if error:
        mostrar_error_popup("Error al descargar, intentelo de nuevo", MENU_PRINCIPAL)
        return

    estado["progreso"] = progreso
    ahora = pygame.time.get_ticks() / 1000.0

    if progreso > estado.get("_ultimo_progreso_registrado", 0.0):
        estado["_ultimo_progreso_registrado"] = progreso
        estado["ultimo_avance_ts"] = ahora

    # Ademas de fijarnos en el status que reporta aria2, tratamos progreso
    # 100% como señal de finalizacion por su cuenta: con select-file en
    # torrents multi-archivo, el status puede tardar en pasar a "complete"
    # (o directamente no llegar a hacerlo de forma confiable en algunas
    # versiones/config de aria2) aun cuando el archivo ya esta completo.
    if status == "complete" or progreso >= 1.0:
        _finalizar_descarga()
        if any(archivos.es_comprimido_soportado(r) for r in estado["rutas_descargadas"]):
            estado["accion_archivo_indice"] = 0
            estado["pantalla"] = ELEGIR_ACCION_ARCHIVO
        else:
            estado["pantalla"] = DESCARGA_COMPLETA
        return

    inactivo_desde = ahora - estado["ultimo_avance_ts"]
    if inactivo_desde > TIMEOUT_INACTIVIDAD_DESCARGA:
        mostrar_error_popup("Error al descargar, intentelo de nuevo", MENU_PRINCIPAL)


def _finalizar_descarga():
    """Mueve todos los archivos descargados en esta tanda desde la carpeta
    temporal a la carpeta_destino real configurada para esta opcion, cada
    uno tomando solo ese archivo (sin subcarpetas del torrent), y guarda
    las rutas finales para mostrarlas."""
    rutas_temporales = aria2_client.rutas_seleccionadas(estado["gid"])
    carpeta_destino = estado["opcion_actual"]["carpeta_destino"]

    rutas_finales = []
    for ruta_temporal in rutas_temporales:
        try:
            ruta_final = aria2_client.mover_a_destino_final(ruta_temporal, carpeta_destino)
        except Exception as e:
            print(f"[R36ARIA] Error moviendo '{ruta_temporal}' a destino final: {e}")
            ruta_final = ruta_temporal  # al menos mostramos donde quedo de verdad
        rutas_finales.append(ruta_final)

    estado["rutas_descargadas"] = rutas_finales
    print(f"[R36ARIA] Descarga completa, {len(rutas_finales)} archivo(s): {rutas_finales}")


def dibujar_descargando(pantalla):
    pantalla.fill(theme.COLOR_FONDO)
    nombre = estado["opcion_actual"]["nombre"] if estado["opcion_actual"] else ""
    theme.dibujar_header(pantalla, nombre)

    # Barra de progreso centrada
    ancho_barra = theme.ANCHO - 80
    alto_barra = 30
    x = 40
    y = theme.ALTO // 2 - alto_barra // 2

    pygame.draw.rect(pantalla, (40, 40, 50), (x, y, ancho_barra, alto_barra), border_radius=6)
    ancho_relleno = int(ancho_barra * estado["progreso"])
    pygame.draw.rect(pantalla, theme.COLOR_ACENTO, (x, y, ancho_relleno, alto_barra), border_radius=6)
    pygame.draw.rect(pantalla, (80, 80, 90), (x, y, ancho_barra, alto_barra), width=2, border_radius=6)

    cantidad = len(estado["indices_elegidos"])
    texto_cantidad = f"{cantidad} archivo" + ("" if cantidad == 1 else "s")
    render_cantidad = theme.fuente_footer.render(texto_cantidad, True, theme.COLOR_TEXTO_APAGADO)
    pantalla.blit(render_cantidad, render_cantidad.get_rect(center=(theme.ANCHO // 2, y - 48)))

    porcentaje = theme.fuente_item.render(f"{int(estado['progreso'] * 100)}%", True, (255, 255, 255))
    pantalla.blit(porcentaje, porcentaje.get_rect(center=(theme.ANCHO // 2, y - 24)))

    theme.dibujar_footer(pantalla, "B: Cancelar descarga")

    if estado["pantalla"] == CONFIRMAR_CANCELAR:
        dibujar_confirmar_cancelar(pantalla)


def _envolver_texto(texto, fuente, ancho_max):
    """Parte el texto en lineas que entren en ancho_max, cortando por
    caracter (sirve para rutas de archivo, que no tienen espacios donde
    cortar de forma natural)."""
    lineas = []
    actual = ""
    for char in texto:
        candidato = actual + char
        if fuente.size(candidato)[0] > ancho_max and actual:
            lineas.append(actual)
            actual = char
        else:
            actual = candidato
    if actual:
        lineas.append(actual)
    return lineas


def dibujar_descarga_completa(pantalla):
    pantalla.fill(theme.COLOR_FONDO)
    nombre = estado["opcion_actual"]["nombre"] if estado["opcion_actual"] else ""
    theme.dibujar_header(pantalla, nombre)

    rutas = estado.get("rutas_descargadas", [])
    carpeta_destino = estado["opcion_actual"]["carpeta_destino"] if estado["opcion_actual"] else ""

    fuente_ruta = theme.fuente_footer
    max_ancho_texto = theme.ANCHO - 60

    lineas = [f"Guardado en: {carpeta_destino}"]
    lineas.extend(os.path.basename(r) for r in rutas)

    lineas_envueltas = []
    for linea in lineas:
        lineas_envueltas.extend(_envolver_texto(linea, fuente_ruta, max_ancho_texto))

    alto_linea = 20
    alto_disponible = theme.ALTO - theme.ALTO_HEADER - theme.ALTO_FOOTER - 90
    max_lineas = max(1, alto_disponible // alto_linea)
    if len(lineas_envueltas) > max_lineas:
        lineas_mostradas = lineas_envueltas[: max_lineas - 1]
        lineas_mostradas.append(f"... y {len(lineas_envueltas) - (max_lineas - 1)} mas")
    else:
        lineas_mostradas = lineas_envueltas

    alto_caja = 60 + len(lineas_mostradas) * alto_linea + 15
    top_caja = theme.ALTO // 2 - alto_caja // 2
    top_caja = max(theme.ALTO_HEADER + 10, top_caja)
    alto_caja = min(alto_caja, theme.ALTO - theme.ALTO_FOOTER - 10 - top_caja)
    caja = pygame.Rect(20, top_caja, theme.ANCHO - 40, alto_caja)
    pygame.draw.rect(pantalla, (30, 30, 30), caja, border_radius=10)
    pygame.draw.rect(pantalla, theme.COLOR_OK, caja, width=2, border_radius=10)

    cantidad = len(rutas)
    titulo = f"Descarga completa ({cantidad} archivos)" if cantidad > 1 else "Descarga completa"
    texto = theme.fuente_titulo.render(titulo, True, (255, 255, 255))
    pantalla.blit(texto, texto.get_rect(centerx=caja.centerx, top=caja.top + 15))

    y = caja.top + 55
    for linea in lineas_mostradas:
        texto_linea = fuente_ruta.render(linea, True, theme.COLOR_TEXTO_APAGADO)
        pantalla.blit(texto_linea, texto_linea.get_rect(centerx=caja.centerx, top=y))
        y += alto_linea

    theme.dibujar_footer(pantalla, "A o B: Volver al menu")
