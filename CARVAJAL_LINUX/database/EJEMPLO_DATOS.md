# 📊 EJEMPLO DE DATOS EN LA BASE DE DATOS

## Caso Práctico: Archivo VENTAS_PAGE1_FILA1_20260227_161509.xlsx

### 1️⃣ REGISTRO EN TABLA: reporte_ventas_cabecera

```sql
SELECT * FROM reporte_ventas_cabecera 
WHERE codigo_unico = '770999027699220260227RV63935321';
```

**Resultado:**
```
id_cabecera              : 1
codigo_unico            : 770999027699220260227RV63935321  [ÚNICO - Clave principal]
hash_contenido          : a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8... [UNIQUE - SHA256]
nombre_archivo          : VENTAS_PAGE1_FILA1_20260227_161509.xlsx
proveedor               : Dismel Ltda
entidad_vendedora       : SUPERTIENDAS Y DROGUERIAS OLIMPICAS S.A.
fecha_inicio_reporte    : 2026-02-26
fecha_fin_reporte       : 2026-02-26
fecha_generacion        : 2026-02-27 16:15:09.000
version                 : 1  [Si hay actualización, será v2]
estado                  : procesado
total_filas             : 60
created_at              : 2026-03-03 10:00:00.000
updated_at              : 2026-03-03 10:00:00.000
```

**Tamaño estimado**: ~200 bytes

---

### 2️⃣ REGISTROS EN TABLA: reporte_ventas_detalle (20 de 60)

```sql
SELECT * FROM reporte_ventas_detalle 
WHERE id_cabecera = 1 
LIMIT 5;
```

**Resultado de PRIMEROS 5 registros:**

| id_detalle | id_cabecera | pv_ean | pv_descripcion | pv_codigo_interno | fecha_inicial | fecha_final | item_ean | item_codigo_comprador | item_codigo_proveedor | item_descripcion | cantidad_vendida | unidad_medida | precio_con_impuestos | precio_sin_impuestos | columna_reservada_14 | numero_fila_origen | estado_validacion | fecha_registro |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 7701008002562 | SAO 256 AGUACHICA Cr 23 | SAO 256 AGUACHICA Cr 23 | 2026-02-26 | 2026-02-26 | 7708894411683 | NULL | NULL | NULL | 1.0 | NULL | 5294.0 | NULL | NULL | 10 | OK | 2026-03-03 10:00:01 |
| 2 | 1 | 7701008002562 | SAO 256 AGUACHICA Cr 23 | SAO 256 AGUACHICA Cr 23 | 2026-02-26 | 2026-02-26 | 7708894411348 | NULL | NULL | NULL | 2.0 | NULL | 5294.0 | NULL | NULL | 11 | OK | 2026-03-03 10:00:02 |
| 3 | 1 | 7701008001374 | STO 137 VILLACOLOMBIA | STO 137 VILLACOLOMBIA | 2026-02-26 | 2026-02-26 | 7708894411584 | NULL | NULL | NULL | 1.0 | NULL | 5294.0 | NULL | NULL | 12 | OK | 2026-03-03 10:00:03 |
| 4 | 1 | 7701008001220 | STO 122 CARMELO | STO 122 CARMELO | 2026-02-26 | 2026-02-26 | 7707180701125 | NULL | NULL | NULL | 1.0 | NULL | 43762.0 | NULL | NULL | 13 | OK | 2026-03-03 10:00:04 |
| 5 | 1 | 7701008000858 | STO 085 CALLE 85 | STO 085 CALLE 85 | 2026-02-26 | 2026-02-26 | 7708894411348 | NULL | NULL | NULL | 1.0 | NULL | 5294.0 | NULL | NULL | 14 | OK | 2026-03-03 10:00:05 |

**Total en tabla**: 60 registros (un por fila del Excel)

**Observaciones:**
- ✅ **Llenas**: pv_ean, pv_descripcion, pv_codigo_interno, fecha_inicial, fecha_final, item_ean, cantidad_vendida, precio_con_impuestos
- ❌ **Vacías**: item_codigo_comprador, item_codigo_proveedor, item_descripcion, unidad_medida, precio_sin_impuestos, columna_reservada_14
- **numero_fila_origen**: 10, 11, 12... (para auditoría, referencia a fila en Excel)

