import sqlite3
from pathlib import Path

# Ubicar la base de datos en Goodyear/data/goodyear.db (subir un nivel desde utils/)
goodyear_dir = Path(__file__).resolve().parent.parent
data_dir = goodyear_dir / "data"
data_dir.mkdir(parents=True, exist_ok=True)
db_path = data_dir / "goodyear.db"

con = sqlite3.connect(db_path)
cur = con.cursor()

# Asegurar la tabla usuarios para evitar errores en entornos nuevos
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        email TEXT,
        password_hash TEXT NOT NULL,
        rol TEXT NOT NULL
    )
    """
)
con.commit()

cur.execute('SELECT id, usuario, email, rol FROM usuarios')
usuarios = cur.fetchall()

print("\n" + "="*60)
print("📋 USUARIOS EN LA BASE DE DATOS")
print("="*60)

if usuarios:
    for u in usuarios:
        print(f"\n  🔹 ID: {u[0]}")
        print(f"     Usuario: {u[1]}")
        print(f"     Email: {u[2]}")
        print(f"     Rol: {u[3]}")
    print("\n" + "="*60)
    print(f"✅ Total: {len(usuarios)} usuario(s) registrado(s)")
else:
    print("\n  ⚠️  No hay usuarios en la base de datos")
    
print("="*60 + "\n")

con.close()
