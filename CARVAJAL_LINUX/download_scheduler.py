#!/usr/bin/env python3
# ============================================================================
# CARVAJAL VENTAS - Scheduler de Procesamiento en Docker
# ============================================================================
# Este script corre en Docker
# Propósito: Verifica periódicamente si hay nuevos archivos y los procesa
# automáticamente (detecta tipo, parsea, almacena en BD)
#
# Se ejecuta continuamente: cada INTERVALO_MINUTOS verifica
# ============================================================================

import os
import logging
import sys
import shutil
from pathlib import Path
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import time

# Agregar src al path
sys.path.insert(0, '/app')

from src.processor.detector import ReporteDetector, TipoReporte
from src.processor import ExcelParserVentas, ExcelParserInventario
from src.config import (
    DESCARGAS_VENTAS_DIR, DESCARGAS_INVENTARIO_DIR, LOGS_DIR,
    PROCESADOS_VENTAS_DIR, PROCESADOS_INVENTARIO_DIR
)
from src.models.database import SessionLocal
from src.models.repository import ReportRepository
from src.notificaciones import enviar_notificacion_error, enviar_notificacion_exito

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Intervalo de verificación (en minutos)
INTERVALO_MINUTOS = int(os.getenv('INTERVALO_VERIFICACION', 10))

# Crear directorio de logs si no existe
Path(LOGS_DIR).mkdir(exist_ok=True)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(LOGS_DIR, 'scheduler.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# VARIABLES GLOBALES
# ============================================================================

archivos_procesados = set()  # Para evitar procesar el mismo archivo 2 veces
scheduler = None

# ============================================================================
# FUNCIONES
# ============================================================================

def obtener_archivos_pendientes(directorio):
    """Obtiene lista de archivos .xlsx en un directorio, ignorando subcarpetas de procesados"""
    try:
        logger.debug(f"Buscando en: {directorio}")
        archivos = []
        
        if not os.path.exists(directorio):
            return archivos

        for archivo in Path(directorio).rglob('*.xlsx'):
            nombre = archivo.name
            
            # Ignorar archivos temporales de Excel (empiezan con ~$)
            if nombre.startswith('~$'):
                continue
                
            # Ignorar si ya fue procesado en esta sesión
            if str(archivo) in archivos_procesados:
                continue
            
            # Ignorar si está en carpeta "procesados"
            if 'procesado' in nombre.lower():
                continue
            
            archivos.append(archivo)
        
        return archivos

    except Exception as e:
        logger.error(f"Error listando archivos: {str(e)}")
        return []


def procesar_archivo(ruta_archivo):
    """Procesa un archivo (detecta tipo, parsea, almacena y mueve)"""
    db = SessionLocal()
    try:
        logger.info(f"🔄 Procesando: {ruta_archivo.name}")
        
        # 1. Detectar tipo
        detector = ReporteDetector()
        tipo_reporte, metadata = detector.validar_deteccion(ruta_archivo)
        
        if tipo_reporte == TipoReporte.DESCONOCIDO:
            error_msg = f"No se pudo detectar tipo para: {ruta_archivo.name}"
            logger.error(f"❌ {error_msg}")
            ReportRepository.registrar_error(db, "DESCONOCIDO", ruta_archivo.name, error_msg)
            return False
        
        logger.info(f"✅ Detectado como: {tipo_reporte.value}")
        
        # 2. Parsear según tipo
        resultado = None
        if tipo_reporte == TipoReporte.VENTAS:
            with ExcelParserVentas(ruta_archivo) as parser:
                resultado = parser.procesar()
        elif tipo_reporte == TipoReporte.INVENTARIO:
            with ExcelParserInventario(ruta_archivo) as parser:
                resultado = parser.procesar()
        
        if not resultado or not resultado.get('valido'):
            error_msg = f"Error en parsing: {resultado.get('errores', 'Error desconocido')}"
            logger.error(f"❌ {error_msg}")
            ReportRepository.registrar_error(db, tipo_reporte.value, ruta_archivo.name, error_msg)
            return False

        logger.info(f"✅ Reporte parseado con {resultado['resumen']['total_filas']} filas.")

        # 3. Guardar en BD
        exito_guardado = False
        if tipo_reporte == TipoReporte.VENTAS:
            exito_guardado = ReportRepository.guardar_reporte_ventas(db, resultado)
        else:
            exito_guardado = ReportRepository.guardar_reporte_inventario(db, resultado)

        if not exito_guardado:
            return False

        # 4. Mover a carpeta de procesados
        try:
            directorio_destino = PROCESADOS_VENTAS_DIR if tipo_reporte == TipoReporte.VENTAS else PROCESADOS_INVENTARIO_DIR
            directorio_destino.mkdir(parents=True, exist_ok=True)
            
            # Nombre con timestamp para evitar colisiones si el archivo se repite
            nuevo_nombre = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ruta_archivo.name}"
            ruta_destino = directorio_destino / nuevo_nombre
            
            shutil.move(str(ruta_archivo), str(ruta_destino))
            logger.info(f"📁 Archivo movido a: {ruta_destino.name}")
        except Exception as e_move:
            logger.warning(f"⚠️  No se pudo mover el archivo (pero se guardó en BD): {e_move}")

        # Registrar en memoria para el ciclo actual
        archivos_procesados.add(str(ruta_archivo))
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error crítico procesando {ruta_archivo.name}: {str(e)}", exc_info=True)
        return False
    finally:
        db.close()


