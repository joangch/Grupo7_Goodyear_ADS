import csv, sqlite3, hashlib, os
from config.configuracion import DB_PATH, PASSWORD_SALT

def _hash(p): return hashlib.sha256((PASSWORD_SALT + p).encode("utf-8")).hexdigest()

# asegurar carpeta DB
db_dir = os.path.dirname(DB_PATH)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# Intentar crear la tabla objetivo si no existe (no modifica tablas ya existentes)
cur.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE NOT NULL,
    email TEXT,
    password_hash TEXT NOT NULL,
    rol TEXT NOT NULL
)
""")
con.commit()

# Leer esquema actual para saber si existe la columna 'password'
cur.execute("PRAGMA table_info(usuarios)")
existing_cols = [r[1] for r in cur.fetchall()]
has_password_col = "password" in existing_cols

with open("users.csv", newline="", encoding="utf-8") as f:
    rdr = csv.DictReader(f)
    for row in rdr:
        usuario = row["usuario"].strip()
        email = row.get("email","").strip()
        plain = row["password"].strip()
        rol = row.get("rol","cliente").strip()
        pwh = _hash(plain)
        cur.execute("SELECT id FROM usuarios WHERE usuario=?", (usuario,))
        r = cur.fetchone()
        if r:
            # Actualizar: si existe columna password, actualizarla también con el hash
            if has_password_col:
                cur.execute(
                    "UPDATE usuarios SET email=?, password=?, password_hash=?, rol=? WHERE id=?",
                    (email, pwh, pwh, rol, r[0])
                )
            else:
                cur.execute(
                    "UPDATE usuarios SET email=?, password_hash=?, rol=? WHERE id=?",
                    (email, pwh, rol, r[0])
                )
            print(f"Actualizado: {usuario}")
        else:
            # Insertar: incluir 'password' en columnas si existe en esquema (llenar con hash)
            if has_password_col:
                cur.execute(
                    "INSERT INTO usuarios (usuario,email,password,password_hash,rol) VALUES (?,?,?,?,?)",
                    (usuario, email, pwh, pwh, rol)
                )
            else:
                cur.execute(
                    "INSERT INTO usuarios (usuario,email,password_hash,rol) VALUES (?,?,?,?)",
                    (usuario, email, pwh, rol)
                )
            print(f"Insertado: {usuario}")
con.commit()
con.close()
print("Importación completada.")