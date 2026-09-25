"""
Estado global de la aplicacion y nombres de pantalla.
Se mantiene como un dict mutable simple, accedido por todos los modulos de ui/.
"""

import time

# --- Nombres de pantalla / estados de la maquina de estados ---
MENU_PRINCIPAL = "MENU_PRINCIPAL"
RESOLVIENDO_METADATA = "RESOLVIENDO_METADATA"
LISTA_ARCHIVOS = "LISTA_ARCHIVOS"
DESCARGANDO = "DESCARGANDO"
ELEGIR_ACCION_ARCHIVO = "ELEGIR_ACCION_ARCHIVO"
EXTRAYENDO = "EXTRAYENDO"
DESCARGA_COMPLETA = "DESCARGA_COMPLETA"
CONFIRMAR_CANCELAR = "CONFIRMAR_CANCELAR"
NUEVOS_TORRENTS_LISTA = "NUEVOS_TORRENTS_LISTA"
ENTRADA_TEXTO = "ENTRADA_TEXTO"
OPCIONES = "OPCIONES"
SELECCIONAR_CATEGORIA = "SELECCIONAR_CATEGORIA"
ERROR_POPUP = "ERROR_POPUP"

# --- Timeouts configurables ---
TIMEOUT_METADATA = 90          # segundos totales esperando resolver el magnet
                                # (los magnets sin buenos trackers/DHT pueden
                                # tardar bastante; los .torrent locales no
                                # usan este timeout, ya tienen la metadata)
TIMEOUT_INACTIVIDAD_DESCARGA = 20   # segundos sin progreso en la descarga

FILAS_TECLADO = [
    list("1234567890"),
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
    list("/-_."),  # simbolos utiles para escribir rutas de carpetas
    [" "],  # barra espaciadora: fila de un solo "boton" que ocupa todo el ancho
]


def estado_inicial():
    return {
        "pantalla": MENU_PRINCIPAL,
        "pantalla_anterior": MENU_PRINCIPAL,
        "idioma": "es",  # se sobreescribe al arrancar con core.settings.cargar_idioma()

        # Menu principal
        "opciones_categorias": [],  # las categorias "reales" (sin las entradas especiales de Agregar/Salir), es lo que se persiste
        "opciones_menu": [],
        "indice_menu": 0,

        # Agregar torrents nuevos
        "torrents_nuevos_encontrados": [],
        "torrents_nuevos_indice_cursor": 0,
        "torrent_actual_nuevo": "",
        "nuevo_torrent_nombre": "",
        "modo_entrada_texto": "nombre",  # "nombre"/"destino" (agregar) o "editar_nombre"/"editar_carpeta" (editar)
        "valor_entrada_texto": "",

        # Pantalla de Opciones y edicion de categorias existentes
        "opciones_menu_cursor": 0,
        "editar_categoria_modo": "nombre",  # "nombre" o "carpeta": que campo se va a editar
        "editar_categoria_indice_cursor": 0,
        "editar_categoria_indice_actual": None,  # indice dentro de opciones_categorias que se esta editando

        # Resolucion de metadata / archivos del torrent
        "opcion_actual": None,
        "gid": None,
        "inicio_resolucion": 0.0,
        "archivos": [],

        # Lista de archivos (seleccion multiple)
        "indice_cursor": 0,
        "indices_elegidos": set(),   # guarda los "index" reales de aria2 (no posiciones en la lista) marcados para descargar

        # Busqueda / teclado
        "buscando": False,
        "texto_busqueda": "",
        "fila_teclado": 0,
        "col_teclado": 0,
        "mayusculas": True,  # alternable con L en el teclado virtual

        # Descarga
        "progreso": 0.0,
        "ultimo_completado": 0,
        "ultimo_avance_ts": 0.0,
        "rutas_descargadas": [],   # rutas finales (ya movidas) de todos los archivos descargados en esta tanda
        "accion_archivo_indice": 0,  # 0=mantener, 1=extraer y borrar, 2=extraer y mantener

        # Extraccion (puede haber varios comprimidos en la cola, se procesan de a uno)
        "extractor": None,  # instancia de ExtractorIncremental mientras se extrae
        "progreso_extraccion": 0.0,
        "borrar_comprimido_al_terminar": False,
        "cola_extraccion": [],        # rutas pendientes de extraer (subconjunto de rutas_descargadas)
        "indice_extraccion_actual": 0,
        "total_extraccion": 0,

        # Confirmar cancelar
        "confirmar_indice": 1,  # 0 = Si, 1 = No (arranca en No por seguridad)

        # Error popup
        "mensaje_error": "",
    }


estado = estado_inicial()


def resetear_para_menu():
    """Vuelve al menu principal limpiando todo lo relativo a una opcion elegida."""
    estado["pantalla"] = MENU_PRINCIPAL
    estado["opcion_actual"] = None
    estado["gid"] = None
    estado["archivos"] = []
    estado["indice_cursor"] = 0
    estado["indices_elegidos"] = set()
    estado["buscando"] = False
    estado["texto_busqueda"] = ""
    estado["progreso"] = 0.0
    estado["rutas_descargadas"] = []
    estado["accion_archivo_indice"] = 0
    if estado.get("extractor") is not None:
        try:
            estado["extractor"].cerrar()
        except Exception:
            pass
    estado["extractor"] = None
    estado["progreso_extraccion"] = 0.0
    estado["borrar_comprimido_al_terminar"] = False
    estado["cola_extraccion"] = []
    estado["indice_extraccion_actual"] = 0
    estado["total_extraccion"] = 0
