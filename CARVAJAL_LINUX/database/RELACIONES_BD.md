# 🔗 RELACIONES Y FLUJO DE DATOS ENTRE TABLAS

## Visualización de Cómo Conectan las 4 Tablas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  📋 reporte_ventas_cabecera                     (1 registro)               │
│  ┌──────────────────────────────────────────┐                             │
│  │ id_cabecera: 1                           │                             │
│  │ codigo_unico: 770999027699220260227...   │──┐                          │
│  │ hash_contenido: a1b2c3d4e5f6g7h8...      │  │                          │
│  │ proveedor: Dismel Ltda                   │  │                          │
│  │ entidad_vendedora: SUPERTIENDAS...       │  │                          │
│  │ fecha_inicio_reporte: 2026-02-26         │  │                          │
│  │ fecha_fin_reporte: 2026-02-26            │  │                          │
│  │ estado: procesado                        │  │                          │
│  │ version: 1                               │  │                          │
│  │ total_filas: 60                          │  │                          │
│  │ created_at: 2026-03-03 10:00:00          │  │                          │
│  └──────────────────────────────────────────┘  │                          │
│                         │                      │                          │
│                         └──────────────────────┼──────────────────────┐   │
│                                                │                      │   │
│  📝 reporte_ventas_log (1 registro)            │      📊 reporte_ventas_detalle (60 registros)
│  ┌──────────────────────────────────────────┐  │      ┌──────────────────────────────────────┐
│  │ id_log: 1                                │  │      │ id_detalle: 1                        │
│  │ codigo_unico: 770999027699220260227...   │  │      │ id_cabecera: 1 ◄─────────────┐       │
│  │ hash_contenido: a1b2c3d4e5f6...          │  │      │ pv_ean: 7701008002562        │       │
│  │ tipo_intento: nueva_carga                │  │      │ pv_descripcion: SAO 256...    │       │
│  │ descripcion: Reporte 60 filas procesado  │  │      │ item_ean: 7708894411683       │       │
│  │ fecha_intento: 2026-03-03 10:00:00       │  │      │ cantidad_vendida: 1.0         │       │
│  └──────────────────────────────────────────┘  │      │ precio_con_impuestos: 5294    │       │
│                                                │      │ ... (10 más columnas)         │       │
│                                                │      │ numero_fila_origen: 10        │       │
│  📈 reporte_ventas_resumen_diario (1 registro) │      │ estado_validacion: OK         │       │
│  ┌──────────────────────────────────────────┐  │      │ fecha_registro: 2026-03-03    │       │
│  │ id_resumen: 1                            │  │      │                               │       │
│  │ fecha_reporte: 2026-02-26                │  │      └──────────────┬─────────────────────┘
│  │ año: 2026                                │  │                    │
│  │ mes: 2                                   │  │      ┌─────────────▼─────────────────────┐
│  │ dia: 26                                  │  │      │ id_detalle: 2                      │
│  │ total_puntos_venta: 8                    │  │      │ id_cabecera: 1 ◄─────────────┐     │
│  │ total_items_vendidos: 15                 │  │      │ pv_ean: 7701008002562        │     │
│  │ total_cantidad_vendida: 75               │  │      │ item_ean: 7708894411348       │     │
│  │ total_ventas_con_impuestos: 450000       │  │      │ cantidad_vendida: 2.0         │     │
│  │ cantidad_reportes: 1                     │  │      │ ... (11 más)                  │     │
│  │ fecha_actualizacion: 2026-03-03 10:00   │  │      │                               │     │
│  └──────────────────────────────────────────┘  │      └──────────────┬─────────────────────┘
│                                                │                    │
│                         ┌───────────────────────┘      ... (58 registros más)
│                         │
└─────────────────────────┼──────────────────────────────────────────────┘
```

---

## 📊 Conteo de Registros

```
1 reporte procesado = 1 cabecera + 60 detalles + 1 auditoría + (1 ó update) resumen
                    = 62 registros nuevos (en primera carga del día)

Si llega otro reporte el MISMO día:
                    = 1 cabecera + 60 detalles + 1 auditoría (+ NO inserta resumen, solo UPDATE)
                    = 62 registros nuevos (+ UPDATE 1)

Si llega reporte DIFERENTE día:
                    = 1 cabecera + 60 detalles + 1 auditoría + 1 resumen
                    = 62 registros nuevos
```

---

## 🔄 Flujos de Relación

### Flujo 1: Consultar Reporte Completo
```sql
START: codigo_unico = '770999027699220260227RV63935321'
       ↓
