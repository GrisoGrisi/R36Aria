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

# Carpeta raiz del proyecto (donde vive main.py), independientemente de
# desde donde se invoque el script.
RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Carpeta temporal de descargas: vive dentro del proyecto (en la SD) y no
# en /tmp, que en muchas consolas es RAM (tmpfs) y se llena con archivos grandes.
DIR_TEMPORAL = os.path.join(RAIZ_PROYECTO, "tempdownloads")
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

    os.makedirs(DIR_TEMPORAL, exist_ok=True)

    _proc = subprocess.Popen([
        ruta_aria2c,
        "--enable-rpc",
        "--rpc-listen-all=false",
        "--rpc-listen-port=6800",
        # Por defecto aria2 descarta pedidos RPC de mas de 2M, y un .torrent
        # viaja en base64 (~33% mas grande) dentro del pedido: los torrents
        # grandes (muchos archivos/piezas) eran rechazados.
        "--rpc-max-request-size=64M",
        f"--dir={DIR_TEMPORAL}",
        "--seed-time=0",
        "--follow-torrent=mem",
        "--bt-stop-timeout=0",
        # Sin preasignar el archivo completo: en tarjetas SD FAT/exFAT la
        # preasignacion de un archivo grande tarda minutos con 0% visible.
        "--file-allocation=none",
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


def rpc_call(method, params=None, timeout=5):
    """timeout (segundos) es chico por defecto porque la mayoria de las
    llamadas se hacen en cada frame; las pesadas (agregar un .torrent
    grande, listar miles de archivos) piden uno mas largo."""
    payload = {
        "jsonrpc": "2.0",
        "id": "r36aria",
        "method": method,
        "params": params or [],
    }
    r = requests.post(RPC_URL, json=payload, timeout=timeout)
    if not r.ok:
        # aria2 explica el motivo real en el cuerpo JSON; raise_for_status()
        # lo escondia detras de un "400 Client Error" generico.
        try:
            motivo = r.json().get("error", {}).get("message")
        except ValueError:
            motivo = None
        raise RuntimeError(
            f"aria2 rechazo '{method}' (HTTP {r.status_code}): {motivo or r.text[:200]}"
        )
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
    resp = rpc_call("aria2.addTorrent", [contenido_b64, [], {"pause": "true"}], timeout=60)
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
    # No se llama en cada frame (solo al entrar a la lista y al terminar),
    # asi que puede tener un timeout largo: en torrents con miles de
    # archivos la respuesta es muy grande.
    resp = rpc_call("aria2.getFiles", [gid], timeout=60)
    return resp["result"]


def iniciar_descarga_archivos(gid, indices_elegidos):
    """Selecciona uno o varios archivos dentro del torrent (aria2 acepta
    una lista de indices separados por coma en select-file) y arranca la
    descarga. Siempre se descarga a la carpeta temporal del proceso --
    cambiar 'dir' a mitad de una descarga BitTorrent ya agregada no
    siempre se respeta de forma confiable en aria2. Una vez terminada, se
    mueve a la carpeta_destino real con mover_a_destino_final()."""
    indices_str = ",".join(str(i) for i in sorted(indices_elegidos))
    rpc_call("aria2.changeOption", [gid, {"select-file": indices_str}])
    rpc_call("aria2.unpause", [gid])


def limpiar_carpetas_vacias(carpeta):
    """Borra 'carpeta' y sus padres mientras esten vacios, sin salirse nunca
    de DIR_TEMPORAL (la propia DIR_TEMPORAL tampoco se borra)."""
    base = os.path.realpath(DIR_TEMPORAL)
    actual = os.path.realpath(carpeta)
    while actual.startswith(base + os.sep):
        try:
            os.rmdir(actual)  # falla si no esta vacia
        except OSError:
            break
        actual = os.path.dirname(actual)


def mover_a_destino_final(ruta_origen, carpeta_destino):
    """Mueve el archivo ya descargado a carpeta_destino, tomando solo ese
    archivo (sin arrastrar ninguna subcarpeta que haya creado el torrent),
    y sin pisar un archivo existente con el mismo nombre. Verifica que el
    archivo haya llegado completo antes de dar el movimiento por bueno."""
    if not os.path.isfile(ruta_origen):
        raise FileNotFoundError(f"No existe el archivo descargado: {ruta_origen}")

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

    tamano_origen = os.path.getsize(ruta_origen)
    shutil.move(ruta_origen, destino)

    if not os.path.isfile(destino) or os.path.getsize(destino) != tamano_origen:
        raise OSError(f"El archivo no llego completo a {destino}")

    # Limpieza: carpetas que creo el torrent dentro de la temporal y quedaron vacias.
    limpiar_carpetas_vacias(os.path.dirname(ruta_origen))

    return destino


def consultar_progreso(gid):
    """Devuelve (progreso 0-1, status, error, velocidad_bytes_s, completado, total)."""
    status = rpc_call("aria2.tellStatus", [gid, [
        "completedLength", "totalLength", "status", "errorCode", "errorMessage",
        "downloadSpeed", "connections",
    ]])
    r = status["result"]

    if r.get("errorCode") and r["errorCode"] != "0":
        motivo = r.get("errorMessage", "Error desconocido")
        print(f"[R36ARIA] aria2 reporto error (codigo {r['errorCode']}): {motivo}")
        return 0.0, "error", motivo, 0, 0, 0

    completado = int(r["completedLength"])
    total = int(r["totalLength"])
    progreso = completado / total if total else 0.0
    velocidad = int(r.get("downloadSpeed", 0))
    return progreso, r["status"], None, velocidad, completado, total


def cancelar_gid(gid):
    """Elimina la descarga/metadata en curso sin importar su estado actual.
    OJO: forceRemove es asincronico, aria2 la detiene recien en su
    siguiente vuelta interna. Si hay que tocar archivos despues, usar
    liberar_gid(), que espera a que realmente se haya detenido."""
    try:
        rpc_call("aria2.forceRemove", [gid])
    except Exception:
        pass


def liberar_gid(gid, espera_max=5.0):
    """Detiene el gid, espera a que aria2 lo haya soltado de verdad (cierra
    archivos y guarda/borra su archivo de control .aria2) y lo saca de la
    lista de resultados. Seguro de llamar aunque ya este completo."""
    cancelar_gid(gid)
    limite = time.time() + espera_max
    while time.time() < limite:
        try:
            estado_gid = rpc_call("aria2.tellStatus", [gid, ["status"]])["result"]["status"]
        except Exception:
            break  # ya no existe para aria2
        if estado_gid in ("removed", "complete", "error"):
            break
        time.sleep(0.05)
    try:
        rpc_call("aria2.removeDownloadResult", [gid])
    except Exception:
        pass


_cache_espacio = {"ts": 0.0, "valor": None}


def espacio_libre_bytes(max_edad=2.0):
    """Espacio libre (bytes) de la tarjeta donde vive el proyecto (y por lo
    tanto tempdownloads/). Se cachea unos segundos para poder llamarla en
    cada frame sin consultar el sistema de archivos a 30 FPS. Devuelve
    None si no se pudo consultar."""
    ahora = time.monotonic()
    if ahora - _cache_espacio["ts"] >= max_edad:
        try:
            valor = shutil.disk_usage(RAIZ_PROYECTO).free
        except OSError:
            valor = None
        _cache_espacio["ts"] = ahora
        _cache_espacio["valor"] = valor
    return _cache_espacio["valor"]


def temporal_tiene_contenido():
    return os.path.isdir(DIR_TEMPORAL) and bool(os.listdir(DIR_TEMPORAL))


def tamano_carpeta_temporal():
    """Suma el tamano de todos los archivos dentro de DIR_TEMPORAL."""
    total = 0
    for carpeta, _, nombres in os.walk(DIR_TEMPORAL):
        for nombre in nombres:
            try:
                total += os.path.getsize(os.path.join(carpeta, nombre))
            except OSError:
                pass
    return total


def vaciar_carpeta_temporal():
    """Borra TODO el contenido de DIR_TEMPORAL (archivos parciales, archivos
    de control .aria2 y carpetas del torrent). Es seguro porque esa carpeta
    es solo de trabajo de R36ARIA y se descarga un torrent a la vez. Solo
    usar cuando aria2 ya solto el gid (ver liberar_gid)."""
    if not os.path.isdir(DIR_TEMPORAL):
        return
    for nombre in os.listdir(DIR_TEMPORAL):
        ruta = os.path.join(DIR_TEMPORAL, nombre)
        try:
            if os.path.isdir(ruta) and not os.path.islink(ruta):
                shutil.rmtree(ruta, ignore_errors=True)
            else:
                os.remove(ruta)
        except OSError as e:
            print(f"[R36ARIA] No se pudo borrar '{ruta}': {e}")
    _cache_espacio["ts"] = 0.0  # fuerza releer el espacio libre ya liberado


def cancelar_y_borrar_descarga(gid):
    """Cancelacion completa: detiene la descarga, espera a aria2, y borra
    todo lo que haya dejado en la carpeta temporal (archivos, parciales,
    archivos .aria2 y carpetas)."""
    rutas = rutas_seleccionadas(gid)
    liberar_gid(gid)
    for ruta in rutas:
        for candidato in (ruta, ruta + ".aria2"):
            try:
                if os.path.exists(candidato):
                    os.remove(candidato)
            except OSError:
                pass
    # El archivo de control de un torrent multi-archivo NO queda junto al
    # archivo sino en la raiz de DIR_TEMPORAL (<nombre del torrent>.aria2),
    # asi que el borrado puntual de arriba no alcanza: se limpia todo.
    vaciar_carpeta_temporal()


def rutas_seleccionadas(gid):
    """Devuelve las rutas de archivo marcadas como 'selected' para ese gid (para poder borrarlas si se cancela)."""
    try:
        archivos = obtener_archivos(gid)
        return [f["path"] for f in archivos if f.get("selected") == "true"]
    except Exception:
        return []
