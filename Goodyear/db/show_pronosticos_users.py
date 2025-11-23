#!/usr/bin/env python3
from pathlib import Path
import sys
import json
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent))

try:
    from Goodyear.config.configuracion import DATABASE_URL
except Exception:
    import os
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        print(json.dumps({"error": "No DATABASE_URL available and config import failed"}, ensure_ascii=False))
        raise SystemExit(1)


def fetch_all(conn, sql):
    res = conn.execute(text(sql))
    cols = res.keys()
    return [dict(zip(cols, row)) for row in res.fetchall()]


def main():
    engine = create_engine(DATABASE_URL, future=True)
    with engine.connect() as conn:
        pronosticos = fetch_all(conn, "SELECT id, fecha, eagle_f1, assurance, wrangler, efficientgrip FROM pronostico_historial ORDER BY fecha ASC LIMIT 1000")
        usuarios = fetch_all(conn, "SELECT id_usuario, username, nombre_completo, email, telefono, id_rol, estado, fecha_creacion FROM usuario ORDER BY id_usuario LIMIT 500")

    out = {
        "pronosticos_count": len(pronosticos),
        "pronosticos": pronosticos,
        "usuarios_count": len(usuarios),
        "usuarios": usuarios,
    }
    print(json.dumps(out, default=str, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
