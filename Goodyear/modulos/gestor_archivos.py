
import os
import uuid
from pathlib import Path
from typing import List
from config.configuracion import UPLOAD_DIR

def asegurar_directorio():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def guardar_imagen(contenido: bytes, nombre_original: str, reclamo_id: int) -> str:
    asegurar_directorio()
    ext = Path(nombre_original).suffix.lower()
    nuevo_nombre = f"reclamo_{reclamo_id}_{uuid.uuid4().hex}{ext}"
    ruta = UPLOAD_DIR / nuevo_nombre
    with open(ruta, "wb") as f:
        f.write(contenido)
    return str(ruta)

def listar_archivos_reclamo(reclamo_id: int) -> List[str]:
    asegurar_directorio()
    patron = f"reclamo_{reclamo_id}_"
    return [str(p) for p in UPLOAD_DIR.iterdir() if p.is_file() and p.name.startswith(patron)]