LOOKUP: reporte_ventas_cabecera 
        WHERE codigo_unico = ?
       ↓
FOUND: id_cabecera = 1
       ↓
JOIN: SELECT * FROM reporte_ventas_detalle 
      WHERE id_cabecera = 1
       ↓
RESULT: 1 cabecera + 60 detalles
        [Desde API: GET /ventas/{codigo_unico}]
```

### Flujo 2: Detectar Duplicado
```sql
START: Hash nuevo = a1b2c3d4e5f6...
       Código nuevo = 770999027699220260227RV63935321
       ↓
CHECK: SELECT id_cabecera 
       FROM reporte_ventas_cabecera 
       WHERE codigo_unico = ? AND hash_contenido = ?
       ↓
FOUND: id_cabecera = 1 (con mismo hash)
       ↓
DECISION: RECHAZAR (DUPLICADO)
          INSERT log (tipo = 'intento_duplicado')
          RESPONSE: 202 Accepted (Duplicado detectado)
```

### Flujo 3: Nueva Versión
```sql
START: Hash nuevo = ZZZZZZZZZZZZZ... (DIFERENTE)
       Código nuevo = 770999027699220260227RV63935321 (MISMO)
       ↓
CHECK: SELECT id_cabecera, version, hash_contenido
       FROM reporte_ventas_cabecera 
       WHERE codigo_unico = ?
       ↓
FOUND: id_cabecera = 1, version = 1, hash = diferente
       ↓
DECISION: NUEVA VERSIÓN
          INSERT cabecera (version = 2, hash = nuevo, estado = 'procesado')
          INSERT 60 detalles (id_cabecera = 2)
          INSERT log (tipo = 'nueva_carga')
          UPDATE resumen (modificar totales)
```

### Flujo 4: Resumen Diario Automático
```sql
START: Procesamiento de reporte para fecha 2026-02-26
       ↓
CHECK: SELECT id_resumen FROM reporte_ventas_resumen_diario
       WHERE fecha_reporte = '2026-02-26'
       ↓
NO FOUND: Insertamos
          INSERT resumen_diario (
            fecha_reporte = '2026-02-26',
            total_puntos_venta = 8,
            total_items_vendidos = 15,
            total_cantidad_vendida = 75,
            total_ventas = 450000,
            cantidad_reportes = 1
          )
          ↓
FOUND (después): Update
         UPDATE resumen_diario SET
           total_cantidad_vendida += 75,
           total_ventas += 450000,
           cantidad_reportes = 2,
           fecha_actualizacion = NOW()
         WHERE fecha_reporte = '2026-02-26'
```

---

## 🔐 Integridad Referencial

```
ELIMINACIÓN EN CASCADA:
┌─ DELETE FROM reporte_ventas_cabecera WHERE id = 1
│
├─► CASCADE: DELETE FROM reporte_ventas_detalle WHERE id_cabecera = 1
│   └─ Elimina 60 registros automáticamente
│
└─ NOTA: reporte_ventas_log NO se elimina
         (mantiene auditoría histórica)

RESTRICCIONES ÚNICAS:
┌─ codigo_unico (UNIQUE)
│  └─ No permite dos cabeceras con mismo código_único
│
├─ hash_contenido (UNIQUE)
│  └─ No permite dos cabeceras con mismo hash
│
└─ (id_cabecera, numero_fila_origen) (UNIQUE)
   └─ No permite dos detalles de mismo reporte en misma fila origen
```

---

## 📊 Ejemplos de Consultas que Usan Relaciones

### Ejemplo 1: Reporte Completo (Para API)
```sql
SELECT 
    c.id_cabecera,
    c.codigo_unico,
    c.proveedor,
    c.entidad_vendedora,
    c.fecha_inicio_reporte,
    c.fecha_fin_reporte,
    c.total_filas,
    COUNT(d.id_detalle) as detalles_guardados,
    SUM(d.cantidad_vendida) as total_cantidad,
    SUM(d.precio_con_impuestos * d.cantidad_vendida) as total_venta
FROM reporte_ventas_cabecera c
LEFT JOIN reporte_ventas_detalle d ON c.id_cabecera = d.id_cabecera
WHERE c.codigo_unico = '770999027699220260227RV63935321'
GROUP BY c.id_cabecera;

RESULT: 1 fila con resumen completo
```

### Ejemplo 2: Historial de Cambios (Versionado)
```sql
SELECT 
    c.version,
    c.hash_contenido,
    c.created_at,
    COUNT(d.id_detalle) as num_detalles,
    l.tipo_intento,
    l.fecha_intento
