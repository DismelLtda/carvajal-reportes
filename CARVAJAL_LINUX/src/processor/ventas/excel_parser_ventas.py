"""
💰 PARSER DE REPORTES VENTAS
Extrae datos de reportes de ventas (60-100 filas, 14 columnas)
Estructura: Metadata (filas 1-8) + Cabecera (fila 9) + Datos (filas 10+)
"""

from pathlib import Path
from typing import List, Dict, Any
from ..base.excel_parser import ExcelParserBase, FilaDetalle
import logging

logger = logging.getLogger(__name__)


class ExcelParserVentas(ExcelParserBase):
    """
    Parser especializado para reportes de VENTAS
    
    Características:
    - 14 columnas esperadas
    - 60-100 filas de datos típicamente
    - Fila 9: Cabecera
    - Filas 10+: Datos transaccionales (ventas individuales)
    
    Columnas esperadas:
    1. Código Único
    2. Cantidad
    3. Descripción
    4. Precio Unitario
    5-14. Metadata específica de venta
    """
    
    # Configuración específica para VENTAS
    FILA_CABECERA = 9
    FILA_INICIO_DATOS = 10
    NUMERO_COLUMNAS_ESPERADO = 14
    
    # Nombres de columnas extraídos directamente de los archivos Excel reales
    COLUMNAS = [
        'EAN', # Punto de venta EAN
        'Descripción', # Punto de venta Nombre
        'Código interno Almacen',
        'Fecha Inicial',
        'Fecha Final',
        'Código EAN del item',
        'Código de Ítem / Com',
        'Código de Ítem / Pro',
        'Descripción del Ítem',
        'Cantidad Vendida',
        'Unidad de Medida',
        'Precio neto al consu',
        'Precio neto al consu_1', # Duplicate column name in portal
        'Precio neto al consumido sin impuestos'
    ]
    
    def procesar(self) -> Dict[str, Any]:
        """
        Procesa un reporte de VENTAS completo
        
        Returns:
            Diccionario con estructura:
            {
                'tipo': 'VENTAS',
                'metadata': Metadata object,
                'cabeceras': [lista de columnas],
                'detalles': [lista de FilaDetalle],
                'resumen': {
                    'total_filas': int,
                    'total_cantidad': float,
                    'total_dinero': float,
                    'errores_validacion': [list]
                },
                'valido': bool
            }
        """
        
        logger.info("=" * 80)
        logger.info("🔄 PROCESANDO REPORTE VENTAS")
        logger.info(f"   Archivo: {self.ruta_archivo.name}")
        logger.info("=" * 80)
        
        # Validar estructura general
        es_valido, errores_estructura = self.validar_estructura()
        
        if not es_valido:
            logger.error(f"❌ Estructura inválida:")
            for error in errores_estructura:
                logger.error(f"   - {error}")
            return {
                'tipo': 'VENTAS',
                'valido': False,
                'errores': errores_estructura
            }
        
        # Extraer metadata
        metadata = self.extraer_metadata()
        
        # Extraer cabeceras y detalles
        cabeceras = self.extraer_cabeceras()
        detalles = self.extraer_detalles()
        
        # Validar detalles y calcular resumen
        resumen = self._calcular_resumen(detalles)
        
        resultado = {
            'tipo': 'VENTAS',
            'metadata': metadata,
            'cabeceras': cabeceras,
            'detalles': detalles,
            'resumen': resumen,
            'valido': True,
        }
        
        logger.info(
            f"✅ Procesamiento completado:\n"
            f"   Total filas: {resumen['total_filas']}\n"
            f"   Total cantidad: {resumen['total_cantidad']}\n"
            f"   Total dinero: ${resumen['total_dinero']:,.2f}\n"
            f"   Hash: {metadata.hash_contenido[:16]}..."
        )
        
        return resultado
    
    def _calcular_resumen(self, detalles: List[FilaDetalle]) -> Dict[str, Any]:
        """
        Calcula resumen de ventas desde detalles
        
        Args:
            detalles: Lista de FilaDetalle extraídas
            
        Returns:
            Diccionario con resumen:
            {
                'total_filas': int,
                'total_cantidad': float (sum de columna Cantidad),
                'total_dinero': float (sum de columna Total),
                'precio_promedio': float,
                'cantidad_promedio': float,
                'filas_con_descuento': int,
                'filas_sin_desc': int,
                'errores_validacion': [list]
            }
        """
        
        total_filas = len(detalles)
        total_cantidad = 0.0
        total_dinero = 0.0
        filas_con_descuento = 0
        errores = []
        
        for fila in detalles:
            datos = fila.datos
            
            try:
                # Extraer valores numéricos
                cantidad = float(datos.get('Cantidad Vendida', 0) or 0)
                total = float(datos.get('Precio neto al consu_1', 0) or 0)
                descuento = 0
                
                total_cantidad += cantidad
                total_dinero += total
                
                if descuento > 0:
                    filas_con_descuento += 1
                    
            except (ValueError, TypeError) as e:
                errores.append(
                    f"Fila {fila.numero_fila}: Error parsing numérico - {str(e)}"
                )
        
        # Calcular promedios
        precio_promedio = total_dinero / total_filas if total_filas > 0 else 0
        cantidad_promedio = total_cantidad / total_filas if total_filas > 0 else 0
        
        resumen = {
            'total_filas': total_filas,
            'total_cantidad': round(total_cantidad, 2),
            'total_dinero': round(total_dinero, 2),
            'precio_promedio': round(precio_promedio, 2),
            'cantidad_promedio': round(cantidad_promedio, 2),
            'filas_con_descuento': filas_con_descuento,
            'filas_sin_desc': total_filas - filas_con_descuento,
            'errores_validacion': errores if errores else None
        }
        
        return resumen
    
    def extraer_codigo_unico(self, fila_detalle: FilaDetalle) -> str:
        """
        Extrae código único de una fila (primera columna)
        Usado como clave para deduplicación
        
        Args:
            fila_detalle: FilaDetalle a procesar
            
        Returns:
            Código único como string
        """
        
        valor = fila_detalle.datos.get('Código EAN del item', '')
        return str(valor).strip() if valor else ''
    
    def validar_fila_ventas(self, fila_detalle: FilaDetalle) -> tuple[bool, List[str]]:
        """
        Valida que una fila de venta tenga datos mínimos requeridos
        
        Args:
            fila_detalle: FilaDetalle a validar
            
        Returns:
            Tupla (es_válida, lista_errores)
        """
        
        errores = []
        
        # Validar código único (obligatorio)
        codigo = fila_detalle.datos.get('Código EAN del item', '')
        if not codigo:
            errores.append("Código EAN del item vacío")
        
        # Validar cantidad (debe ser > 0)
        try:
            cantidad = float(fila_detalle.datos.get('Cantidad Vendida', 0) or 0)
            if cantidad <= 0:
                errores.append(f"Cantidad Vendida inválida: {cantidad}")
        except (ValueError, TypeError):
            errores.append("Cantidad Vendida no numérica")
        
        # Validar total (debe ser > 0)
        try:
            total = float(fila_detalle.datos.get('Precio neto al consu_1', 0) or 0)
            if total <= 0:
                errores.append(f"Precio neto al consu_1 inválido: {total}")
        except (ValueError, TypeError):
            errores.append("Precio neto al consu_1 no numérico")
        
        return len(errores) == 0, errores


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == '__main__':
    import sys
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Buscar archivo de prueba
    test_file = Path('descargas_reportes/ventas/VENTAS_PAGE1_FILA1_20260227_161509.xlsx')
    
    if not test_file.exists():
        print(f"❌ Archivo no encontrado: {test_file}")
        sys.exit(1)
    
    # Procesar
    with ExcelParserVentas(test_file) as parser:
        resultado = parser.procesar()
        
        if resultado['valido']:
            print(f"\n✅ Procesamiento exitoso")
            print(f"   Tipo: {resultado['tipo']}")
            print(f"   Filas: {resultado['resumen']['total_filas']}")
            print(f"   Total: ${resultado['resumen']['total_dinero']:,.2f}")
        else:
            print(f"\n❌ Error en procesamiento")
            print(f"   Errores: {resultado['errores']}")
