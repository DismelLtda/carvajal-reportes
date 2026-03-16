"""
📦 PARSER DE REPORTES INVENTARIO
Extrae datos de reportes de inventario (8000+ filas, 13 columnas)
Estructura: Metadata (filas 1-8) + Cabecera (fila 9) + Datos (filas 10+)
"""

from pathlib import Path
from typing import List, Dict, Any
from ..base.excel_parser import ExcelParserBase, FilaDetalle
import logging

logger = logging.getLogger(__name__)


class ExcelParserInventario(ExcelParserBase):
    """
    Parser especializado para reportes de INVENTARIO
    
    Características:
    - 13 columnas esperadas
    - 8000-20000 filas de datos típicamente
    - Fila 9: Cabecera
    - Filas 10+: Datos de stock (snapshot por SKU y localización)
    
    Columnas esperadas:
    1. Item EAN
    2. PV EAN
    3. Descripción
    4. Código Lugar
    5. Descripción Lugar
    6. Cantidad Física
    7. Cantidad Sistema
    8. Diferencia
    9-13. Metadata específica de inventario
    """
    
    # Configuración específica para INVENTARIO
    FILA_CABECERA = 9
    FILA_INICIO_DATOS = 10
    NUMERO_COLUMNAS_ESPERADO = 12
    
    # Nombres de columnas extraídos directamente de los archivos Excel reales
    COLUMNAS = [
        'Código de Producto / Ean',
        'Descripción de Producto',
        'COL_3', # Columna vacía en portal
        'Código interno Almacen',
        'Cantidad',
        'Código Lugar',
        'COL_7', # Columna vacía en portal
        'Nombre Lugar',
        'Código de item / Com',
        'Precio Lista',
        'Precio Neto',
        'Precio Neto_1' # Duplicate column name in portal
    ]
    
    def procesar(self) -> Dict[str, Any]:
        """
        Procesa un reporte de INVENTARIO completo
        
        Returns:
            Diccionario con estructura:
            {
                'tipo': 'INVENTARIO',
                'metadata': Metadata object,
                'cabeceras': [lista de columnas],
                'detalles': [lista de FilaDetalle],
                'resumen': {
                    'total_filas': int,
                    'total_items_unicos': int,
                    'total_lugares_unicos': int,
                    'cantidad_total_fisica': float,
                    'cantidad_total_sistema': float,
                    'items_con_diferencia': int,
                    'diferencia_total': float,
                    'lugares_con_diferencia': dict,
                    'errores_validacion': [list]
                },
                'valido': bool
            }
        """
        
        logger.info("=" * 80)
        logger.info("🔄 PROCESANDO REPORTE INVENTARIO")
        logger.info(f"   Archivo: {self.ruta_archivo.name}")
        logger.info("=" * 80)
        
        # Validar estructura general
        es_valido, errores_estructura = self.validar_estructura()
        
        if not es_valido:
            logger.error(f"❌ Estructura inválida:")
            for error in errores_estructura:
                logger.error(f"   - {error}")
            return {
                'tipo': 'INVENTARIO',
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
            'tipo': 'INVENTARIO',
            'metadata': metadata,
            'cabeceras': cabeceras,
            'detalles': detalles,
            'resumen': resumen,
            'valido': True,
        }
        
        logger.info(
            f"✅ Procesamiento completado:\n"
            f"   Total filas: {resumen['total_filas']}\n"
            f"   Items únicos: {resumen['total_items_unicos']}\n"
            f"   Lugares únicos: {resumen['total_lugares_unicos']}\n"
            f"   Cantidad total: {resumen['cantidad_total_fisica']:,.0f} unidades\n"
            f"   Items con diferencia: {resumen['items_con_diferencia']}\n"
            f"   Hash: {metadata.hash_contenido[:16]}..."
        )
        
        return resultado
    
    def _calcular_resumen(self, detalles: List[FilaDetalle]) -> Dict[str, Any]:
        """
        Calcula resumen de inventario desde detalles
        
        Args:
            detalles: Lista de FilaDetalle extraídas
            
        Returns:
            Diccionario con resumen:
            {
                'total_filas': int,
                'total_items_unicos': int (count distinct Item EAN),
                'total_lugares_unicos': int (count distinct Código Lugar),
                'cantidad_total_fisica': float,
                'cantidad_total_sistema': float,
                'items_con_diferencia': int,
                'diferencia_total': float (sum de dif negativas),
                'lugares_con_diferencia': dict de {lugar: diferencia_neta},
                'errores_validacion': [list]
            }
        """
        
        total_filas = len(detalles)
        items_unicos = set()
        lugares_unicos = set()
        cantidad_total_fisica = 0.0
        cantidad_total_sistema = 0.0
        items_con_diferencia = 0
        diferencia_total = 0.0
        lugares_diferencias = {}
        errores = []
        
        for fila in detalles:
            datos = fila.datos
            
            try:
                # Extraer identificadores
                item_ean = datos.get('Código de Producto / Ean', '')
                codigo_lugar = datos.get('Código interno Almacen', '')
                
                if item_ean:
                    items_unicos.add(str(item_ean))
                
                if codigo_lugar:
                    lugares_unicos.add(str(codigo_lugar))
                
                # Extraer valores numéricos
                cantidad_fisica = float(datos.get('Cantidad', 0) or 0)
                cantidad_sistema = 0
                diferencia = 0
                
                cantidad_total_fisica += cantidad_fisica
                cantidad_total_sistema += cantidad_sistema
                
                if diferencia != 0:
                    items_con_diferencia += 1
                    diferencia_total += abs(diferencia)
                    
                    # Registro de diferencias por lugar
                    if codigo_lugar not in lugares_diferencias:
                        lugares_diferencias[codigo_lugar] = 0
                    lugares_diferencias[codigo_lugar] += diferencia
                    
            except (ValueError, TypeError) as e:
                errores.append(
                    f"Fila {fila.numero_fila}: Error parsing numérico - {str(e)}"
                )
        
        # Ordenar lugares por diferencia absoluta
        lugares_con_diferencia_ordenados = dict(
            sorted(
                lugares_diferencias.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:10]  # Top 10
        )
        
        resumen = {
            'total_filas': total_filas,
            'total_items_unicos': len(items_unicos),
            'total_lugares_unicos': len(lugares_unicos),
            'cantidad_total_fisica': round(cantidad_total_fisica, 2),
            'cantidad_total_sistema': round(cantidad_total_sistema, 2),
            'items_con_diferencia': items_con_diferencia,
            'diferencia_total': round(diferencia_total, 2),
            'lugares_con_diferencia': lugares_con_diferencia_ordenados,
            'porcentaje_con_diferencia': round(
                (items_con_diferencia / total_filas * 100) if total_filas > 0 else 0,
                2
            ),
            'errores_validacion': errores if errores else None
        }
        
        return resumen
    
    def extraer_ean_codigo_lugar(self, fila_detalle: FilaDetalle) -> tuple[str, str]:
        """
        Extrae EAN y Código Lugar de una fila (clave compuesta)
        Usado como clave para deduplicación en BD
        
        Args:
            fila_detalle: FilaDetalle a procesar
            
        Returns:
            Tupla (item_ean, codigo_lugar)
        """
        
        ean = str(fila_detalle.datos.get('Código de Producto / Ean', '')).strip()
        lugar = str(fila_detalle.datos.get('Código interno Almacen', '')).strip()
        
        return ean, lugar
    
    def validar_fila_inventario(self, fila_detalle: FilaDetalle) -> tuple[bool, List[str]]:
        """
        Valida que una fila de inventario tenga datos mínimos requeridos
        
        Args:
            fila_detalle: FilaDetalle a validar
            
        Returns:
            Tupla (es_válida, lista_errores)
        """
        
        errores = []
        
        # Validar Código de Producto / Ean (obligatorio)
        ean = fila_detalle.datos.get('Código de Producto / Ean', '')
        if not ean:
            errores.append("Código de Producto / Ean vacío")
        
        # Validar Código interno Almacen (obligatorio)
        lugar = fila_detalle.datos.get('Código interno Almacen', '')
        if not lugar:
            errores.append("Código interno Almacen vacío")
        
        # Validar Cantidad (obligatorio, debe ser >= 0)
        try:
            cant = float(fila_detalle.datos.get('Cantidad', 0) or 0)
            if cant < 0:
                errores.append(f"Cantidad negativa: {cant}")
        except (ValueError, TypeError):
            errores.append("Cantidad no numérica")
        
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
    
    # Buscar archivos de prueba
    test_files = list(Path('descargas_reportes/inventario').glob('*.xlsx'))
    
    if not test_files:
        print(f"❌ No se encontraron archivos de inventario")
        sys.exit(1)
    
    # Procesar el primero
    test_file = test_files[0]
    print(f"\n🔍 Procesando: {test_file.name}\n")
    
    with ExcelParserInventario(test_file) as parser:
        resultado = parser.procesar()
        
        if resultado['valido']:
            print(f"\n✅ Procesamiento exitoso")
            print(f"   Tipo: {resultado['tipo']}")
            print(f"   Filas: {resultado['resumen']['total_filas']}")
            print(f"   Items únicos: {resultado['resumen']['total_items_unicos']}")
            print(f"   Lugares: {resultado['resumen']['total_lugares_unicos']}")
            print(f"   Cantidad total: {resultado['resumen']['cantidad_total_fisica']:,.0f}")
        else:
            print(f"\n❌ Error en procesamiento")
            print(f"   Errores: {resultado['errores']}")
