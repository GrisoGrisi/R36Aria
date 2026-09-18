"""
Presentacion directa sobre el framebuffer clasico de Linux (/dev/fb0),
evitando por completo la GPU (KMSDRM/EGL). Pensado para dispositivos donde
la GPU no inicializa correctamente (ver README para el detalle del bug),
pero el framebuffer de toda la vida sigue funcionando sin problema.

Uso tipico:

    fb = FramebufferDirecto()
    fb.abrir()
    superficie = pygame.Surface((fb.ancho, fb.alto))  # dibujar normal aca
    ...
    fb.presentar(superficie)  # en vez de pygame.display.flip()
    ...
    fb.cerrar()
"""

import ctypes
import fcntl
import os

FBIOGET_VSCREENINFO = 0x4600
FBIOGET_FSCREENINFO = 0x4602


class _FBBitfield(ctypes.Structure):
    _fields_ = [
        ("offset", ctypes.c_uint32),
        ("length", ctypes.c_uint32),
        ("msb_right", ctypes.c_uint32),
    ]


class _FBVarScreeninfo(ctypes.Structure):
    _fields_ = [
        ("xres", ctypes.c_uint32),
        ("yres", ctypes.c_uint32),
        ("xres_virtual", ctypes.c_uint32),
        ("yres_virtual", ctypes.c_uint32),
        ("xoffset", ctypes.c_uint32),
        ("yoffset", ctypes.c_uint32),
        ("bits_per_pixel", ctypes.c_uint32),
        ("grayscale", ctypes.c_uint32),
        ("red", _FBBitfield),
        ("green", _FBBitfield),
        ("blue", _FBBitfield),
        ("transp", _FBBitfield),
        ("nonstd", ctypes.c_uint32),
        ("activate", ctypes.c_uint32),
        ("height", ctypes.c_uint32),
        ("width", ctypes.c_uint32),
        ("accel_flags", ctypes.c_uint32),
        ("pixclock", ctypes.c_uint32),
        ("left_margin", ctypes.c_uint32),
        ("right_margin", ctypes.c_uint32),
        ("upper_margin", ctypes.c_uint32),
        ("lower_margin", ctypes.c_uint32),
        ("hsync_len", ctypes.c_uint32),
        ("vsync_len", ctypes.c_uint32),
        ("sync", ctypes.c_uint32),
        ("vmode", ctypes.c_uint32),
        ("rotate", ctypes.c_uint32),
        ("colorspace", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 4),
    ]


class _FBFixScreeninfo(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_char * 16),
        ("smem_start", ctypes.c_ulong),
        ("smem_len", ctypes.c_uint32),
        ("type", ctypes.c_uint32),
        ("type_aux", ctypes.c_uint32),
        ("visual", ctypes.c_uint32),
        ("xpanstep", ctypes.c_uint16),
        ("ypanstep", ctypes.c_uint16),
        ("ywrapstep", ctypes.c_uint16),
        ("line_length", ctypes.c_uint32),
        ("mmio_start", ctypes.c_ulong),
        ("mmio_len", ctypes.c_uint32),
        ("accel", ctypes.c_uint32),
        ("capabilities", ctypes.c_uint16),
        ("reserved", ctypes.c_uint16 * 2),
    ]


def _mascara(bitfield):
    if bitfield.length == 0:
        return 0
    return ((1 << bitfield.length) - 1) << bitfield.offset


class FramebufferDirecto:
    """Abre /dev/fb0, expone ancho/alto/bpp reales, y permite volcar un
    pygame.Surface directamente a la pantalla via lseek+write, sin GPU."""

    def __init__(self, ruta_dispositivo="/dev/fb0"):
        self.ruta_dispositivo = ruta_dispositivo
        self.fd = None
        self.ancho = 0
        self.alto = 0
        self.bits_por_pixel = 0
        self.line_length = 0
        self.plantilla_formato = None  # pygame.Surface molde con los masks reales

    def abrir(self):
        import pygame  # import tardio para no obligar a pygame en modulos que solo leen info

        self.fd = os.open(self.ruta_dispositivo, os.O_RDWR)
        print(f"[fbdev] abierto {self.ruta_dispositivo}, fd={self.fd}")

        buf = bytearray(ctypes.sizeof(_FBVarScreeninfo))
        fcntl.ioctl(self.fd, FBIOGET_VSCREENINFO, buf)
        var = _FBVarScreeninfo.from_buffer_copy(buf)
        print(f"[fbdev] FBIOGET_VSCREENINFO OK: {var.xres}x{var.yres} @ {var.bits_per_pixel}bpp")

        buf2 = bytearray(ctypes.sizeof(_FBFixScreeninfo))
        fcntl.ioctl(self.fd, FBIOGET_FSCREENINFO, buf2)
        fix = _FBFixScreeninfo.from_buffer_copy(buf2)
        print(f"[fbdev] FBIOGET_FSCREENINFO OK: line_length={fix.line_length} smem_len={fix.smem_len}")

        self.ancho = var.xres
        self.alto = var.yres
        self.bits_por_pixel = var.bits_per_pixel
        self.line_length = fix.line_length or (var.xres * (var.bits_per_pixel // 8))

        rmask = _mascara(var.red)
        gmask = _mascara(var.green)
        bmask = _mascara(var.blue)
        amask = _mascara(var.transp)
        print(f"[fbdev] masks: r={hex(rmask)} g={hex(gmask)} b={hex(bmask)} a={hex(amask)}")

        # Superficie molde de 1x1 solo para que pygame sepa a que formato
        # convertir despues -- no se dibuja nada en ella.
        self.plantilla_formato = pygame.Surface(
            (1, 1), depth=self.bits_por_pixel, masks=(rmask, gmask, bmask, amask)
        )
        print("[fbdev] superficie molde creada OK")
        # No usamos mmap: algunos drivers de framebuffer viejos/limitados
        # (como el de este kernel 4.4 de Rockchip) no lo soportan bien y
        # devuelven EINVAL. En su lugar escribimos con lseek+write, que
        # pasa por una via del driver mas simple y mejor soportada.
        print("[fbdev] listo (modo lseek+write, sin mmap)")

    def presentar(self, superficie):
        """Recibe un pygame.Surface (en cualquier formato) del tamano
        (self.ancho, self.alto), lo convierte al formato real de la
        pantalla, y lo vuelca al framebuffer via lseek+write."""
        convertida = superficie.convert(self.plantilla_formato)
        pitch_origen = convertida.get_pitch()
        datos = bytes(convertida.get_buffer().raw)
        ancho_bytes = self.ancho * (self.bits_por_pixel // 8)

        if pitch_origen == self.line_length:
            os.lseek(self.fd, 0, os.SEEK_SET)
            os.write(self.fd, datos[: self.line_length * self.alto])
        else:
            # El stride de la superficie convertida no coincide con el del
            # framebuffer (puede pasar por alineacion) -- escribimos fila
            # por fila, cada una en su posicion exacta.
            for y in range(self.alto):
                inicio = y * pitch_origen
                fila = datos[inicio: inicio + ancho_bytes]
                os.lseek(self.fd, y * self.line_length, os.SEEK_SET)
                os.write(self.fd, fila)

    def cerrar(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
