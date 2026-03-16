"""
🗄️ MODELOS SQLALCHEMY
Mapeo ORM de todas las tablas de la BD para VENTAS e INVENTARIO
Compatible con SQLite y PostgreSQL
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# ============================================================================
# MODELOS COMPARTIDOS (Ambos tipos de reporte)
# ============================================================================

class ReporteLog(Base):
    """Log de procesamiento de reportes (compartido para VENTAS e INVENTARIO)"""
    
    __tablename__ = 'reporte_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo_reporte = Column(String(20), nullable=False)  # 'VENTAS' o 'INVENTARIO'
    archivo = Column(String(255), nullable=False)
    fecha_procesamiento = Column(DateTime, nullable=False, default=datetime.now)
    tipo_intento = Column(String(50), nullable=False)  # 'EXITOSO', 'ERROR', 'DUPLICADO', etc.
    mensaje = Column(Text)
    hash_contenido = Column(String(64), unique=True)  # SHA256
    tamaño_bytes = Column(Integer)
    
    # Índices
    __table_args__ = (
        Index('idx_reporte_log_tipo_fecha', 'tipo_reporte', 'fecha_procesamiento'),
        Index('idx_reporte_log_hash', 'hash_contenido'),
    )


# ============================================================================
# MODELOS VENTAS (Transaccional)
# ============================================================================

class ReporteVentasCabecera(Base):
    """Cabecera de cada reporte de VENTAS procesado"""
    
    __tablename__ = 'reporte_ventas_cabecera'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identificación única
    codigo_unico = Column(String(64), unique=True, nullable=False)  # Generado por sistema
    id_informe = Column(String(100), index=True) # Extraído de A1
    hash_contenido = Column(String(64), unique=True, nullable=False)  # SHA256 del archivo
    
    # Metadatos del archivo
    archivo = Column(String(255), nullable=False)
    proveedor = Column(String(255)) # Extraído de Fila 3
    entidad_vendedora = Column(String(255)) # Extraído de Fila 4
    fecha_descarga = Column(DateTime, nullable=False, default=datetime.now)
    fecha_reporte = Column(Date)  # Fecha que reporta el archivo
    tamaño_bytes = Column(Integer)
    
    # Estadísticas
    numero_filas = Column(Integer)
    numero_columnas = Column(Integer)
    total_cantidad = Column(Float, default=0)
    total_dinero = Column(Float, default=0)
    total_descuentos = Column(Float, default=0)
    
    # Control de versiones
    version_procesador = Column(String(20), default='1.0')
    version_bd = Column(Integer, default=1)
    
    # Estado
    estado = Column(String(50), default='PROCESADO')  # PROCESADO, ERROR, DUPLICADO
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relación 1:N con detalles
    detalles = relationship('ReporteVentasDetalle', back_populates='cabecera', cascade='all, delete-orphan')
    
    # Índices
    __table_args__ = (
        Index('idx_ventas_cabecera_codigo_unico', 'codigo_unico'),
        Index('idx_ventas_cabecera_hash', 'hash_contenido'),
        Index('idx_ventas_cabecera_fecha', 'fecha_descarga'),
        Index('idx_ventas_cabecera_estado', 'estado'),
    )


class ReporteVentasDetalle(Base):
    """Detalle de cada venta en un reporte"""
    
    __tablename__ = 'reporte_ventas_detalle'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key
    cabecera_id = Column(Integer, ForeignKey('reporte_ventas_cabecera.id'), nullable=False)
    cabecera = relationship('ReporteVentasCabecera', back_populates='detalles')
    
    # Datos de la venta (Abreviados según requerimiento)
    numero_fila_excel = Column(Integer, nullable=False)
    punto_venta_ean = Column(String(64)) # Col 1: EAN
    punto_venta_nombre = Column(String(255)) # Col 2: Descripción
    codigo_almacen = Column(String(100)) # Col 3: Código interno Almacen
    fecha_inicial = Column(Date) # Col 4
    fecha_final = Column(Date) # Col 5
    item_ean = Column(String(64), nullable=False) # Col 6: Código EAN del item
    item_codigo_comprador = Column(String(64)) # Col 7: Código de Ítem / Com
    item_codigo_proveedor = Column(String(64)) # Col 8: Código de Ítem / Pro
    item_descripcion = Column(String(255)) # Col 9: Descripción del Ítem
    cantidad_vendida = Column(Float) # Col 10: Cantidad Vendida
    unidad_medida = Column(String(50)) # Col 11: Unidad de Medida
    precio_neto = Column(Float) # Col 12: Precio neto al consu
    total_neto = Column(Float) # Col 13: Precio neto al consu_1
    precio_sin_impuestos = Column(Float) # Col 14: Precio neto al consumido sin impuestos
    
    # Control
    fecha_procesamiento = Column(DateTime, default=datetime.now)
    
    # Índices
    __table_args__ = (
        Index('idx_ventas_detalle_cabecera', 'cabecera_id'),
        Index('idx_ventas_detalle_ean', 'item_ean'),
        Index('idx_ventas_detalle_fecha', 'fecha_inicial'),
    )


class ReporteVentasResumenDiario(Base):
    """
    Resumen incremental diario de VENTAS
    Agregación de ventas por día (suma acumulativa)
    """
    
    __tablename__ = 'reporte_ventas_resumen_diario'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identificación
    fecha_resumen = Column(Date, unique=True, nullable=False)
    
    # Agregaciones acumulativas (SUMAR de todos los detalles hasta fecha)
    total_cantidad_acumulada = Column(Float, default=0)
    total_dinero_acumulado = Column(Float, default=0)
    total_descuentos_acumulados = Column(Float, default=0)
    cantidad_transacciones = Column(Integer, default=0)
    cantidad_reportes_procesados = Column(Integer, default=0)
    
    # Estadísticas por medio
    transacciones_con_descuento = Column(Integer, default=0)
    transacciones_sin_descuento = Column(Integer, default=0)
    
    # Control
    fecha_calculo = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Índices
    __table_args__ = (
        Index('idx_ventas_resumen_fecha', 'fecha_resumen'),
    )


# ============================================================================
# MODELOS INVENTARIO (Snapshot)
# ============================================================================

class ReporteInventarioCabecera(Base):
    """Cabecera de cada reporte de INVENTARIO procesado"""
    
    __tablename__ = 'reporte_inventario_cabecera'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identificación única
    codigo_unico = Column(String(64), unique=True, nullable=False)
    id_informe = Column(String(100), index=True) # Extraído de A1
    hash_contenido = Column(String(64), unique=True, nullable=False)  # SHA256
    
    # Metadatos del archivo
    archivo = Column(String(255), nullable=False)
    emisor = Column(String(255)) # Extraído de Fila 3
    receptor = Column(String(255)) # Extraído de Fila 4
    fecha_descarga = Column(DateTime, nullable=False, default=datetime.now)
    fecha_reporte = Column(Date)  # Fecha que reporta el archivo
    tamaño_bytes = Column(Integer)
    
    # Estadísticas
    numero_filas = Column(Integer)
    numero_columnas = Column(Integer)
    total_items_unicos = Column(Integer)
    total_lugares_unicos = Column(Integer)
    cantidad_total_fisica = Column(Float, default=0)
    cantidad_total_sistema = Column(Float, default=0)
    cantidad_diferencias = Column(Integer, default=0)
    
    # Control de versiones
    version_procesador = Column(String(20), default='1.0')
    version_bd = Column(Integer, default=1)
    
    # Estado
    estado = Column(String(50), default='PROCESADO')
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relación 1:N con detalles
    detalles = relationship('ReporteInventarioDetalle', back_populates='cabecera', cascade='all, delete-orphan')
    
    # Índices
    __table_args__ = (
        Index('idx_inventario_cabecera_codigo_unico', 'codigo_unico'),
        Index('idx_inventario_cabecera_hash', 'hash_contenido'),
        Index('idx_inventario_cabecera_fecha', 'fecha_descarga'),
        Index('idx_inventario_cabecera_estado', 'estado'),
    )


class ReporteInventarioDetalle(Base):
    """Detalle de cada línea de stock en un reporte (snapshot)"""
    
    __tablename__ = 'reporte_inventario_detalle'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key
    cabecera_id = Column(Integer, ForeignKey('reporte_inventario_cabecera.id'), nullable=False)
    cabecera = relationship('ReporteInventarioCabecera', back_populates='detalles')
    
    # Datos del inventario (Abreviados según requerimiento)
    numero_fila_excel = Column(Integer, nullable=False)
    item_ean = Column(String(64), nullable=False) # Col 1: Código de Producto / Ean
    item_descripcion = Column(String(255)) # Col 2: Descripción de Producto
    codigo_almacen = Column(String(100)) # Col 4: Código interno Almacen
    cantidad = Column(Float) # Col 5: Cantidad
    codigo_lugar = Column(String(100), nullable=False) # Col 6: Código Lugar
    nombre_lugar = Column(String(255)) # Col 8: Nombre Lugar
    item_codigo_comprador = Column(String(64)) # Col 9: Código de item / Comprador
    precio_lista = Column(Float) # Col 10: Precio Lista
    precio_neto = Column(Float) # Col 11: Precio Neto
    total_neto = Column(Float) # Col 12: Precio Neto (duplicado)
    
    # Control
    fecha_procesamiento = Column(DateTime, default=datetime.now)
    fecha_inventario = Column(Date)
    
    # Índices
    __table_args__ = (
        Index('idx_inventario_detalle_cabecera', 'cabecera_id'),
        Index('idx_inventario_detalle_ean', 'item_ean'),
        Index('idx_inventario_detalle_lugar', 'codigo_lugar'),
    )


class ReporteInventarioResumenDiario(Base):
    """
    Resumen snap shot diario de INVENTARIO
    Reemplaza el anterior cada día (no es acumulativo, es snapshot)
    Agregación de stock actual por SKU y localización
    """
    
    __tablename__ = 'reporte_inventario_resumen_diario'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identificación (composición: fecha + ean + lugar)
    fecha_inventario = Column(Date, nullable=False)
    item_ean = Column(String(64), nullable=False)
    codigo_lugar = Column(String(100), nullable=False)
    
    # Única combinación por día
    __table_args__ = (
        UniqueConstraint('fecha_inventario', 'item_ean', 'codigo_lugar', name='uix_inventario_snapshot'),
        Index('idx_inventario_resumen_fecha', 'fecha_inventario'),
        Index('idx_inventario_resumen_ean', 'item_ean'),
        Index('idx_inventario_resumen_lugar', 'codigo_lugar'),
    )
    
    # Datos snapshot de  ese día-ean-lugar
    descripcion = Column(String(255))
    descripcion_lugar = Column(String(255))
    cantidad_fisica = Column(Float, default=0)
    cantidad_sistema = Column(Float, default=0)
    diferencia = Column(Float, default=0)
    
    # Control
    fecha_calculo = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ============================================================================
# INFORMACIÓN DEL ESQUEMA
# ============================================================================

MODELOS = [
    ReporteLog,
    ReporteVentasCabecera,
    ReporteVentasDetalle,
    ReporteVentasResumenDiario,
    ReporteInventarioCabecera,
    ReporteInventarioDetalle,
    ReporteInventarioResumenDiario,
]

MODELOS_NOMBRES = {
    'reporte_log': ReporteLog,
    'reporte_ventas_cabecera': ReporteVentasCabecera,
    'reporte_ventas_detalle': ReporteVentasDetalle,
    'reporte_ventas_resumen_diario': ReporteVentasResumenDiario,
    'reporte_inventario_cabecera': ReporteInventarioCabecera,
    'reporte_inventario_detalle': ReporteInventarioDetalle,
    'reporte_inventario_resumen_diario': ReporteInventarioResumenDiario,
}


# ============================================================================
# UTILIDADES
# ============================================================================

def crear_todas_tablas(engine):
    """Crea todas las tablas en la BD usando el engine SQLAlchemy"""
    Base.metadata.create_all(engine)
    print("✅ Todas las tablas creadas/verificadas en la BD")


def eliminar_todas_tablas(engine):
    """Elimina todas las tablas (¡CUIDADO!)"""
    Base.metadata.drop_all(engine)
    print("⚠️  Todas las tablas eliminadas")


if __name__ == '__main__':
    print("Módulo de modelos SQLAlchemy")
    print(f"Modelos definidos: {len(MODELOS)}")
    for modelo in MODELOS:
        print(f"  - {modelo.__tablename__}")
