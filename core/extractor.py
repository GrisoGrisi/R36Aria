"""
Deteccion y extraccion de archivos comprimidos, usando solo la libreria
estandar de Python (zipfile / tarfile) -- sin dependencias externas, para
no depender de pip/apt en la consola.

Formatos soportados: .zip, .tar, .tar.gz/.tgz, .tar.bz2/.tbz2, .tar.xz/.txz
No se soportan .rar ni .7z (requieren herramientas externas que no vienen
en la libreria estandar de Python).
"""

import os
import tarfile
import zipfile

_SUFIJOS_TAR = (".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz", ".tar")


def es_comprimido(ruta):
    nombre = os.path.basename(ruta).lower()
    if nombre.endswith(_SUFIJOS_TAR):
        return True
    return nombre.endswith(".zip")


def _carpeta_extraccion(ruta_archivo):
    """Nombre de carpeta destino: el archivo sin su extension, en la
    misma carpeta donde esta el comprimido."""
    nombre = os.path.basename(ruta_archivo)
    nombre_lower = nombre.lower()
    for sufijo in _SUFIJOS_TAR:
        if nombre_lower.endswith(sufijo):
            base = nombre[: -len(sufijo)]
            break
    else:
        base, _ = os.path.splitext(nombre)

    carpeta_padre = os.path.dirname(ruta_archivo)
    return os.path.join(carpeta_padre, base)


def extraer(ruta_archivo):
    """Extrae el comprimido a una subcarpeta (con su nombre, sin
    extension) dentro de la misma carpeta donde esta. Devuelve la ruta de
    esa carpeta con el contenido ya extraido."""
    destino = _carpeta_extraccion(ruta_archivo)
    os.makedirs(destino, exist_ok=True)

    nombre_lower = ruta_archivo.lower()
    if nombre_lower.endswith(".zip"):
        with zipfile.ZipFile(ruta_archivo) as z:
            z.extractall(destino)
    else:
        with tarfile.open(ruta_archivo) as t:
            # filter="data" restringe rutas peligrosas (absolutas, fuera
            # de la carpeta destino, symlinks raros, etc.)
            t.extractall(destino, filter="data")

    return destino
