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

(Actualmente trabajando en ello)