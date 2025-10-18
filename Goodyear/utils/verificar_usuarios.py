import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "data" / "goodyear.db"
con = sqlite3.connect(db_path)
cur = con.cursor()

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
