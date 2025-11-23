from pathlib import Path
import sys
import logging
import argparse

# Este archivo está dentro de Goodyear/db; insertar el root del repo en sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent))

from Goodyear.config.configuracion import DATABASE_URL
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

try:
    import sqlparse

    def split_statements(sql_text):
        return [s.strip() for s in sqlparse.split(sql_text) if s.strip()]
except Exception:
    def split_statements(sql_text):
        return [s.strip() for s in sql_text.split(";") if s.strip()]


def run_file(path, engine):
    path = Path(path)
    logging.info(f"Leyendo {path}")
    sql = path.read_text(encoding="utf-8")
    statements = split_statements(sql)
    logging.info(f"{len(statements)} statements encontradas")
    with engine.begin() as conn:
        for i, stmt in enumerate(statements, 1):
            try:
                logging.info(f"Ejecutando stmt {i}")
                conn.exec_driver_sql(stmt)
            except Exception:
                logging.exception(f"Fallo en stmt {i}:")
                raise


def main():
    p = argparse.ArgumentParser(description="Ejecutar archivos SQL contra DATABASE_URL")
    p.add_argument("files", nargs="+", help="Archivos .sql a ejecutar en orden")
    args = p.parse_args()

    engine = create_engine(DATABASE_URL, future=True)
    for f in args.files:
        run_file(f, engine)
    logging.info("Migraciones finalizadas.")


if __name__ == "__main__":
    main()