FROM reporte_ventas_cabecera c
LEFT JOIN reporte_ventas_detalle d ON c.id_cabecera = d.id_cabecera
LEFT JOIN reporte_ventas_log l ON c.codigo_unico = l.codigo_unico
WHERE c.codigo_unico = '770999027699220260227RV63935321'
ORDER BY c.version;

RESULT:
┌─────┬──────────────────┬─────────────────────┬──────────┬──────────────────┬─────────────────────┐
│ v1  │ a1b2c3d4e5f6...  │ 2026-03-03 10:00:00 │ 60       │ nueva_carga      │ 2026-03-03 10:00:00 │
│ v2  │ ZZZZZZZZZZZZZ... │ 2026-03-03 11:30:00 │ 62       │ nueva_carga      │ 2026-03-03 11:30:00 │
└─────┴──────────────────┴─────────────────────┴──────────┴──────────────────┴─────────────────────┘
```

### Ejemplo 3: Auditoría Completa
```sql
SELECT 
    l.id_log,
    l.codigo_unico,
    l.tipo_intento,
    l.descripcion,
    l.fecha_intento,
    COUNT(CASE WHEN l.tipo_intento = 'nueva_carga' THEN 1 END) OVER (PARTITION BY l.codigo_unico) as cargas_exitosas,
    COUNT(CASE WHEN l.tipo_intento = 'intento_duplicado' THEN 1 END) OVER (PARTITION BY l.codigo_unico) as duplicados_detectados
FROM reporte_ventas_log l
WHERE l.codigo_unico = '770999027699220260227RV63935321'
ORDER BY l.fecha_intento DESC;

RESULT: Timeline completo de intentos
```

### Ejemplo 4: Productos Top (Multi-tabla)
```sql
SELECT 
    d.item_ean,
    COUNT(DISTINCT d.id_cabecera) as nunca_en_reportes,
    COUNT(*) as veces_vendido,
    SUM(d.cantidad_vendida) as total_cantidad,
    SUM(d.precio_con_impuestos * d.cantidad_vendida) as total_ingresos,
    ROUND(AVG(d.precio_con_impuestos), 2) as precio_promedio
FROM reporte_ventas_detalle d
INNER JOIN reporte_ventas_cabecera c ON d.id_cabecera = c.id_cabecera
WHERE c.fecha_inicio_reporte >= '2026-02-01'
  AND c.fecha_inicio_reporte <= '2026-02-29'
GROUP BY d.item_ean
HAVING SUM(d.cantidad_vendida) > 5
ORDER BY total_ingresos DESC
LIMIT 20;

RESULT: Top 20 productos febrero con rentabilidad > 5 unidades
```

---

## 🎯 Performance Esperado con Índices

| Operación | Query Tipo | Tiempo Esperado | Índice |
|-----------|-----------|-----------------|--------|
| Obtener reporte por código | SELECT ... WHERE codigo_unico | 5 ms | idx_cabecera_codigo_unico |
| Resumen diario | SELECT ... WHERE fecha_reporte | 2 ms | idx_resumen_fecha |
| Detalles de reporte | SELECT ... WHERE id_cabecera | 8 ms | idx_detalle_cabecera |
| Productos top N | GROUP BY item_ean | 15 ms | idx_detalle_item_ean |
| Rango de fechas | SELECT ... WHERE fecha BETWEEN | 10 ms | idx_cabecera_fecha_inicio |
| Detectar duplicado | SELECT ... WHERE codigo + hash | 3 ms | UNIQUE constraints |
| Auditoría completa | SELECT ... FROM log WHERE tipo | 5 ms | idx_log_tipo_intento |

---

## ✅ Resumen de Relaciones

```
reporte_ventas_cabecera
    ↓ (1 cabecera a muchos detalles)
reporte_ventas_detalle

reporte_ventas_cabecera
    ↓ (1 cabecera a muchos logs)
reporte_ventas_log

reporte_ventas_detalle
    ↓ (muchos detalles agregan a resumen)
reporte_ventas_resumen_diario

ÍNDICES CLAVE:
- Cabecera: codigo_unico (UNIQUE), hash_contenido (UNIQUE), fecha_inicio
- Detalle: id_cabecera (FK), item_ean, pv_ean, fecha_inicial
- Log: codigo_unico, tipo_intento, fecha_intento
- Resumen: fecha_reporte (UNIQUE), año/mes
```
