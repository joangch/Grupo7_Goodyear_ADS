
# Goodyear - Sistema de Reclamos (Prototipo con Streamlit)

Este prototipo implementa:
- Login básico con roles (cliente, interno)
- Módulo de Reclamos (Cliente): crear reclamos, subir imágenes, chat por reclamo
- Módulo Interno de Reclamos: bandeja, filtros, cambio de estado, visualización de imágenes, chat
- Persistencia con SQLite
- Validaciones y manejo de errores
- Logs

## Ejecutar
```bash
pip install streamlit
streamlit run main.py
```

**Usuarios de prueba**
- Cliente: `cliente_demo` / `cliente123`
- Interno: `interno_demo` / `interno123`
