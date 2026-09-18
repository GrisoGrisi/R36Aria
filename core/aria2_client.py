"""
Manejo de aria2 en modo daemon RPC.
Todas las llamadas son sincronas pero rapidas (localhost), pensadas para
ser invocadas desde el loop de pygame sin bloquear mas de unos ms.
"""

import base64
import os
import platform
import shutil
import subprocess
import time
import requests

RPC_URL = "http://localhost:6800/jsonrpc"
DIR_TEMPORAL = "/tmp/r36aria_downloads"

# Carpeta raiz del proyecto (donde vive main.py), independientemente de
# desde donde se invoque el script.
RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_TORRENTS = os.path.join(RAIZ_PROYECTO, "torrents")

_proc = None


def resolver_ruta_aria2c():
    """
    Busca el binario de aria2c en este orden:
    1) Variable de entorno ARIA2_BIN (la usa el script de PortMaster).
    2) bin/aria2c.<arquitectura> dentro del propio proyecto (el que viene incluido).
    3) bin/aria2c generico dentro del proyecto.
    4) 'aria2c' del PATH del sistema, por si ya esta instalado.
    """
    if os.environ.get("ARIA2_BIN") and os.path.isfile(os.environ["ARIA2_BIN"]):
        return os.environ["ARIA2_BIN"]

    arquitectura = platform.machine()  # ej: aarch64, armv7l, x86_64
    candidato_arch = os.path.join(RAIZ_PROYECTO, "bin", f"aria2c.{arquitectura}")
    if os.path.isfile(candidato_arch):
        return candidato_arch

    candidato_generico = os.path.join(RAIZ_PROYECTO, "bin", "aria2c")
    if os.path.isfile(candidato_generico):
        return candidato_generico

    return "aria2c"  # ultimo recurso: confiar en el PATH del sistema


def iniciar_aria2():
    """Lanza aria2c como subproceso con el RPC habilitado. Llamar una sola vez al arrancar."""
    global _proc
    ruta_aria2c = resolver_ruta_aria2c()

    # Nos aseguramos de que el binario incluido tenga permiso de ejecucion
    # (los zips a veces pierden el bit +x al descomprimirse).
    if ruta_aria2c != "aria2c":
        try:
            os.chmod(ruta_aria2c, 0o755)
        except OSError:
            pass

    _proc = subprocess.Popen([
        ruta_aria2c,
        "--enable-rpc",
        "--rpc-listen-all=false",
        "--rpc-listen-port=6800",
        f"--dir={DIR_TEMPORAL}",
        "--seed-time=0",
        "--follow-torrent=mem",
        "--bt-stop-timeout=0",
    ])
    # Pequeña espera para que el RPC este listo antes de la primera llamada
    time.sleep(1.0)
    return _proc


def detener_aria2():
    """Cierre prolijo: intenta shutdown por RPC, si no responde mata el proceso."""
    try:
        rpc_call("aria2.shutdown", [])
    except Exception:
        pass

    global _proc
    if _proc is not None and _proc.poll() is None:
        _proc.terminate()
        try:
            _proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _proc.kill()


def rpc_call(method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "id": "r36aria",
        "method": method,
        "params": params or [],
    }
    r = requests.post(RPC_URL, json=payload, timeout=5)
    r.raise_for_status()
    return r.json()


def agregar_magnet_en_pausa(magnet_url):
    """Agrega el magnet pausado, para poder resolver metadata sin descargar contenido."""
    resp = rpc_call("aria2.addUri", [[magnet_url], {"pause": "true"}])
    return resp["result"]  # gid


def resolver_ruta_torrent(nombre_o_ruta):
    """Si es una ruta absoluta la usa tal cual; si no, la busca dentro de
    la carpeta torrents/ del proyecto."""
    if os.path.isabs(nombre_o_ruta):
        return nombre_o_ruta
    return os.path.join(CARPETA_TORRENTS, nombre_o_ruta)


