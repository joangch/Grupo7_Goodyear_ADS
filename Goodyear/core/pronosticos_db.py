from sqlalchemy import create_engine, text
from config.configuracion import DATABASE_URL

# Engine used for read-only access to forecast tables
engine = create_engine(DATABASE_URL, future=True)

# NOTE: Seeding utilities were removed from core runtime because this
# application reads historicals from your production table `pronostico_historial`.
# If you need to seed a local/dev DB, use the SQL in `Goodyear/db/migrations/seed_forecast_data.sql`
# or run a separate admin script under `Goodyear/db/`.


def fetch_series(table_name: str = 'ventas_demanda') -> dict:
    """Fetches the series from DB and returns a dict with keys: fecha, eagle_f1, assurance, wrangler, efficientgrip
    Dates are formatted as YYYY-MM-DD strings and rows ordered ascending.
    """
    q = text(f"SELECT fecha, eagle_f1, assurance, wrangler, efficientgrip FROM {table_name} ORDER BY fecha ASC")
    with engine.connect() as conn:
        rows = conn.execute(q).all()

    data = {'fecha': [], 'eagle_f1': [], 'assurance': [], 'wrangler': [], 'efficientgrip': []}
    for r in rows:
        fecha = r[0]
        if hasattr(fecha, 'isoformat'):
            fecha = fecha.isoformat()
        data['fecha'].append(str(fecha))
        data['eagle_f1'].append(int(r[1]))
        data['assurance'].append(int(r[2]))
        data['wrangler'].append(int(r[3]))
        data['efficientgrip'].append(int(r[4]))

    return data