def tarea_verificar_y_procesar():
    """Tarea que se ejecuta cada intervalo: verifica y procesa nuevos archivos"""
    
    try:
        logger.info("="*70)
        logger.info(f"VERIFICACIÓN {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        logger.info("="*70)
        
        # Obtener archivos pendientes
        archivos_ventas = obtener_archivos_pendientes(DESCARGAS_VENTAS_DIR)
        archivos_inventario = obtener_archivos_pendientes(DESCARGAS_INVENTARIO_DIR)
        
        # Combinar listas eliminando duplicados por ruta absoluta (en caso de que las carpetas sean la misma)
        mapa_archivos = {str(a): a for a in (archivos_ventas + archivos_inventario)}
        archivos_unicos = list(mapa_archivos.values())
        
        if not archivos_unicos:
            logger.info("✓ Sin archivos nuevos para procesar")
            return
        
        if DESCARGAS_VENTAS_DIR != DESCARGAS_INVENTARIO_DIR:
            logger.info(f"📁 Archivos VENTAS: {len(archivos_ventas)}")
            logger.info(f"📁 Archivos INVENTARIO: {len(archivos_inventario)}")
        else:
            logger.info(f"📁 Archivos detectados: {len(archivos_unicos)}")
        
        # Procesar
        contador_exito = 0
        contador_error = 0
        
        for archivo in archivos_unicos:
            if procesar_archivo(archivo):
                contador_exito += 1
            else:
                contador_error += 1
        
        logger.info("="*70)
        logger.info(f"RESULTADOS:")
        logger.info(f"  ✅ Procesados: {contador_exito}")
        logger.info(f"  ❌ Errores: {contador_error}")
        logger.info("="*70)
        
        # Notificar si hay éxitos
        if contador_exito > 0:
            try:
                enviar_notificacion_exito(
                    cantidad_descargas=contador_exito,
                    ruta_reportes='/app/data/',
                    ruta_logs=LOGS_DIR
                )
            except Exception as e:
                logger.warning(f"⚠️  No se pudo enviar notificación: {str(e)}")
        
        # Notificar si hay errores
        if contador_error > 0:
            try:
                enviar_notificacion_error(
                    titulo_error=f"Errores en procesamiento de reportes",
                    descripcion_error=f"Se encontraron {contador_error} errores al procesar reportes",
                    tipo_error="PROCESAMIENTO",
                    paso_fallido=f"Procesamiento de {contador_error} archivo(s)",
                    detalles_tecnicos=f"Ver logs en {LOGS_DIR}/scheduler.log"
                )
            except Exception as e:
                logger.warning(f"⚠️  No se pudo enviar notificación de error: {str(e)}")
        
    except Exception as e:
        logger.error(f"❌ Error en tarea de verificación: {str(e)}", exc_info=True)


def iniciar_scheduler():
    """Inicia el scheduler de APScheduler"""
    
    global scheduler
    
    logger.info("="*70)
    logger.info("INICIANDO SCHEDULER DE PROCESAMIENTO")
    logger.info("="*70)
    
    scheduler = BackgroundScheduler()
    
    # Agregar tarea que se repite cada INTERVALO_MINUTOS
    scheduler.add_job(
        tarea_verificar_y_procesar,
        trigger=IntervalTrigger(minutes=INTERVALO_MINUTOS),
        id='verificar_procesar',
        name='Verifica y procesa nuevos reportes',
        replace_existing=True
    )
    
    scheduler.start()
    
    logger.info(f"📅 Scheduler iniciado")
    logger.info(f"⏱️  Verifica cada {INTERVALO_MINUTOS} minuto(s)")
    logger.info(f"📁 Carpeta VENTAS: {DESCARGAS_VENTAS_DIR}")
    logger.info(f"📁 Carpeta INVENTARIO: {DESCARGAS_INVENTARIO_DIR}")
    logger.info("="*70)
    
    return scheduler


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal - mantiene scheduler corriendo"""
    
    logger.info("\n" + "="*70)
    logger.info("🚀 CARVAJAL VENTAS - SCHEDULER DE PROCESAMIENTO")
    logger.info("="*70)
    logger.info(f"Inicio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info(f"Intervalo: {INTERVALO_MINUTOS} minuto(s)")
    logger.info("="*70 + "\n")
    
    try:
        # Ejecutar primera verificación inmediatamente
        logger.info("🔍 Ejecutando verificación inicial...")
        tarea_verificar_y_procesar()
        
        # Iniciar scheduler
        iniciar_scheduler()
        
        # Mantener el proceso corriendo
        logger.info("\n✅ Scheduler corriendo. Presiona Ctrl+C para salir.\n")
        
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\n⏹️  Scheduler detenido por usuario")
        if scheduler:
            scheduler.shutdown()
        sys.exit(0)
    
    except Exception as e:
        logger.critical(f"❌ Error crítico: {str(e)}", exc_info=True)
        logger.error("El scheduler ha sido detenido por error")
        sys.exit(1)


if __name__ == "__main__":
    main()