def agregar_torrent_en_pausa(ruta_torrent):
    """Agrega un archivo .torrent local, que ya trae toda la metadata
    adentro -- a diferencia de un magnet, el gid devuelto ya es el
    definitivo y los archivos se pueden listar de inmediato, sin esperar
    resolucion de metadata."""
    with open(ruta_torrent, "rb") as f:
        contenido_b64 = base64.b64encode(f.read()).decode("ascii")
    resp = rpc_call("aria2.addTorrent", [contenido_b64, [], {"pause": "true"}])
    return resp["result"]  # gid definitivo


def chequear_metadata(gid):
    """
    Devuelve una tupla (listo, gid_real, error).
    listo=True y gid_real seteado cuando la metadata ya se resolvio.
    error contiene un mensaje si aria2 reporto un errorCode != 0.
    """
    status = rpc_call("aria2.tellStatus", [gid, ["followedBy", "status", "errorCode", "errorMessage"]])
    r = status["result"]

    if r.get("errorCode") and r["errorCode"] != "0":
        return False, None, r.get("errorMessage", "Error desconocido")

    followed = r.get("followedBy")
    if followed:
        return True, followed[0], None

    return False, None, None


def obtener_archivos(gid):
    resp = rpc_call("aria2.getFiles", [gid])
    return resp["result"]


def iniciar_descarga_archivo(gid, index_elegido):
    """Selecciona solo el archivo elegido dentro del torrent y arranca la
    descarga. Siempre se descarga a la carpeta temporal del proceso --
    cambiar 'dir' a mitad de una descarga BitTorrent ya agregada no
    siempre se respeta de forma confiable en aria2. Una vez terminada, se
    mueve a la carpeta_destino real con mover_a_destino_final()."""
    rpc_call("aria2.changeOption", [gid, {"select-file": str(index_elegido)}])
    rpc_call("aria2.unpause", [gid])


def mover_a_destino_final(ruta_origen, carpeta_destino):
    """Mueve el archivo ya descargado a carpeta_destino, tomando solo ese
    archivo (sin arrastrar ninguna subcarpeta que haya creado el torrent),
    y sin pisar un archivo existente con el mismo nombre."""
    os.makedirs(carpeta_destino, exist_ok=True)
    nombre = os.path.basename(ruta_origen)
    destino = os.path.join(carpeta_destino, nombre)

    if os.path.abspath(destino) == os.path.abspath(ruta_origen):
        return destino  # ya estaba ahi (no deberia pasar, pero por las dudas)

    base, ext = os.path.splitext(nombre)
    contador = 1
    while os.path.exists(destino):
        destino = os.path.join(carpeta_destino, f"{base} ({contador}){ext}")
        contador += 1

    shutil.move(ruta_origen, destino)

    # Intento de limpieza: si la carpeta que creo el torrent (dentro de la
    # carpeta temporal) quedo vacia, la borramos. No es grave si falla.
    carpeta_origen = os.path.dirname(ruta_origen)
    try:
        while carpeta_origen and carpeta_origen != DIR_TEMPORAL and not os.listdir(carpeta_origen):
            os.rmdir(carpeta_origen)
            carpeta_origen = os.path.dirname(carpeta_origen)
    except OSError:
        pass

    return destino


def consultar_progreso(gid):
    """Devuelve (progreso 0-1, status, error) para el gid dado."""
    status = rpc_call("aria2.tellStatus", [gid, ["completedLength", "totalLength", "status", "errorCode", "errorMessage"]])
    r = status["result"]

    if r.get("errorCode") and r["errorCode"] != "0":
        return 0.0, "error", r.get("errorMessage", "Error desconocido")

    completado = int(r["completedLength"])
    total = int(r["totalLength"])
    progreso = completado / total if total else 0.0
    return progreso, r["status"], None


def cancelar_gid(gid):
    """Elimina la descarga/metadata en curso sin importar su estado actual."""
    try:
        rpc_call("aria2.forceRemove", [gid])
    except Exception:
        pass


def rutas_seleccionadas(gid):
    """Devuelve las rutas de archivo marcadas como 'selected' para ese gid (para poder borrarlas si se cancela)."""
    try:
        archivos = obtener_archivos(gid)
        return [f["path"] for f in archivos if f.get("selected") == "true"]
    except Exception:
        return []
