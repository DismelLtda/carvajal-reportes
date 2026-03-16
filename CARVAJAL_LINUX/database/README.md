# 📚 ÍNDICE - DOCUMENTACIÓN DE BASE DE DATOS (v1.2.0)

## Estructura Actualizada (PostgreSQL 15)

El sistema ha evolucionado de SQLite a una arquitectura robusta en PostgreSQL con nombres de campos abreviados y seguimiento por ID de Informe.

### 1. 📋 Esquema y Modelos (`src/models/schema.py`)
**Descripción**: Los modelos SQLAlchemy definen la estructura de 7 tablas optimizadas.
**Cambios Clave v1.2.0**:
- **`id_informe`**: Campo crítico extraído de la celda A1 del Excel. Permite agrupar todos los registros de un mismo reporte generado por el portal.
- **Nombres Abreviados**: Campos como `Código de Producto / Ean` ahora son `item_ean`.
- **Relaciones**: Cabecera (1) -> Detalle (N).

---

### 2. 📊 Mapeo de Columnas Reales

#### Tabla: `reporte_ventas_detalle`
| Columna Original Excel | Campo en BD/API |
| :--- | :--- |
| EAN | `punto_venta_ean` |
| Descripción | `punto_venta_nombre` |
| Código interno Almacen | `codigo_almacen` |
| Fecha Inicial | `fecha_inicial` |
| Código EAN del item | `item_ean` |
| Cantidad Vendida | `cantidad_vendida` |
| Precio neto al consu | `precio_neto` |
| Precio neto al consu_1 | `total_neto` |
| Precio neto al consumido sin impuestos | `precio_sin_impuestos` |

#### Tabla: `reporte_inventario_detalle`
| Columna Original Excel | Campo en BD/API |
| :--- | :--- |
| Código de Producto / Ean | `item_ean` |
| Descripción de Producto | `item_descripcion` |
| Código interno Almacen | `codigo_almacen` |
| Cantidad | `cantidad` |
| Código Lugar | `codigo_lugar` |
| Nombre Lugar | `nombre_lugar` |

---

### 3. 🔗 Identificación y Deduplicación
Para asegurar la integridad de los líderes técnicos, el sistema utiliza 3 niveles de validación:
1. **`hash_contenido`**: SHA256 del archivo físico. Si el archivo es idéntico, se ignora.
2. **`id_informe`**: El número consecutivo del portal Carvajal.
3. **`codigo_unico`**: Combinación de Tipo + Hash para búsquedas rápidas.

---

### 4. ⚡ Consultas de Ejemplo (SQL)

```sql
-- Obtener todo el inventario de un informe específico
SELECT * FROM reporte_inventario_detalle d
JOIN reporte_inventario_cabecera c ON d.cabecera_id = c.id
WHERE c.id_informe = '80008987202026030616231';

-- Ver resumen de ventas por día
SELECT fecha_resumen, total_cantidad_acumulada, total_dinero_acumulado 
FROM reporte_ventas_resumen_diario
ORDER BY fecha_resumen DESC;
```

---

## 🛠️ Mantenimiento de Datos

### Reset de Tablas
Si se requiere limpiar la base de datos manteniendo el esquema:
```bash
docker exec -it carvajal_postgres psql -U carvajal_user -d carvajal_reportes -c "TRUNCATE reporte_ventas_cabecera, reporte_inventario_cabecera RESTART IDENTITY CASCADE;"
```

---
**Última actualización**: 2026-03-10  
**Versión**: 1.2.0 (PostgreSQL)

1. **Ejecutar schema.sql** en tu BD local (SQLite)
   ```bash
   sqlite3 reportes_ventas.db < schema.sql
   ```

2. **Verificar tablas se crearon**
   ```sql
   SELECT name FROM sqlite_master WHERE type='table';
   ```

3. **Ver datos de ejemplo**
   ```sql
   SELECT * FROM reporte_ventas_cabecera;
   SELECT * FROM reporte_ventas_detalle LIMIT 5;
   ```

4. **Pasar a siguiente fase**: Crear procesador Excel

---

## 📞 PREGUNTAS?

```
¿No entiendo la arquitectura?
→ Leer CHEAT_SHEET.md + RELACIONES_BD.md

¿Necesito implementar queries?
→ Usar ejemplos en EJEMPLO_DATOS.md

¿No sé si algo es correcto?
→ Verificar en schema.sql (fuente de verdad)

¿Necesito referencia rápida?
→ Guardar CHEAT_SHEET.md en favoritos
```

---

## 📊 ESTADÍSTICAS

| Métrica | Valor |
|---------|-------|
| Tablas | 4 |
| Columnas totales | 65 (con auditoría) |
| Índices | 13 |
| Vistas | 3 |
| Restricciones UNIQUE | 2 (codigo_unico, hash_contenido) |
| Restricciones FK | 1 (cascade delete) |
| Tamaño BD/día | ~32.5 KB |
| Tamaño BD/mes | ~1 MB |
| Tamaño BD/año | ~12 MB |

---

## 🎓 APRENDIZAJE

Después de leer esta documentación, deberías entender:

✅ Las 4 tablas y su propósito  
✅ Cómo se relacionan entre sí  
✅ Cómo se detectan duplicados  
✅ Cómo se consultan los datos  
✅ Qué índices se necesitan y por qué  
✅ Performance esperado  
✅ Cómo mantener auditoría  
✅ Cómo manejar versionado  
✅ Cómo escalar a PostgreSQL  

---

**Última actualización**: 3 de marzo de 2026  
**Versión**: 1.0  
**Status**: ✅ Completo y listo para implementar

