"""Utilidades de formato compartidas por varias pantallas."""


def formatear_bytes(cantidad):
    """Formatea bytes como B / KB / MB / GB (ej. 512 B, 3.4 MB, 1.20 GB)."""
    valor = float(cantidad)
    for unidad in ("B", "KB", "MB"):
        if valor < 1024:
            return f"{valor:.0f} {unidad}" if unidad == "B" else f"{valor:.1f} {unidad}"
        valor /= 1024
    return f"{valor:.2f} GB"
