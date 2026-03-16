"""
CARVAJAL VENTAS - Sistema de procesamiento automatizado de reportes
Procesa reportes de VENTAS e INVENTARIO, almacena en BD y expone vía API para Odoo 14
"""

__version__ = '0.1.0'
__author__ = 'Development Team'
__description__ = 'Automated VENTAS/INVENTARIO Excel report processing for Odoo 14'

from . import config
from . import processor

__all__ = [
    'config',
    'processor',
]
