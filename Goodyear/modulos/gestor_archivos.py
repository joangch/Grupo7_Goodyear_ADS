
import os
import uuid
from pathlib import Path
from typing import List
from config.configuracion import UPLOADS_DIR

def asegurar_directorio():
    """Asegura que el directorio de uploads exista."""
    Path(UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

def guardar_imagen(contenido: bytes, nombre_original: str, reclamo_id: int) -> str:
    """
    Guarda una imagen con un nombre único y retorna la ruta completa.
    
    Args:
        contenido: Bytes de la imagen
        nombre_original: Nombre original del archivo
        reclamo_id: ID del reclamo asociado
    
    Returns:
        Ruta completa del archivo guardado
    """
    asegurar_directorio()
    ext = Path(nombre_original).suffix.lower()
    nuevo_nombre = f"reclamo_{reclamo_id}_{uuid.uuid4().hex}{ext}"
    ruta = Path(UPLOADS_DIR) / nuevo_nombre
    with open(ruta, "wb") as f:
        f.write(contenido)
    return str(ruta)

def listar_archivos_reclamo(reclamo_id: int) -> List[str]:
    """Lista todos los archivos asociados a un reclamo específico."""
    asegurar_directorio()
    patron = f"reclamo_{reclamo_id}_"
    uploads_path = Path(UPLOADS_DIR)
    return [str(p) for p in uploads_path.iterdir() if p.is_file() and p.name.startswith(patron)]
