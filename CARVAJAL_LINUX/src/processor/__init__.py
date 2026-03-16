"""
Excel Report Processing Framework
Supports VENTAS and INVENTARIO report types with shared architecture
"""

from .detector import ReporteDetector, TipoReporte
from .base import ExcelParserBase, Metadata, FilaDetalle
from .ventas import ExcelParserVentas
from .inventario import ExcelParserInventario

__all__ = [
    'ReporteDetector',
    'TipoReporte',
    'ExcelParserBase',
    'Metadata',
    'FilaDetalle',
    'ExcelParserVentas',
    'ExcelParserInventario',
]