**Tamaño estimado por registro**: ~300 bytes × 60 = 18 KB

---

### 3️⃣ REGISTROS EN TABLA: reporte_ventas_log

```sql
SELECT * FROM reporte_ventas_log 
WHERE codigo_unico = '770999027699220260227RV63935321';
```

**Resultado:**
```
id_log | codigo_unico | hash_contenido | nombre_archivo | tipo_intento | descripcion | fecha_intento
-------|--------------|--|--|--|--|--
1 | 770999027699220260227RV63935321 | a1b2c3d4... | VENTAS_PAGE1_FILA1_20260227_161509.xlsx | nueva_carga | Reporte procesado exitosamente. Total: 60 filas | 2026-03-03 10:00:00
```

**Posibles tipos de intento:**
- `nueva_carga`: Primera vez que se procesa este código_único
- `intento_duplicado`: Se intentó cargar un archivo con mismo código_único + hash (rechazado)
- `error`: Falló la validación o el procesamiento

---

### 4️⃣ REGISTRO EN TABLA: reporte_ventas_resumen_diario

```sql
SELECT * FROM reporte_ventas_resumen_diario 
WHERE fecha_reporte = '2026-02-26';
```

**Resultado (después de procesar 1 reporte del día 26-02-2026):**
```
id_resumen             : 1
fecha_reporte          : 2026-02-26  [UNIQUE - Una entrada por día]
año                    : 2026
mes                    : 2
dia                    : 26

total_puntos_venta     : 8  [COUNT(DISTINCT pv_ean)]
total_items_vendidos   : 15  [COUNT(DISTINCT item_ean)]
total_cantidad_vendida : 75  [SUM(cantidad_vendida)]
total_ventas_con_impuestos  : 450,000  [SUM(precio * cantidad)]
total_ventas_sin_impuestos  : NULL
cantidad_reportes      : 1  [COUNT(DISTINCT codigo_reporte)]

fecha_actualizacion    : 2026-03-03 10:00:05.000
```

**Nota:** Si llega un nuevo reporte ese mismo día (26-02-2026), NO se inserta nuevo registro. Solo se UPDATE el existente.

---

## 🔄 FLUJO DE DATOS COMPLETO

```
USUARIO descarga Excel
        ↓
ARCHIVO: VENTAS_PAGE1_FILA1_20260227_161509.xlsx
        ↓
PARSER:
├─ Extrae código_unico: 770999027699220260227RV63935321
├─ Calcula hash_contenido: a1b2c3d4e5f6...
├─ Lee metadatos (Fila 1-5)
├─ Lee detalles (Fila 10-69): 60 registros con 14 columnas c/u
└─ Prepara JSON
        ↓
VALIDADOR:
├─ Cabecera: ✓ OK
├─ 60 detalles: ✓ 60 OK
└─ Total validación: 100%
        ↓
DUPLICATE DETECTOR:
├─ ¿Existe (codigo_unico + hash)?
│  ├─ SÍ → DUPLICADO (salir)
│  └─ NO → Continuar
└─ ¿Existe código con DIFERENTE hash?
   ├─ SÍ → NUEVA VERSIÓN (v2)
   └─ NO → NUEVA CARGA
        ↓
BASE DE DATOS:
├─ INSERT reporte_ventas_cabecera (1 registro)
├─ INSERT reporte_ventas_detalle (60 registros)
├─ INSERT reporte_ventas_log (1 registro de auditoría)
├─ UPDATE reporte_ventas_resumen_diario (agregados del día)
└─ COMMIT
        ↓
API RETORNA:
{
  "success": true,
  "codigo_reporte": "770999027699220260227RV63935321",
  "total_filas_procesadas": 60,
  "timestamp": "2026-03-03T10:00:05"
}
```

---

## 📊 CONSULTAS TÍPICAS (Ejemplos SQL)

### Consulta 1: Obtener reporte completo
```sql
SELECT c.*, d.*
FROM reporte_ventas_cabecera c
LEFT JOIN reporte_ventas_detalle d ON c.id_cabecera = d.id_cabecera
WHERE c.codigo_unico = '770999027699220260227RV63935321';
```
**Resultado**: 1 cabecera + 60 detalles = 61 filas

