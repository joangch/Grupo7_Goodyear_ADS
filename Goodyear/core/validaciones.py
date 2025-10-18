
import re
from typing import Optional
from pathlib import Path
from . import gestor_archivos
from config.configuracion import EXT_IMAGENES, MAX_IMG_SIZE

def validar_usuario(usuario: str) -> bool:
    return bool(usuario and 3 <= len(usuario) <= 50)

def validar_password(password: str) -> bool:
    return bool(password and len(password) >= 6)

def validar_email(email: str) -> bool:
    if not email:
        return False
    patron = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(patron, email))

def validar_descripcion(descripcion: str, min_len: int = 10, max_len: int = 1000) -> bool:
    if not descripcion:
        return False
    return min_len <= len(descripcion.strip()) <= max_len

def validar_imagen(nombre: str, contenido: bytes) -> Optional[str]:
    """Valida extensión y tamaño. Retorna None si es válida o mensaje de error."""
    ext = Path(nombre).suffix.lower()
    if ext not in EXT_IMAGENES:
        return f"Formato no permitido ({ext}). Extensiones permitidas: {', '.join(sorted(EXT_IMAGENES))}."
    if contenido is None or len(contenido) == 0:
        return "El archivo está vacío."
    if len(contenido) > MAX_IMG_SIZE:
        return f"El archivo supera el tamaño máximo permitido de {MAX_IMG_SIZE // (1024*1024)}MB."
    return None
