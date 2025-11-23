-- Useful queries to inspect the goodyear2 database
-- Run these from MySQL client or with the provided Python scripts

-- 1) Show available tables
SHOW TABLES;

-- 2) Count rows in important tables
SELECT 'usuario' AS table_name, COUNT(*) AS cnt FROM usuario;
SELECT 'cliente' AS table_name, COUNT(*) AS cnt FROM cliente;
SELECT 'pronostico_historial' AS table_name, COUNT(*) AS cnt FROM pronostico_historial;

-- 3) List first 50 users
SELECT id_usuario, username, nombre_completo, email, telefono, id_rol, estado, fecha_creacion
FROM usuario
ORDER BY id_usuario
LIMIT 50;

-- 4) Show recent pronósticos
SELECT id, fecha, eagle_f1, assurance, wrangler, efficientgrip
FROM pronostico_historial
ORDER BY fecha DESC
LIMIT 50;

-- 5) Example joins (clients + orders) - adjust table names if needed
-- SELECT c.id_cliente, c.nombre_cliente, p.id_pedido, p.fecha_pedido, p.estado
-- FROM cliente c
-- LEFT JOIN pedido p ON c.id_cliente = p.id_cliente
-- ORDER BY c.id_cliente, p.fecha_pedido DESC
-- LIMIT 100;

-- 6) Describe table structures
DESCRIBE usuario;
DESCRIBE cliente;
DESCRIBE pronostico_historial;

-- 7) Get server version (MySQL client)
SELECT VERSION();
