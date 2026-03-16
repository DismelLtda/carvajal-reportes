-- ============================================================================
-- ESQUEMA DE BASE DE DATOS - SISTEMA DE REPORTES DE VENTAS
-- ============================================================================
-- Tipo: SQLite 3 (compatible con PostgreSQL con mínimos cambios)
-- Fecha: 3 de marzo de 2026
-- ============================================================================

-- ============================================================================
-- TABLA 1: CABECERA DE REPORTES DE VENTAS
-- Almacena metadatos del reporte (proveedor, fechas, estado)
-- ============================================================================
CREATE TABLE reporte_ventas_cabecera (
    -- Identificadores
    id_cabecera INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_unico TEXT NOT NULL UNIQUE,  -- 770999027699220260227RV63935321
    hash_contenido TEXT NOT NULL UNIQUE,  -- SHA256 para detectar duplicados exactos
    
    -- Información del reporte
    nombre_archivo TEXT NOT NULL,
    proveedor TEXT NOT NULL,
    entidad_vendedora TEXT NOT NULL,
    
    -- Fechas del reporte
    fecha_inicio_reporte DATE NOT NULL,
    fecha_fin_reporte DATE NOT NULL,
    fecha_generacion DATETIME NOT NULL,
    
    -- Control de versiones
    version INTEGER DEFAULT 1,  -- v1, v2 si hay actualizaciones
    
    -- Estado del procesamiento
    estado TEXT DEFAULT 'procesado' 
        CHECK (estado IN ('procesado', 'error', 'duplicado')),
    
    -- Estadísticas
    total_filas INTEGER DEFAULT 0,
    
    -- Auditoría
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índices para tabla CABECERA
CREATE INDEX idx_cabecera_codigo_unico 
    ON reporte_ventas_cabecera(codigo_unico);
CREATE INDEX idx_cabecera_fecha_inicio 
    ON reporte_ventas_cabecera(fecha_inicio_reporte);
CREATE INDEX idx_cabecera_hash 
    ON reporte_ventas_cabecera(hash_contenido);
CREATE INDEX idx_cabecera_estado 
    ON reporte_ventas_cabecera(estado);
CREATE INDEX idx_cabecera_created 
    ON reporte_ventas_cabecera(created_at);

-- ============================================================================
-- TABLA 2: DETALLE DE REPORTES DE VENTAS
-- Almacena las 14 columnas exactas del Excel (preserva estructura)
-- ============================================================================
CREATE TABLE reporte_ventas_detalle (
    -- Identificadores
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cabecera INTEGER NOT NULL,
    
    -- ========== COLUMNAS DEL EXCEL (14 columnas exactas) ==========
    
    -- GRUPO 1: Punto de Venta (Columnas 1-3)
    pv_ean TEXT NOT NULL,                          -- Col 1: EAN (punto venta)
    pv_descripcion TEXT NOT NULL,                  -- Col 2: Descripción
    pv_codigo_interno TEXT NOT NULL,               -- Col 3: Código interno Almacén
    
    -- GRUPO 2: Fechas (Columnas 4-5)
    fecha_inicial DATE NOT NULL,                   -- Col 4: Fecha Inicial
    fecha_final DATE NOT NULL,                     -- Col 5: Fecha Final
    
    -- GRUPO 3: Información del Ítem (Columnas 6-9)
    item_ean TEXT NOT NULL,                        -- Col 6: Código EAN del item
    item_codigo_comprador TEXT,                    -- Col 7: Código ítem/Comprador (VACÍO)
    item_codigo_proveedor TEXT,                    -- Col 8: Código ítem/Proveedor (VACÍO)
    item_descripcion TEXT,                         -- Col 9: Descripción del ítem (VACÍO)
    
    -- GRUPO 4: Cantidades y Precios (Columnas 10-13)
    cantidad_vendida DECIMAL(10, 2) NOT NULL,     -- Col 10: Cantidad Vendida
    unidad_medida TEXT,                            -- Col 11: Unidad de Medida (VACÍO)
    precio_con_impuestos DECIMAL(12, 2) NOT NULL, -- Col 12: Precio con impuestos
    precio_sin_impuestos DECIMAL(12, 2),           -- Col 13: Precio sin impuestos (VACÍO)
    
    -- GRUPO 5: Reservado para futuro (Columna 14)
    columna_reservada_14 TEXT,                     -- Col 14: Reservado (VACÍO)
    
    -- ========== COLUMNAS DE NEGOCIO/AUDITORÍA ==========
    numero_fila_origen INTEGER NOT NULL,           -- Para auditoría (fila en Excel)
    estado_validacion TEXT DEFAULT 'OK'
        CHECK (estado_validacion IN ('OK', 'WARNING', 'ERROR')),
    
    -- Auditoría
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Restricciones
    FOREIGN KEY (id_cabecera) REFERENCES reporte_ventas_cabecera(id_cabecera)
        ON DELETE CASCADE,
    UNIQUE(id_cabecera, numero_fila_origen)  -- Evita duplicados por fila
);

-- Índices para tabla DETALLE
CREATE INDEX idx_detalle_cabecera 
    ON reporte_ventas_detalle(id_cabecera);
CREATE INDEX idx_detalle_item_ean 
    ON reporte_ventas_detalle(item_ean);
CREATE INDEX idx_detalle_pv_ean 
    ON reporte_ventas_detalle(pv_ean);
CREATE INDEX idx_detalle_fecha_inicial 
    ON reporte_ventas_detalle(fecha_inicial);
CREATE INDEX idx_detalle_cantidad 
    ON reporte_ventas_detalle(cantidad_vendida);

-- ============================================================================
-- TABLA 3: LOG DE INTENTOS (AUDITORÍA)
-- Registra cada intento de carga (nueva, duplicada, error, etc)
-- ============================================================================
CREATE TABLE reporte_ventas_log (
    -- Identificadores
    id_log INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Información del intento
    codigo_unico TEXT,
    nombre_archivo TEXT,
    hash_contenido TEXT,
    
    -- Tipo de intento
    tipo_intento TEXT NOT NULL
        CHECK (tipo_intento IN ('nueva_carga', 'intento_duplicado', 'error')),
    
    -- Detalles
    descripcion TEXT,
    
    -- Auditoría
    fecha_intento DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índices para tabla LOG
CREATE INDEX idx_log_codigo_unico 
    ON reporte_ventas_log(codigo_unico);
CREATE INDEX idx_log_tipo_intento 
    ON reporte_ventas_log(tipo_intento);
CREATE INDEX idx_log_fecha 
    ON reporte_ventas_log(fecha_intento);

-- ============================================================================
-- TABLA 4: RESUMEN DIARIO (CACHÉ)
-- Totales por día para consultas rápidas desde Odoo
-- ============================================================================
CREATE TABLE reporte_ventas_resumen_diario (
    -- Identificadores
    id_resumen INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Fecha (clave compuesta)
    fecha_reporte DATE NOT NULL UNIQUE,
    año INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    dia INTEGER NOT NULL,
    
    -- Totales del día
    total_puntos_venta INTEGER,              -- COUNT(DISTINCT pv_ean)
    total_items_vendidos INTEGER,            -- COUNT(DISTINCT item_ean)
    total_cantidad_vendida DECIMAL(15, 2),   -- SUM(cantidad_vendida)
    total_ventas_con_impuestos DECIMAL(15, 2),   -- SUM(precio_con_impuestos * cantidad)
    total_ventas_sin_impuestos DECIMAL(15, 2),   -- SUM(precio_sin_impuestos * cantidad)
    cantidad_reportes INTEGER,               -- COUNT(DISTINCT codigo_reporte)
    
    -- Auditoría
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índices para tabla RESUMEN
CREATE INDEX idx_resumen_fecha 
    ON reporte_ventas_resumen_diario(fecha_reporte);
CREATE INDEX idx_resumen_año_mes 
    ON reporte_ventas_resumen_diario(año, mes);
CREATE INDEX idx_resumen_mes_dia 
    ON reporte_ventas_resumen_diario(mes, dia);

-- ============================================================================
-- VISTAS (Queries comunes)
-- ============================================================================

-- Vista: Resumen completo de un reporte
CREATE VIEW vw_reporte_resumen AS
SELECT 
    c.id_cabecera,
    c.codigo_unico,
    c.proveedor,
    c.entidad_vendedora,
    c.fecha_inicio_reporte,
    c.fecha_fin_reporte,
    c.version,
    c.estado,
    COUNT(d.id_detalle) as total_detalles,
    SUM(d.cantidad_vendida) as total_cantidad,
    SUM(d.precio_con_impuestos * d.cantidad_vendida) as total_ventas,
    c.created_at
FROM reporte_ventas_cabecera c
LEFT JOIN reporte_ventas_detalle d ON c.id_cabecera = d.id_cabecera
GROUP BY c.id_cabecera;

-- Vista: Productos más vendidos
CREATE VIEW vw_productos_mas_vendidos AS
SELECT 
    item_ean,
    item_descripcion,
    COUNT(*) as veces_vendido,
    SUM(cantidad_vendida) as total_cantidad,
    SUM(precio_con_impuestos * cantidad_vendida) as total_ingresos
FROM reporte_ventas_detalle
WHERE estado_validacion = 'OK'
GROUP BY item_ean
ORDER BY total_cantidad DESC;

-- Vista: Puntos de venta con más ventas
CREATE VIEW vw_puntos_venta_activos AS
SELECT 
    pv_ean,
    pv_descripcion,
    COUNT(*) as items_vendidos,
    SUM(cantidad_vendida) as total_cantidad,
    SUM(precio_con_impuestos * cantidad_vendida) as total_ingresos
FROM reporte_ventas_detalle
WHERE estado_validacion = 'OK'
GROUP BY pv_ean
ORDER BY total_ingresos DESC;

-- ============================================================================
-- TABLA 5: CABECERA DE REPORTES DE INVENTARIO
-- Almacena metadatos del reporte de inventario
-- ============================================================================
CREATE TABLE reporte_inventario_cabecera (
    -- Identificadores
    id_cabecera INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_unico TEXT NOT NULL UNIQUE,  -- 80008987202026022713638
    hash_contenido TEXT NOT NULL UNIQUE,  -- SHA256 para detectar duplicados exactos
    
    -- Información del reporte
    nombre_archivo TEXT NOT NULL,
    emisor TEXT NOT NULL,              -- SUPERTIENDAS Y DROGUERIAS OLIMPICAS S.A.
    receptor TEXT NOT NULL,            -- Dismel Ltda
    
    -- Fechas del reporte
    fecha_inicio_reporte DATE NOT NULL,
    fecha_fin_reporte DATE NOT NULL,
    
    -- Control de versiones
    version INTEGER DEFAULT 1,  -- v1, v2 si hay actualizaciones
    
    -- Estado del procesamiento
    estado TEXT DEFAULT 'procesado' 
        CHECK (estado IN ('procesado', 'error', 'duplicado')),
    
    -- Estadísticas
    total_filas INTEGER DEFAULT 0,
    
    -- Auditoría
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índices para tabla CABECERA INVENTARIO
CREATE INDEX idx_inv_cabecera_codigo_unico 
    ON reporte_inventario_cabecera(codigo_unico);
CREATE INDEX idx_inv_cabecera_fecha_inicio 
    ON reporte_inventario_cabecera(fecha_inicio_reporte);
CREATE INDEX idx_inv_cabecera_hash 
    ON reporte_inventario_cabecera(hash_contenido);
CREATE INDEX idx_inv_cabecera_estado 
    ON reporte_inventario_cabecera(estado);

-- ============================================================================
-- TABLA 6: DETALLE DE REPORTES DE INVENTARIO
-- Almacena las 13 columnas del Excel (stock de productos por ubicación)
-- ============================================================================
CREATE TABLE reporte_inventario_detalle (
    -- Identificadores
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cabecera INTEGER NOT NULL,
    
    -- ========== COLUMNAS DEL EXCEL (13 columnas) ==========
    
    -- GRUPO 1: Producto (Columnas 1-4)
    codigo_producto_ean TEXT NOT NULL,        -- Col 1: Código Producto / EAN
    descripcion_producto TEXT NOT NULL,       -- Col 2: Descripción de Producto
    columna_3_reservada TEXT,                 -- Col 3: [VACÍO]
    codigo_interno_almacen TEXT NOT NULL,     -- Col 4: Código interno Almacén
    
    -- GRUPO 2: Cantidad y Ubicación (Columnas 5-8)
    cantidad_stock DECIMAL(12, 2) NOT NULL,   -- Col 5: Cantidad
    codigo_lugar TEXT NOT NULL,                -- Col 6: Código Lugar (ubicación)
    columna_7_reservada TEXT,                 -- Col 7: [VACÍO]
    nombre_lugar TEXT NOT NULL,                -- Col 8: Nombre Lugar
    
    -- GRUPO 3: Información de Comprador y Precios (Columnas 9-12)
    codigo_item_comprador TEXT NOT NULL,      -- Col 9: Código de item / Comprador
    precio_lista DECIMAL(12, 2) NOT NULL,     -- Col 10: Precio Lista
    precio_neto_1 DECIMAL(12, 2) NOT NULL,    -- Col 11: Precio Neto (1)
    precio_neto_2 DECIMAL(12, 2) NOT NULL,    -- Col 12: Precio Neto (2)
    
    -- GRUPO 4: Reservado (Columna 13)
    columna_13_reservada TEXT,                -- Col 13: [VACÍO]
    
    -- ========== COLUMNAS DE NEGOCIO/AUDITORÍA ==========
    numero_fila_origen INTEGER NOT NULL,      -- Para auditoría (fila en Excel)
    estado_validacion TEXT DEFAULT 'OK'
        CHECK (estado_validacion IN ('OK', 'WARNING', 'ERROR')),
    
    -- Auditoría
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Restricciones
    FOREIGN KEY (id_cabecera) REFERENCES reporte_inventario_cabecera(id_cabecera)
        ON DELETE CASCADE,
    UNIQUE(id_cabecera, numero_fila_origen)  -- Evita duplicados por fila
);

-- Índices para tabla DETALLE INVENTARIO
CREATE INDEX idx_inv_detalle_cabecera 
    ON reporte_inventario_detalle(id_cabecera);
CREATE INDEX idx_inv_detalle_ean 
    ON reporte_inventario_detalle(codigo_producto_ean);
CREATE INDEX idx_inv_detalle_lugar 
    ON reporte_inventario_detalle(codigo_lugar);
CREATE INDEX idx_inv_detalle_codigo_comprador 
    ON reporte_inventario_detalle(codigo_item_comprador);

-- ============================================================================
-- TABLA 7: RESUMEN DIARIO INVENTARIO
-- Stock total por ubicación/día (DIFERENTE a Ventas: es SNAPSHOT, no incremental)
-- ============================================================================
CREATE TABLE reporte_inventario_resumen_diario (
    -- Identificadores
    id_resumen INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Fecha (clave compuesta)
    fecha_reporte DATE NOT NULL UNIQUE,
    año INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    dia INTEGER NOT NULL,
    
    -- Totales del día (SNAPSHOT - reemplaza anterior, no suma)
    total_ubicaciones INTEGER,              -- COUNT(DISTINCT codigo_lugar)
    total_productos INTEGER,                -- COUNT(DISTINCT codigo_producto_ean)
    total_cantidad_stock DECIMAL(15, 2),    -- SUM(cantidad_stock)
    valor_total_lista DECIMAL(15, 2),       -- SUM(precio_lista * cantidad_stock)
    valor_total_neto DECIMAL(15, 2),        -- SUM(precio_neto * cantidad_stock)
    cantidad_reportes INTEGER,              -- COUNT(DISTINCT codigo_reporte)
    
    -- Auditoría
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índices para tabla RESUMEN INVENTARIO
CREATE INDEX idx_inv_resumen_fecha 
    ON reporte_inventario_resumen_diario(fecha_reporte);
CREATE INDEX idx_inv_resumen_año_mes 
    ON reporte_inventario_resumen_diario(año, mes);

-- ============================================================================
-- TABLA 8: LOG COMPARTIDO (Auditoría para Ventas + Inventario)
-- ============================================================================
-- Nota: reporte_ventas_log ya existe, expandimos reporte_ventas_log
-- para que sea agnóstico de tipo de reporte

-- Actualizar tabla log existente (si es necesario)
-- CREATE TABLE reporte_log_general (se puede hacer después si se necesita unificado)

-- ============================================================================
-- DATOS DE PRUEBA (OPCIONAL)
-- ============================================================================

-- Insertar reporte de prueba
INSERT INTO reporte_ventas_cabecera (
    codigo_unico,
    hash_contenido,
    nombre_archivo,
    proveedor,
    entidad_vendedora,
    fecha_inicio_reporte,
    fecha_fin_reporte,
    fecha_generacion,
    estado,
    total_filas
) VALUES (
    '770999027699220260227RV63935321',
    'abc123def456ghi789jkl012mno345pqr678stu901',
    'VENTAS_PAGE1_FILA1_20260227_161509.xlsx',
    'Dismel Ltda',
    'SUPERTIENDAS Y DROGUERIAS OLIMPICAS S.A.',
    '2026-02-26',
    '2026-02-26',
    '2026-02-27 16:15:09',
    'procesado',
    60
);

-- Insertar detalles de prueba
INSERT INTO reporte_ventas_detalle (
    id_cabecera,
    pv_ean,
    pv_descripcion,
    pv_codigo_interno,
    fecha_inicial,
    fecha_final,
    item_ean,
    item_codigo_comprador,
    item_codigo_proveedor,
    item_descripcion,
    cantidad_vendida,
    unidad_medida,
    precio_con_impuestos,
    precio_sin_impuestos,
    columna_reservada_14,
    numero_fila_origen,
    estado_validacion
) VALUES (
    1,
    '7701008002562',
    'SAO 256 AGUACHICA Cr 23',
    'SAO 256 AGUACHICA Cr 23',
    '2026-02-26',
    '2026-02-26',
    '7708894411683',
    NULL,
    NULL,
    NULL,
    1.0,
    NULL,
    5294.0,
    NULL,
    NULL,
    10,
    'OK'
);

-- ============================================================================
-- INFORMACIÓN SOBRE ÍNDICES
-- ============================================================================

-- ÍNDICES CRÍTICOS (performance):
-- 1. idx_cabecera_codigo_unico     → Para búsqueda rápida por código
-- 2. idx_detalle_item_ean          → Para filtrar por producto
-- 3. idx_detalle_fecha_inicial     → Para rangos de fecha
-- 4. idx_resumen_fecha             → Para queries diarias

-- ÍNDICES SECUNDARIOS:
-- 5. idx_cabecera_hash             → Para detectar duplicados
-- 6. idx_detalle_pv_ean            → Para analytics por punto de venta
-- 7. idx_log_tipo_intento          → Para monitoreo

-- ============================================================================
-- NOTAS IMPORTANTES
-- ============================================================================

-- 1. CÓDIGOS ÚNICOS:
--    - codigo_unico: Siempre único (el mismo reporte no se carga dos veces)
--    - hash_contenido: Detecta si el CONTENIDO es idéntico
--    
--    Ejemplos:
--    ✓ Mismo código + mismo hash = DUPLICADO (rechazar)
--    ✗ Mismo código + diferente hash = NUEVA VERSIÓN (v2)

-- 2. COLUMNAS VACÍAS EN EXCEL:
--    Están presentes en la tabla para futuros datos:
--    - item_codigo_comprador (Col 7)
--    - item_codigo_proveedor (Col 8)
--    - item_descripcion (Col 9)
--    - unidad_medida (Col 11)
--    - precio_sin_impuestos (Col 13)
--    - columna_reservada_14 (Col 14)

-- 3. VERSIONADO:
--    Si llega actualización:
--    - Misma código_unico pero diferente contenido
--    - Se crea NEW RECORD con version = 2
--    - Mantiene historial completo

-- 4. CASCADA:
--    Si se elimina un reporte (cabecera):
--    - Se eliminan automáticamente todos sus detalles (FOREIGN KEY CASCADE)
--    - El log se mantiene para auditoría

-- 5. MIGRACIONES:
--    Para producción (PostgreSQL):
--    - Cambiar AUTOINCREMENT por SERIAL
--    - Cambiar DEFAULT CURRENT_TIMESTAMP por CURRENT_TIMESTAMP
--    - El resto del código es compatible
