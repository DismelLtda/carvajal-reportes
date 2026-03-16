"""
Módulo de notificaciones por correo para alertas de errores
Utiliza yagmail para enviar notificaciones cuando ocurren errores en el proceso de descarga
"""

import yagmail
import logging
from datetime import datetime
from typing import Optional

# Configuración del correo
CORREO_REMITENTE = "notificacion@dismelltda.com"
PASSWORD_CORREO = "muaebnciwfmoelgl"
CORREO_DESTINATARIO = "soporte@dismelltda.com"

logger = logging.getLogger(__name__)


def enviar_notificacion_error(
    titulo_error: str,
    descripcion_error: str,
    tipo_error: str = "DESCONOCIDO",
    detalles_tecnicos: Optional[str] = None,
    paso_fallido: Optional[str] = None
) -> bool:
    """
    Envía una notificación de error por correo a soporte@dismelltda.com
    
    Args:
        titulo_error (str): Título descriptivo del error
        descripcion_error (str): Descripción del problema
        tipo_error (str): Tipo de error (LOGIN, DESCARGA, NAVEGACION, etc.)
        detalles_tecnicos (str, optional): Detalles técnicos del error
        paso_fallido (str, optional): En qué paso del proceso falló
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        # Crear instancia de yagmail
        yag = yagmail.SMTP(CORREO_REMITENTE, PASSWORD_CORREO)
        
        # Timestamp actual
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Construir el cuerpo del correo
        asunto = f"❌ ALERTA DE ERROR - {tipo_error}"
        
        cuerpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4;">
                <div style="max-width: 600px; margin: 5px auto; background-color: white; padding: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    
                    <h2 style="color: #d32f2f; border-bottom: 3px solid #d32f2f; padding-bottom: 10px;">
                        ⚠️ ALERTA DE ERROR EN EL PROCESO
                    </h2>
                    
                    <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 4px;">
                        <p style="margin: 0; color: #856404;"><strong>Se ha detectado un error en la automatización.</strong></p>
                    </div>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 5px 0;">
                        <tr style="background-color: #f5f5f5;">
                            <td style="padding: 10px; border: 1px solid #ddd; width: 30%; font-weight: bold;">Fecha/Hora:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{timestamp}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Tipo de Error:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong style="color: #d32f2f;">{tipo_error}</strong></td>
                        </tr>
                        <tr style="background-color: #f5f5f5;">
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; vertical-align: top;">Descripción:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{descripcion_error}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; vertical-align: top;">Título:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{titulo_error}</td>
                        </tr>
                        {f'<tr style="background-color: #f5f5f5;"><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Paso Fallido:</td><td style="padding: 10px; border: 1px solid #ddd;">{paso_fallido}</td></tr>' if paso_fallido else ''}
                        {f'<tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; vertical-align: top;">Detalles Técnicos:</td><td style="padding: 10px; border: 1px solid #ddd;"><code style="background-color: #f0f0f0; padding: 8px; border-radius: 4px; display: block; word-break: break-all;">{detalles_tecnicos}</code></td></tr>' if detalles_tecnicos else ''}
                    </table>
                    
                    <div style="background-color: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px; margin: 20px 0; border-radius: 4px;">
                        <p style="margin: 0; color: #2e7d32;">
                            <strong>Acción Requerida:</strong> Por favor, revisa los logs en la carpeta <code>logs_reportes/</code> para más información detallada del error.
                        </p>
                    </div>
                    
                    <p style="color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px;">
                        Este es un mensaje automático del sistema de automatización de descargas de reportes.
                        <br>No responda a este correo.
                    </p>
                </div>
            </body>
        </html>
        """
        
        # Enviar el correo
        yag.send(
            to=CORREO_DESTINATARIO,
            subject=asunto,
            contents=cuerpo_html
        )
        
        logger.info(f"✉️ Notificación de error enviada exitosamente a {CORREO_DESTINATARIO}")
        logger.info(f"   Tipo: {tipo_error} | Asunto: {asunto}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error al enviar notificación por correo: {str(e)}", exc_info=True)
        return False


def enviar_notificacion_éxito(
    cantidad_descargas: int,
    ruta_reportes: str,
    ruta_logs: str
) -> bool:
    """
    Envía una notificación de éxito cuando se completa el proceso correctamente
    
    Args:
        cantidad_descargas (int): Cantidad de archivos descargados
        ruta_reportes (str): Ruta donde se guardaron los reportes
        ruta_logs (str): Ruta del archivo de logs
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        yag = yagmail.SMTP(CORREO_REMITENTE, PASSWORD_CORREO)
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        asunto = "✅ PROCESO EXITOSO - Descarga de Reportes Completada"
        
        cuerpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4;">
                <div style="max-width: 600px; margin: 20px auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    
                    <h2 style="color: #4caf50; border-bottom: 3px solid #4caf50; padding-bottom: 10px;">
                        ✅ PROCESO COMPLETADO EXITOSAMENTE
                    </h2>
                    
                    <div style="background-color: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px; margin: 10px 0; border-radius: 4px;">
                        <p style="margin: 0; color: #2e7d32;"><strong>La descarga de reportes se completó sin problemas.</strong></p>
                    </div>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
                        <tr style="background-color: #f5f5f5;">
                            <td style="padding: 10px; border: 1px solid #ddd; width: 30%; font-weight: bold;">Fecha/Hora:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{timestamp}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Estado:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong style="color: #4caf50;">✅ EXITOSO</strong></td>
                        </tr>
                        <tr style="background-color: #f5f5f5;">
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Archivos Descargados:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>{cantidad_descargas}</strong> archivo(s)</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; vertical-align: top;">Ubicación de Reportes:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;"><code style="background-color: #f0f0f0; padding: 8px; border-radius: 4px;">{ruta_reportes}</code></td>
                        </tr>
                        <tr style="background-color: #f5f5f5;">
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; vertical-align: top;">Archivo de Logs:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;"><code style="background-color: #f0f0f0; padding: 8px; border-radius: 4px;">{ruta_logs}</code></td>
                        </tr>
                    </table>
                    
                    <p style="color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px;">
                        Este es un mensaje automático del sistema de automatización de descargas de reportes.
                    </p>
                </div>
            </body>
        </html>
        """
        
        yag.send(
            to=CORREO_DESTINATARIO,
            subject=asunto,
            contents=cuerpo_html
        )
        
        logger.info(f"✉️ Notificación de éxito enviada a {CORREO_DESTINATARIO}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error al enviar notificación de éxito: {str(e)}", exc_info=True)
        return False
