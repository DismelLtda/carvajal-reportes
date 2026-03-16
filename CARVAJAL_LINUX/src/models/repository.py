"""
📂 REPOSITORIO DE PERSISTENCIA
Maneja la inserción de datos parseados en la base de datos
Centraliza la lógica de guardado para VENTAS e INVENTARIO
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from .schema import (
    ReporteLog, 
    ReporteVentasCabecera, ReporteVentasDetalle, ReporteVentasResumenDiario,
    ReporteInventarioCabecera, ReporteInventarioDetalle, ReporteInventarioResumenDiario
)

logger = logging.getLogger(__name__)

class ReportRepository:
    """
    Clase para manejar la persistencia de reportes en la BD
    """

    @staticmethod
    def guardar_reporte_ventas(db: Session, resultado: dict) -> bool:
        """
        Guarda un reporte de ventas procesado en la BD
        """
        try:
            metadata = resultado['metadata']
            codigo_unico = f"VNT-{metadata.hash_contenido[:12]}"
            
            # Verificar si ya existe para evitar errores de duplicidad
            existente = db.query(ReporteVentasCabecera).filter_by(codigo_unico=codigo_unico).first()
            if existente:
                logger.warning(f"⚠️  Reporte VENTAS ya existe en BD: {metadata.archivo}")
                return True # Retornamos True para que el scheduler lo mueva a procesados

            # 1. Crear cabecera
            fecha_final_reporte = metadata.fecha_reporte.date() if metadata.fecha_reporte else metadata.fecha_descarga.date()
            
            cabecera = ReporteVentasCabecera(
                codigo_unico=codigo_unico,
                id_informe=metadata.id_informe,
                hash_contenido=metadata.hash_contenido,
                archivo=metadata.archivo,
                proveedor=metadata.proveedor_emisor,
                entidad_vendedora=metadata.entidad_receptor,
                fecha_descarga=metadata.fecha_descarga,
                fecha_reporte=fecha_final_reporte,
                tamaño_bytes=metadata.tamaño_bytes,
                numero_filas=resultado['resumen']['total_filas'],
                numero_columnas=metadata.numero_columnas,
                total_cantidad=resultado['resumen']['total_cantidad'],
                total_dinero=resultado['resumen']['total_dinero']
            )
            
            db.add(cabecera)
            db.flush() # Para obtener el ID de cabecera

            # 2. Crear detalles
            for fila in resultado['detalles']:
                datos = fila.datos
                detalle = ReporteVentasDetalle(
                    cabecera_id=cabecera.id,
                    numero_fila_excel=fila.numero_fila,
                    punto_venta_ean=datos.get('EAN', ''),
                    punto_venta_nombre=datos.get('Descripción', ''),
                    codigo_almacen=datos.get('Código interno Almacen', ''),
                    fecha_inicial=datetime.strptime(datos.get('Fecha Inicial', ''), '%d-%m-%Y').date() if datos.get('Fecha Inicial') else fecha_final_reporte,
                    fecha_final=datetime.strptime(datos.get('Fecha Final', ''), '%d-%m-%Y').date() if datos.get('Fecha Final') else fecha_final_reporte,
                    item_ean=datos.get('Código EAN del item', 'N/A'),
                    item_codigo_comprador=datos.get('Código de Ítem / Com', ''),
                    item_codigo_proveedor=datos.get('Código de Ítem / Pro', ''),
                    item_descripcion=datos.get('Descripción del Ítem', ''),
                    cantidad_vendida=float(datos.get('Cantidad Vendida', 0) or 0),
                    unidad_medida=datos.get('Unidad de Medida', ''),
                    precio_neto=float(datos.get('Precio neto al consu', 0) or 0),
                    total_neto=float(datos.get('Precio neto al consu_1', 0) or 0),
                    precio_sin_impuestos=float(datos.get('Precio neto al consumido sin impuestos', 0) or 0)
                )
                db.add(detalle)

            # 3. Actualizar Resumen Diario (Incremental)
            resumen = db.query(ReporteVentasResumenDiario).filter_by(fecha_resumen=fecha_final_reporte).first()
            
            if not resumen:
                resumen = ReporteVentasResumenDiario(
                    fecha_resumen=fecha_final_reporte,
                    total_cantidad_acumulada=0.0,
                    total_dinero_acumulado=0.0,
                    total_descuentos_acumulados=0.0,
                    cantidad_transacciones=0,
                    cantidad_reportes_procesados=0
                )
                db.add(resumen)
            
            # Asegurar que no sean None antes de sumar
            resumen.total_cantidad_acumulada = (resumen.total_cantidad_acumulada or 0.0) + resultado['resumen']['total_cantidad']
            resumen.total_dinero_acumulado = (resumen.total_dinero_acumulado or 0.0) + resultado['resumen']['total_dinero']
            resumen.cantidad_transacciones = (resumen.cantidad_transacciones or 0) + resultado['resumen']['total_filas']
            resumen.cantidad_reportes_procesados = (resumen.cantidad_reportes_procesados or 0) + 1

            # 4. Registrar en Log
            log = ReporteLog(
                tipo_reporte='VENTAS',
                archivo=metadata.archivo,
                tipo_intento='EXITOSO',
                mensaje=f"Procesado exitosamente: {resultado['resumen']['total_filas']} filas",
                hash_contenido=metadata.hash_contenido,
                tamaño_bytes=metadata.tamaño_bytes
            )
            db.add(log)

            db.commit()
            logger.info(f"✅ Reporte VENTAS guardado en BD: {metadata.archivo}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error guardando VENTAS en BD: {str(e)}")
            return False

    @staticmethod
    def guardar_reporte_inventario(db: Session, resultado: dict) -> bool:
        """
        Guarda un reporte de inventario procesado en la BD
        """
        try:
            metadata = resultado['metadata']
            codigo_unico = f"INV-{metadata.hash_contenido[:12]}"

            # Verificar si ya existe
            existente = db.query(ReporteInventarioCabecera).filter_by(codigo_unico=codigo_unico).first()
            if existente:
                logger.warning(f"⚠️  Reporte INVENTARIO ya existe en BD: {metadata.archivo}")
                return True # Retornamos True para que el scheduler lo mueva a procesados

            # 1. Crear cabecera
            fecha_final_reporte = metadata.fecha_reporte.date() if metadata.fecha_reporte else metadata.fecha_descarga.date()
            
            cabecera = ReporteInventarioCabecera(
                codigo_unico=codigo_unico,
                id_informe=metadata.id_informe,
                hash_contenido=metadata.hash_contenido,
                archivo=metadata.archivo,
                emisor=metadata.proveedor_emisor,
                receptor=metadata.entidad_receptor,
                fecha_descarga=metadata.fecha_descarga,
                fecha_reporte=fecha_final_reporte,
                tamaño_bytes=metadata.tamaño_bytes,
                numero_filas=resultado['resumen']['total_filas'],
                numero_columnas=metadata.numero_columnas,
                total_items_unicos=resultado['resumen']['total_items_unicos'],
                total_lugares_unicos=resultado['resumen']['total_lugares_unicos'],
                cantidad_total_fisica=resultado['resumen']['cantidad_total_fisica'],
                cantidad_total_sistema=resultado['resumen']['cantidad_total_sistema'],
                cantidad_diferencias=resultado['resumen']['items_con_diferencia']
            )
            
            db.add(cabecera)
            db.flush()

            # 2. Crear detalles e insertar/actualizar snapshot diario
            for fila in resultado['detalles']:
                datos = fila.datos
                detalle = ReporteInventarioDetalle(
                    cabecera_id=cabecera.id,
                    numero_fila_excel=fila.numero_fila,
                    item_ean=datos.get('Código de Producto / Ean', ''),
                    item_descripcion=datos.get('Descripción de Producto', ''),
                    codigo_almacen=datos.get('Código interno Almacen', ''),
                    cantidad=float(datos.get('Cantidad', 0) or 0),
                    codigo_lugar=datos.get('Código Lugar', ''),
                    nombre_lugar=datos.get('Nombre Lugar', ''),
                    item_codigo_comprador=datos.get('Código de item / Comprador', ''),
                    precio_lista=float(datos.get('Precio Lista', 0) or 0),
                    precio_neto=float(datos.get('Precio Neto', 0) or 0),
                    total_neto=float(datos.get('Precio Neto_1', 0) or 0),
                    fecha_inventario=fecha_final_reporte
                )
                db.add(detalle)

                # Actualizar snapshot diario (reemplaza si ya existe para ese día-ean-lugar)
                ean = datos.get('Código de Producto / Ean', '')
                lugar = datos.get('Código interno Almacen', '')
                
                snapshot = db.query(ReporteInventarioResumenDiario).filter_by(
                    fecha_inventario=fecha_final_reporte,
                    item_ean=ean,
                    codigo_lugar=lugar
                ).first()
                
                if not snapshot:
                    snapshot = ReporteInventarioResumenDiario(
                        fecha_inventario=fecha_final_reporte,
                        item_ean=ean,
                        codigo_lugar=lugar
                    )
                    db.add(snapshot)
                
                snapshot.descripcion = datos.get('Descripción de Producto', '')
                snapshot.descripcion_lugar = datos.get('Nombre Lugar', '')
                snapshot.cantidad_fisica = float(datos.get('Cantidad', 0) or 0)
                snapshot.cantidad_sistema = float(datos.get('Precio Neto', 0) or 0) # Usar un campo disponible o 0
                snapshot.diferencia = 0

            # 3. Registrar en Log
            log = ReporteLog(
                tipo_reporte='INVENTARIO',
                archivo=metadata.archivo,
                tipo_intento='EXITOSO',
                mensaje=f"Procesado exitosamente: {resultado['resumen']['total_filas']} filas",
                hash_contenido=metadata.hash_contenido,
                tamaño_bytes=metadata.tamaño_bytes
            )
            db.add(log)

            db.commit()
            logger.info(f"✅ Reporte INVENTARIO guardado en BD: {metadata.archivo}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error guardando INVENTARIO en BD: {str(e)}")
            return False

    @staticmethod
    def registrar_error(db: Session, tipo: str, archivo: str, mensaje: str):
        """Registra un intento fallido en el log"""
        try:
            log = ReporteLog(
                tipo_reporte=tipo,
                archivo=archivo,
                tipo_intento='ERROR',
                mensaje=mensaje,
                fecha_procesamiento=datetime.now()
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.error(f"Error registrando error en log: {e}")
