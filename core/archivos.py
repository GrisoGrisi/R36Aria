"""
Deteccion y extraccion de archivos comprimidos, usando unicamente la
libreria estandar de Python (zipfile, tarfile) -- sin dependencias nuevas.

La extraccion es incremental (metodo paso()): cada llamada procesa un
bloque acotado de bytes y devuelve si termino o no, para poder mostrar
una barra de progreso real sin congelar la interfaz mientras se extrae.
El contenido se extrae directo dentro de carpeta_destino, sin crear una
subcarpeta extra con el nombre del archivo.

Formatos soportados: .zip, .tar, .tar.gz/.tgz, .tar.bz2/.tbz2, .tar.xz/.txz
No soportados (necesitarian herramientas externas no garantizadas en la
consola): .rar, .7z
"""

import os
import tarfile
import zipfile

_EXTENSIONES_TAR_COMPUESTAS = (".tar.gz", ".tar.bz2", ".tar.xz")
_EXTENSIONES_TAR_SIMPLES = (".tar", ".tgz", ".tbz2", ".txz")

BYTES_POR_PASO = 1024 * 1024  # 1 MB por paso, se llama una vez por frame


def es_comprimido_soportado(ruta):
    nombre = ruta.lower()
    if nombre.endswith(".zip"):
        return True
    if nombre.endswith(_EXTENSIONES_TAR_COMPUESTAS):
        return True
    if nombre.endswith(_EXTENSIONES_TAR_SIMPLES):
        return True
    return False


def _ruta_segura(carpeta_base, nombre_relativo):
    """Evita que una entrada maliciosa del comprimido (ej. '../../etc/x')
    escriba fuera de carpeta_base."""
    base_norm = os.path.normpath(carpeta_base)
    destino = os.path.normpath(os.path.join(base_norm, nombre_relativo))
    if destino != base_norm and not destino.startswith(base_norm + os.sep):
        raise ValueError(f"Ruta insegura dentro del comprimido: {nombre_relativo}")
    return destino


class ExtractorIncremental:
    """Extrae un .zip o .tar.* de a poco, para poder mostrar una barra de
    progreso real. Uso:

        ex = ExtractorIncremental(ruta_archivo, carpeta_destino)
        while not ex.paso():
            ... actualizar barra con ex.bytes_hechos / ex.bytes_totales ...
        ex.cerrar()
    """

    def __init__(self, ruta_archivo, carpeta_destino):
        self.ruta_archivo = ruta_archivo
        self.carpeta_destino = carpeta_destino
        self.bytes_totales = 0
        self.bytes_hechos = 0

        self._zip = None
        self._tar = None
        self._miembros = []
        self._indice_miembro = 0
        self._entrada_actual = None
        self._salida_actual = None

        os.makedirs(carpeta_destino, exist_ok=True)
        nombre_min = ruta_archivo.lower()

        if nombre_min.endswith(".zip"):
            self._zip = zipfile.ZipFile(ruta_archivo, "r")
            self._miembros = [m for m in self._zip.infolist() if not m.is_dir()]
            self.bytes_totales = sum(m.file_size for m in self._miembros)
        else:
            self._tar = tarfile.open(ruta_archivo, "r:*")
            self._miembros = [m for m in self._tar.getmembers() if m.isfile()]
            self.bytes_totales = sum(m.size for m in self._miembros)

    def _iniciar_siguiente_miembro(self):
        while self._indice_miembro < len(self._miembros):
            miembro = self._miembros[self._indice_miembro]
            self._indice_miembro += 1

            if self._zip is not None:
                nombre_relativo = miembro.filename
                destino = _ruta_segura(self.carpeta_destino, nombre_relativo)
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                self._entrada_actual = self._zip.open(miembro)
                self._salida_actual = open(destino, "wb")
                return True
            else:
                nombre_relativo = miembro.name
                destino = _ruta_segura(self.carpeta_destino, nombre_relativo)
                extraido = self._tar.extractfile(miembro)
                if extraido is None:
                    continue  # no es un archivo regular legible (enlace, etc.)
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                self._entrada_actual = extraido
                self._salida_actual = open(destino, "wb")
                return True

        return False

    def paso(self):
        """Procesa hasta BYTES_POR_PASO bytes. Devuelve True cuando termino
        toda la extraccion."""
        if self._entrada_actual is None:
            if not self._iniciar_siguiente_miembro():
                self.cerrar()
                return True

        bloque = self._entrada_actual.read(BYTES_POR_PASO)
        if bloque:
            self._salida_actual.write(bloque)
            self.bytes_hechos += len(bloque)
            return False

        # Se termino este miembro
        self._salida_actual.close()
        self._entrada_actual.close()
        self._entrada_actual = None
        self._salida_actual = None
        return False

    def cerrar(self):
        if self._salida_actual is not None:
            self._salida_actual.close()
            self._salida_actual = None
        if self._entrada_actual is not None:
            self._entrada_actual.close()
            self._entrada_actual = None
        if self._zip is not None:
            self._zip.close()
            self._zip = None
        if self._tar is not None:
            self._tar.close()
            self._tar = None