---

### Consulta 2: Ventas por punto de venta
```sql
SELECT 
    pv_ean,
    pv_descripcion,
    COUNT(*) as items_vendidos,
    SUM(cantidad_vendida) as total_cantidad,
    SUM(precio_con_impuestos * cantidad_vendida) as total_ventas
FROM reporte_ventas_detalle
WHERE id_cabecera = 1
GROUP BY pv_ean
ORDER BY total_ventas DESC;
```
**Resultado**: 8 puntos de venta con sus totales

---

### Consulta 3: Productos más vendidos
```sql
SELECT 
    item_ean,
    COUNT(*) as veces_vendido,
    SUM(cantidad_vendida) as total_cantidad
FROM reporte_ventas_detalle
WHERE id_cabecera = 1
GROUP BY item_ean
ORDER BY total_cantidad DESC
LIMIT 10;
```
**Resultado**: Top 10 productos

---

### Consulta 4: Resumen del día (MÁS RÁPIDA)
```sql
SELECT 
    fecha_reporte,
    total_puntos_venta,
    total_items_vendidos,
    total_cantidad_vendida,
    total_ventas_con_impuestos
FROM reporte_ventas_resumen_diario
WHERE fecha_reporte = '2026-02-26';
```
**Resultado**: 1 fila (caché pre-calculado)

---

### Consulta 5: Auditoría - Intentos de duplicados
```sql
SELECT 
    codigo_unico,
    tipo_intento,
    COUNT(*) as intentos,
    MAX(fecha_intento) as ultimo_intento
FROM reporte_ventas_log
GROUP BY codigo_unico, tipo_intento;
```
**Resultado**: Historial de intentos

---

## 📈 ESTADÍSTICAS DE BD

| Elemento | Cantidad | Tamaño |
|----------|----------|--------|
| Registros cabecera/día | ~1-5 | 200 B × 5 = 1 KB |
| Registros detalle/día | ~50-100 | 300 B × 100 = 30 KB |
| Registros log/día | ~2-10 | 150 B × 10 = 1.5 KB |
| Registros resumen/día | 1 | 500 B |
| **Total/día** | - | **~32.5 KB** |
| **Total/mes (30 días)** | - | **~975 KB (~1 MB)** |
| **Total/año** | - | **~12 MB** |

**Conclusión**: BD muy ligera. Ideal para SQLite. Sin problemas de escalabilidad.

---

## 🔐 ÍNDICES Y PERFORMANCE

### Índices Creados:
```
Tabla CABECERA (8 índices):
- idx_cabecera_codigo_unico     → O(log N) para búsquedas por código
- idx_cabecera_fecha_inicio     → O(log N) para rangos de fecha
- idx_cabecera_hash             → O(log N) para detectar duplicados
- idx_cabecera_estado           → O(log N) para filtrar por estado
- idx_cabecera_created          → O(log N) para ordenar por fecha

Tabla DETALLE (5 índices):
- idx_detalle_cabecera          → O(log N) para JOINs
- idx_detalle_item_ean          → O(log N) para búsquedas por producto
- idx_detalle_pv_ean            → O(log N) para análisis por punto venta
- idx_detalle_fecha_inicial     → O(log N) para rangos de fecha
- idx_detalle_cantidad          → O(log N) para top N

Total: 13 índices optimizados
```

### Queries esperadas (con índices):
- Obtener reporte por código: **~5 ms**
- Resumen diario: **~2 ms**
- Productos top 10: **~10 ms**
- Detectar duplicado: **~3 ms**

---

## ✅ CARACTERÍSTICAS CLAVE

1. **Fidelidad Excel**: 14 columnas exactas preservadas
2. **Duplicados**: Detectados por código_único + hash_contenido
3. **Auditoria**: Log completo de intentos
4. **Performance**: Resumen_diario caché para Odoo
5. **Versionado**: Mantiene historial si hay actualizaciones
6. **Escalabilidad**: Fácil migrar a PostgreSQL
7. **Índices**: Optimizados para queries comunes
