# 🛍️ CARVAJAL VENTAS - Sistema de Procesamiento Automático de Reportes (v1.2.0)

Sistema integral para procesar automáticamente reportes de **VENTAS** e **INVENTARIO** desde archivos Excel, almacenarlos en base de datos PostgreSQL y exponerlos vía API REST para integración con **Odoo 14**.

## 📋 Características Actualizadas

- ✅ **Procesamiento automático**: Detección, parseo y carga continua cada 10 minutos.
- ✅ **Identificación Única (`id_informe`)**: Extracción automática del ID del reporte desde la celda **A1** de los Excel.
- ✅ **Detección inteligente**: Clasificación por nombre de archivo y contenido (encabezados).
- ✅ **Persistencia Robusta**: PostgreSQL 15 con validación de duplicidad mediante Hash SHA256 e ID de Informe.
- ✅ **API REST Avanzada**: Endpoints con filtros por fecha, ID de informe, tienda/proveedor y nombres de campos abreviados.
- ✅ **Arquitectura Docker**: Despliegue seguro en Rocky Linux con aislamiento de servicios.

## 🏗️ Arquitectura del Sistema

```
CARVAJAL_LINUX/
├── src/
│   ├── api/main.py                   # API FastAPI (Filtros y Abreviaciones)
│   ├── models/
│   │   ├── schema.py                 # Modelos SQLAlchemy (Campos Abreviados)
│   │   └── repository.py             # Lógica de Persistencia e Inserción
│   ├── processor/
│   │   ├── detector.py               # Detección (Ventas vs Inventario)
│   │   ├── base/excel_parser.py       # Extracción de Metadata (A1, F3, F4)
│   │   ├── ventas/excel_parser_ventas.py
│   │   └── inventario/excel_parser_inventario.py
├── download_scheduler.py             # Orquestador de procesamiento continuo
├── docker-compose.yml                # Definición de servicios (App, DB, Downloader)
├── Dockerfile                        # Imagen Python 3.11 optimizada
└── init-db.sql                       # Inicialización de esquema Postgres
```

## 📡 API Endpoints (v1.2.0)

### 🏥 Health & Docs
- `GET /health`: Estado de API y Base de Datos (Sin autenticación).
- `GET /docs`: Documentación interactiva Swagger UI.

### 🔐 Autenticación (JWT)
`POST /api/v1/auth/login`
- **Cuerpo (Form Data)**: `username`, `password`
- **Respuesta**: `{"access_token": "...", "token_type": "bearer"}`
- **Uso**: Incluir en encabezados como `Authorization: Bearer <token>`.

### 💰 VENTAS (Protegido)
`GET /api/v1/ventas/registros`
- **Filtros**: `fecha`, `id_informe`, `proveedor`
- **Campos**: `item_ean`, `item_descripcion`, `cantidad`, `precio_neto`, `total_neto`, `punto_venta`, `id_informe`.

### 📦 INVENTARIO (Registros Abreviados)
`GET /api/v1/inventario/registros`
- **Filtros**: `fecha`, `id_informe`, `tienda`
- **Campos**: `item_ean`, `item_descripcion`, `cantidad`, `codigo_lugar`, `nombre_lugar`, `precio_neto`, `id_informe`.

## 📊 Modelos de Datos Reales (Mapeo Carvajal)

### VENTAS (14 Columnas)
| Columna Excel | Campo API/BD |
| :--- | :--- |
| Celda A1 | `id_informe` |
| Código EAN del item | `item_ean` |
| Descripción del Ítem | `item_descripcion` |
| Cantidad Vendida | `cantidad` |
| Precio neto al consu | `precio_neto` |
| Precio neto al consu_1 | `total_neto` |
| Precio neto al consumido sin impuestos | `precio_sin_impuestos` |

### INVENTARIO (12 Columnas)
| Columna Excel | Campo API/BD |
| :--- | :--- |
| Celda A1 | `id_informe` |
| Código de Producto / Ean | `item_ean` |
| Descripción de Producto | `item_descripcion` |
| Cantidad | `cantidad` |
| Nombre Lugar | `nombre_lugar` |

## 🚀 Despliegue en Servidor Linux

1. **Subir archivos**: Copiar carpeta `CARVAJAL_LINUX` al servidor.
2. **Configurar `.env`**: Asegurar credenciales de Postgres.
3. **Iniciar**:
```bash
docker-compose up -d --build
```
4. **Logs**:
```bash
docker-compose logs -f downloader
```

## 🔧 Notas para Líderes Técnicos
- El sistema utiliza **SQLAlchemy 2.0** con el patrón Repository para desacoplar la lógica de negocio de la BD.
- La deduplicación es doble: por **Hash del archivo** y por **ID de Informe**, evitando procesar el mismo Excel dos veces.
- Los nombres de campos en la API fueron abreviados para facilitar el consumo desde Odoo (ej: `codigo_producto_ean` -> `item_ean`).

---
**Última actualización**: 2026-03-10  
**Versión**: 1.2.0 (Stable)  
**Soporte**: Equipo de Desarrollo CARVAJAL
