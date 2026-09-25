"""
Traducciones de toda la interfaz de R36ARIA. Cada pantalla llama a
t("clave") en vez de escribir el texto literal, para poder mostrar la UI
en español o ingles segun estado["idioma"].

Para agregar un idioma nuevo: agregar un diccionario mas a TEXTOS con las
mismas claves que "es"/"en", y agregarlo como opcion en options_screen.py.
"""

from core.state_manager import estado

TEXTOS = {
    "es": {
        # Menu principal
        "salir": "Salir",
        "menu_footer": "A: Elegir  START: Agregar torrent  SELECT: Opciones  Dpad: Navegar",

        # Resolviendo metadata
        "resolviendo_metadata": "Resolviendo informacion del magnet...",
        "espera_momento": "Espera un momento",
        "espera_momento_puntos": "Espera un momento...",

        # Lista de archivos
        "sin_resultados": "Sin resultados",
        "lista_footer": "A: Marcar{sufijo}  X: Descargar  SELECT: Buscar  B: Volver",

        # Teclado / busqueda
        "espacio": "ESPACIO",
        "buscar_placeholder": "Buscar...",
        "teclado_footer_busqueda": "A: Escribir  L: Mayus/Minus  Y: Borrar  X: Espacio  START: Cerrar  B: Cancelar",
        "teclado_footer_entrada": "A: Escribir  L: Mayus/Minus  Y: Borrar  X: Espacio  START: Confirmar  B: Cancelar",

        # Popups
        "cerrar_popup": "Presiona A o B para cerrar",
        "confirmar_cancelar_descarga": "¿Cancelar la descarga?",
        "si": "Si",
        "no": "No",

        # Mensajes de error (usados como clave en mostrar_error_popup)
        "error_cargar_magnet": "Error al cargar magnet, intentelo de nuevo",
        "error_descargar": "Error al descargar, intentelo de nuevo",
        "error_extraer": "Error al extraer el archivo",
        "error_leer_torrent": "No se pudo leer el archivo .torrent",
        "error_no_torrents_nuevos": "No se encontraron torrents nuevos en torrents/",

        # Pantalla de descarga
        "cancelar_descarga_footer": "B: Cancelar descarga",
        "archivo": "archivo",
        "archivos": "archivos",
        "descarga_completa": "Descarga completa",
        "descarga_completa_cantidad": "Descarga completa ({cantidad} archivos)",
        "guardado_en": "Guardado en: {carpeta}",
        "y_n_mas": "... y {n} mas",
        "volver_menu_ayb": "A o B: Volver al menu",

        # Eleccion de accion sobre archivo comprimido
        "mantener_archivo": "Mantener el archivo como esta",
        "extraer_borrar": "Extraer y borrar el comprimido",
        "extraer_mantener": "Extraer y mantener el comprimido",
        "archivo_comprimido_titulo": "Archivo comprimido",
        "detecto_comprimido_pregunta": "Se detecto un archivo comprimido, que queres hacer?",
        "elegir_dpad_footer": "A: Elegir   Dpad: Navegar",
        "extrayendo": "Extrayendo...",
        "extrayendo_cantidad": "Extrayendo... ({actual}/{total})",

        # Agregar torrents nuevos
        "torrents_nuevos_titulo": "Torrents nuevos",
        "sin_torrents_nuevos": "Sin torrents nuevos",
        "agregar_footer": "A: Configurar   B: Volver al menu",
        "nombre_para_torrent": "Nombre para el torrent",
        "carpeta_destino_completa": "Carpeta destino (ruta completa)",
        "nuevo_nombre_torrent": "Nuevo nombre para el torrent",
        "nueva_carpeta_destino": "Nueva carpeta destino (ruta completa)",

        # Opciones
        "opciones_titulo": "Opciones",
        "renombrar_torrent": "Renombrar un torrent",
        "cambiar_carpeta_descarga": "Cambiar carpeta de descarga",
        "idioma_entrada": "Idioma: Español",
        "opciones_footer": "A: Elegir  B: Volver al menu",
        "seleccionar_categoria_footer": "A: Elegir  B: Volver",
        "renombrar_elegir_torrent": "Renombrar: elegi un torrent",
        "cambiar_carpeta_elegir_torrent": "Cambiar carpeta: elegi un torrent",
        "no_hay_torrents_cargados": "No hay torrents cargados todavia",
    },
    "en": {
        # Main menu
        "salir": "Exit",
        "menu_footer": "A: Select  START: Add torrent  SELECT: Options  Dpad: Navigate",

        # Resolving metadata
        "resolviendo_metadata": "Resolving magnet information...",
        "espera_momento": "Please wait",
        "espera_momento_puntos": "Please wait...",

        # File list
        "sin_resultados": "No results",
        "lista_footer": "A: Select{sufijo}  X: Download  SELECT: Search  B: Back",

        # Keyboard / search
        "espacio": "SPACE",
        "buscar_placeholder": "Search...",
        "teclado_footer_busqueda": "A: Type  L: Upper/Lower  Y: Delete  X: Space  START: Close  B: Cancel",
        "teclado_footer_entrada": "A: Type  L: Upper/Lower  Y: Delete  X: Space  START: Confirm  B: Cancel",

        # Popups
        "cerrar_popup": "Press A or B to close",
        "confirmar_cancelar_descarga": "Cancel the download?",
        "si": "Yes",
        "no": "No",

        # Error messages
        "error_cargar_magnet": "Error loading magnet, please try again",
        "error_descargar": "Download error, please try again",
        "error_extraer": "Error extracting the file",
        "error_leer_torrent": "Could not read the .torrent file",
        "error_no_torrents_nuevos": "No new torrents found in torrents/",

        # Download screen
        "cancelar_descarga_footer": "B: Cancel download",
        "archivo": "file",
        "archivos": "files",
        "descarga_completa": "Download complete",
        "descarga_completa_cantidad": "Download complete ({cantidad} files)",
        "guardado_en": "Saved to: {carpeta}",
        "y_n_mas": "... and {n} more",
        "volver_menu_ayb": "A or B: Back to menu",

        # Compressed file action choice
        "mantener_archivo": "Keep the file as is",
        "extraer_borrar": "Extract and delete the archive",
        "extraer_mantener": "Extract and keep the archive",
        "archivo_comprimido_titulo": "Compressed file",
        "detecto_comprimido_pregunta": "A compressed file was found, what do you want to do?",
        "elegir_dpad_footer": "A: Select   Dpad: Navigate",
        "extrayendo": "Extracting...",
        "extrayendo_cantidad": "Extracting... ({actual}/{total})",

        # Add new torrents
        "torrents_nuevos_titulo": "New torrents",
        "sin_torrents_nuevos": "No new torrents",
        "agregar_footer": "A: Configure   B: Back to menu",
        "nombre_para_torrent": "Name for the torrent",
        "carpeta_destino_completa": "Destination folder (full path)",
        "nuevo_nombre_torrent": "New name for the torrent",
        "nueva_carpeta_destino": "New destination folder (full path)",

        # Options
        "opciones_titulo": "Options",
        "renombrar_torrent": "Rename a torrent",
        "cambiar_carpeta_descarga": "Change download folder",
        "idioma_entrada": "Language: English",
        "opciones_footer": "A: Select  B: Back to menu",
        "seleccionar_categoria_footer": "A: Select  B: Back",
        "renombrar_elegir_torrent": "Rename: choose a torrent",
        "cambiar_carpeta_elegir_torrent": "Change folder: choose a torrent",
        "no_hay_torrents_cargados": "No torrents added yet",
    },
}


def t(clave, **kwargs):
    """Devuelve el texto traducido para la clave dada, en el idioma actual
    (estado["idioma"]). Si faltara la clave o el idioma, cae a español."""
    idioma = estado.get("idioma", "es")
    tabla = TEXTOS.get(idioma, TEXTOS["es"])
    texto = tabla.get(clave, TEXTOS["es"].get(clave, clave))
    if kwargs:
        return texto.format(**kwargs)
    return texto
