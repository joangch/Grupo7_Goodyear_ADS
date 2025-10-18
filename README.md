# 🧾 Goodyear – Sistema de Gestión de Reclamos y Logística (Prototipo Integrado)

Este repositorio contiene el desarrollo de un **prototipo funcional** orientado a la **gestión de procesos logísticos y de atención al cliente** de la empresa **Goodyear**.  
El proyecto busca **optimizar la comunicación entre clientes y áreas internas**, digitalizando procesos clave como **pedidos, reclamos, despachos, planificación y reportería**, usando **Python y Streamlit**.

---

## 🚀 Objetivo general

Diseñar un sistema modular que integre las principales operaciones de atención y logística, permitiendo:
- Registro y gestión de reclamos de clientes.
- Canalización automática hacia las áreas internas correspondientes.
- Seguimiento de pedidos y despachos.
- Comunicación interactiva mediante chat interno.
- Generación de reportes e indicadores de desempeño.

---

## 🧩 Módulos principales

| Módulo | Descripción |
|:-------|:-------------|
| 🔐 **Login y Roles** | Permite acceso diferenciado para *clientes* y *personal interno* con autenticación básica. |
| 📦 **Pedidos (Cliente)** | Registro de pedidos, cálculo de montos, seguimiento de estados y confirmación de entrega. |
| 🚚 **Despacho Interno** | Control de preparación, tránsito y entrega de pedidos; cálculo del *lead time*. |
| 🗓️ **Programación de Despachos** | Asignación de transportes, fechas y operarios mediante calendario integrado. |
| 🗺️ **Planificación de Rutas** | Optimización de recorridos y tiempos de entrega usando modelos Python o AMPL. |
| 🧾 **Reclamos (Cliente)** | Registro de reclamos con descripción, carga de imágenes y chat con el área de calidad. |
| 🧑‍🔧 **Reclamos Internos** | Atención de reclamos, actualización de estados y comunicación directa con clientes. |
| 📊 **Reportería** | Indicadores de desempeño, tiempos promedio y análisis de reclamos/pedidos. |
| 📈 **Pronóstico de Demanda** | Modelos predictivos para estimar ventas futuras y optimizar inventarios. |

---

## ⚙️ Tecnologías utilizadas

- **Lenguaje:** Python 🐍  
- **Framework:** Streamlit  
- **Base de datos:** SQLite  
- **Paradigma:** Programación Orientada a Objetos (POO)  
- **Gestión de archivos:** Validación y carga de imágenes  
- **Registro:** Sistema de logs para seguimiento de eventos  
- **Diseño:** Modular, limpio y documentado  

---

## 🧱 Estructura del proyecto

Raíz del repo (resumen):

```
Goodyear/
	main.py                 # App principal (Streamlit)
	interfaces/             # Páginas de la app (login, reclamos, reportería, etc.)
	modulos/                # Lógica de negocio (DB, validaciones, seguridad)
	config/                 # Configuración y constantes
	data/                   # Base de datos SQLite y otros datos
	logs/                   # Archivos de log
```

---

## ▶️ Cómo ejecutar el proyecto (Windows/PowerShell)

Requisitos:
- Python 3.10+ (probado con 3.13)
- Pip actualizado

1) Instalar dependencias

```powershell
cd c:\ADS-2025-2\sistema_reclamos
pip install -r Goodyear\requirements.txt
```

2) Crear carpetas necesarias (si no existen)

```powershell
mkdir -Force Goodyear\data, Goodyear\logs, Goodyear\uploads | Out-Null
```

3) Iniciar la app Streamlit (recomendado)

```powershell
python -m streamlit run Goodyear\main.py --server.port 8503
```

Si el puerto está en uso, prueba otro (ej: 8521):

```powershell
python -m streamlit run Goodyear\main.py --server.port 8521
```

Opcional (sin telemetría de Streamlit):

```powershell
python -m streamlit run Goodyear\main.py --server.port 8503 --browser.gatherUsageStats false
```

Alternativa breve (si `streamlit` está en tu PATH):

```powershell
streamlit run "Goodyear\main.py" --server.port 8503
```

Consejo: usar `python -m streamlit` asegura que se use el Streamlit del mismo intérprete de Python que tienes activo, evitando confusiones si hay varias instalaciones.

Liberar un puerto ocupado (ej. 8503):

```powershell
netstat -ano | findstr :8503
taskkill /PID <PID> /F
```

4) Crear usuarios demo (una vez dentro de la app)
- En el sidebar, selecciona “Seed (demo)” y pulsa los botones para crear:
	- cliente_demo / cliente123
	- interno_demo / interno123

5) Navegación básica
- Cliente: Pedidos, Reclamos
- Interno: Despacho, Programación, Rutas, Reclamos internos, Reportería, Pronósticos

Notas:
- La reportería usa el módulo limpio: `Goodyear/interfaces/reporteria_clean.py`.
- La base de datos SQLite se encuentra en `Goodyear/data/goodyear.db`.
- Si ves advertencias sobre `use_container_width`, no afectan el uso. Se migrarán a `width='stretch'` más adelante.

---

## 🧪 Verificación rápida

1) Inicia sesión como `cliente_demo` y registra un reclamo.
2) Cierra sesión; entra como `interno_demo`; revisa “Reclamos internos” y responde en el chat.
3) Abre “Reportería”, mueve filtros y prueba exportar Excel/PDF.

---

## 🛠️ Soporte

Si tienes problemas para levantar la app, comparte la salida de PowerShell y el contenido de `Goodyear/logs/`.