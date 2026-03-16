#!/usr/bin/env python3
# ============================================================================
# CARVAJAL VENTAS - Script de Sincronización a Servidor
# ============================================================================
# Este script se ejecuta en Windows Server 2016
# Propósito: Carga automáticamente archivos descargados al servidor Rocky Linux
# Uso: python sync_to_server.py (desde Task Scheduler de Windows)
#
# Prerequisito: pip install paramiko python-dotenv
# ============================================================================

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import paramiko
from dotenv import load_dotenv
import time

# Cargar variables de entorno
load_dotenv()

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Servidor Rocky Linux
SERVIDOR_HOST = os.getenv('SERVIDOR_HOST', 'IP_SERVIDOR')  # IP o hostname
SERVIDOR_PUERTO = int(os.getenv('SERVIDOR_PUERTO', 22))
SERVIDOR_USUARIO = os.getenv('SERVIDOR_USUARIO', 'carvajal')
SERVIDOR_CONTRASEÑA = os.getenv('SERVIDOR_CONTRASEÑA', '')
SERVIDOR_RUTA_DESTINO = os.getenv('SERVIDOR_RUTA_DESTINO', '/opt/carvajal/descargas_reportes/')

# Directorios locales (Windows)
DIRECTORIO_DESCARGAS = os.getenv('DIRECTORIO_DESCARGAS', 'descargas_reportes')
DIRECTORIO_LOGS = os.getenv('DIRECTORIO_LOGS', 'logs_sincronizacion')

# Configurar logging
Path(DIRECTORIO_LOGS).mkdir(exist_ok=True)
timestamp_log = datetime.now().strftime("%Y%m%d_%H%M%S")
archivo_log = os.path.join(DIRECTORIO_LOGS, f"sincronizacion_{timestamp_log}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(archivo_log, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# CLASES Y FUNCIONES
# ============================================================================

class SincronizadorSFTP:
    """Sincroniza archivos Excel descargados al servidor via SFTP"""
    
    def __init__(self, host, puerto, usuario, contraseña, ruta_destino):
        self.host = host
        self.puerto = puerto
        self.usuario = usuario
        self.contraseña = contraseña
        self.ruta_destino = ruta_destino
        self.client = None
        self.sftp = None
        self.contador_sincronizados = 0
        self.contador_errores = 0
    
    def conectar(self):
        """Conecta al servidor via SSH/SFTP"""
        try:
            logger.info(f"🔗 Conectando a {self.host}:{self.puerto}...")
            
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.client.connect(
                self.host,
                port=self.puerto,
                username=self.usuario,
                password=self.contraseña,
                timeout=10
            )
            
            self.sftp = self.client.open_sftp()
            logger.info(f"✅ Conectado a {self.host}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando: {str(e)}")
            return False
    
    def desconectar(self):
        """Desconecta del servidor"""
        try:
            if self.sftp:
                self.sftp.close()
            if self.client:
                self.client.close()
            logger.info("✅ Desconectado del servidor")
        except Exception as e:
            logger.warning(f"⚠️  Error desconectando: {str(e)}")
    
    def obtener_archivos_locales(self, directorio):
        """Obtiene lista de archivos Excel preservando estructura de directorios"""
        try:
            archivos = []
            directorio_base = Path(directorio)
            
            # Buscar todos los .xlsx recursivamente
            for archivo in directorio_base.rglob('*.xlsx'):
                # Ignorar archivos en carpetas "procesados"
                if 'procesado' not in str(archivo).lower():
                    # Retornar tupla: (ruta_local, ruta_relativa)
                    ruta_relativa = archivo.relative_to(directorio_base)
                    archivos.append((archivo, str(ruta_relativa)))
            
            return archivos
            
        except Exception as e:
            logger.error(f"Error listando archivos locales: {str(e)}")
            return []
    
    def obtener_archivos_remotos(self):
        """Obtiene lista de archivos en servidor remoto (recursivamente)"""
        try:
            if not self.sftp:
                return set()
            
            archivos_remotos = set()
            
            def listar_recursivamente(ruta, prefijo=''):
                """Busca archivos recursivamente en el servidor"""
                try:
                    for item in self.sftp.listdir_attr(ruta):
                        ruta_completa = f"{ruta}/{item.filename}"
                        prefijo_item = f"{prefijo}{item.filename}" if not prefijo else f"{prefijo}/{item.filename}"
                        
                        # Si es directorio, entrar recursivamente
                        if item.filename not in ['.', '..']:
                            if item.filename[-1] != '/':  # Archivo
                                if item.filename.endswith('.xlsx'):
                                    archivos_remotos.add(prefijo_item)
                            else:  # Directorio
                                try:
                                    listar_recursivamente(ruta_completa, prefijo_item[:-1])
                                except IOError:
                                    pass
                except IOError:
                    pass
            
            try:
                listar_recursivamente(self.ruta_destino)
            except IOError:
                logger.warning(f"⚠️  Directorio remoto no existe aún: {self.ruta_destino}")
            
            return archivos_remotos
            
        except Exception as e:
            logger.error(f"Error listando archivos remotos: {str(e)}")
            return set()
    
    def crear_directorio_remoto(self, ruta):
        """Crea un directorio en el servidor si no existe"""
        try:
            try:
                self.sftp.stat(ruta)
                # Directorio ya existe
                return True
            except IOError:
                # No existe, crearlo
                logger.info(f"📁 Creando directorio remoto: {ruta}")
                self.sftp.mkdir(ruta)
                return True
        except Exception as e:
            logger.error(f"❌ Error creando directorio {ruta}: {str(e)}")
            return False
    
    def subir_archivo(self, ruta_local, ruta_relativa):
        """Sube un archivo al servidor preservando estructura de directorios"""
        try:
            # Construir ruta remota completa
            ruta_remota = f"{self.ruta_destino}{ruta_relativa}".replace('\\', '/')
            
            # Crear directorio padre si no existe
            directorio_remoto = '/'.join(ruta_remota.split('/')[:-1])
            if directorio_remoto and directorio_remoto != self.ruta_destino.rstrip('/'):
                # Crear directorios padre
                partes = directorio_remoto.split('/')
                ruta_actual = ''
                for parte in partes:
                    if parte:
                        ruta_actual = f"{ruta_actual}/{parte}" if ruta_actual else f"/{parte}"
                        if not ruta_actual.startswith('/'):
                            ruta_actual = f"/{ruta_actual}"
                        try:
                            self.sftp.stat(ruta_actual)
                        except IOError:
                            try:
                                self.sftp.mkdir(ruta_actual)
                                logger.info(f"  └─ Directorio creado: {ruta_actual}")
                            except Exception as e:
                                logger.warning(f"  ⚠️  No se pudo crear {ruta_actual}: {str(e)}")
            
            logger.info(f"📤 Subiendo: {ruta_relativa}")
            self.sftp.put(str(ruta_local), ruta_remota)
            
            logger.info(f"✅ Subido correctamente: {ruta_relativa}")
            self.contador_sincronizados += 1
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error subiendo {ruta_relativa}: {str(e)}")
            self.contador_errores += 1
            return False
    
    def sincronizar(self, directorio_local):
        """Sincroniza archivos del directorio local al servidor preservando estructura"""
        logger.info("="*70)
        logger.info(f"INICIO DE SINCRONIZACIÓN - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        logger.info("="*70)
        
        # Conectar
        if not self.conectar():
            logger.error("No se pudo conectar al servidor, abortando sincronización")
            return False
        
        try:
            # Obtener archivos
            archivos_locales = self.obtener_archivos_locales(directorio_local)
            archivos_remotos = self.obtener_archivos_remotos()
            
            logger.info(f"📁 Archivos locales encontrados: {len(archivos_locales)}")
            logger.info(f"📁 Archivos remotos existentes: {len(archivos_remotos)}")
            
            if not archivos_locales:
                logger.warning("⚠️  No hay archivos para sincronizar")
                return True
            
            # Sincronizar nuevos archivos
            for archivo_local, ruta_relativa in archivos_locales:
                # Si ya existe en servidor, saltarlo
                if ruta_relativa in archivos_remotos:
                    logger.info(f"⏭️  Ya existe en servidor: {ruta_relativa}")
                    continue
                
                # Subir archivo con estructura preservada
                self.subir_archivo(archivo_local, ruta_relativa)
            
            logger.info("="*70)
            logger.info(f"SINCRONIZACIÓN COMPLETADA:")
            logger.info(f"  ✅ Sincronizados: {self.contador_sincronizados}")
            logger.info(f"  ❌ Errores: {self.contador_errores}")
            logger.info("="*70)
            
            return self.contador_errores == 0
            
        except Exception as e:
            logger.error(f"Error durante sincronización: {str(e)}", exc_info=True)
            return False
        
        finally:
            self.desconectar()


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal"""
    
    # Validar configuración
    if SERVIDOR_HOST == 'IP_SERVIDOR':
        print("❌ ERROR: No configuraste SERVIDOR_HOST en .env")
        print("Crea/edita .env con:")
        print("  SERVIDOR_HOST=192.168.x.x  (IP del servidor Rocky)")
        print("  SERVIDOR_USUARIO=carvajal")
        print("  SERVIDOR_CONTRASEÑA=tu_contraseña")
        sys.exit(1)
    
    # Validar que exista directorio de descargas
    if not os.path.exists(DIRECTORIO_DESCARGAS):
        logger.error(f"❌ Directorio no existe: {DIRECTORIO_DESCARGAS}")
        sys.exit(1)
    
    # Crear sincronizador
    sincronizador = SincronizadorSFTP(
        host=SERVIDOR_HOST,
        puerto=SERVIDOR_PUERTO,
        usuario=SERVIDOR_USUARIO,
        contraseña=SERVIDOR_CONTRASEÑA,
        ruta_destino=SERVIDOR_RUTA_DESTINO
    )
    
    # Sincronizar
    exitoso = sincronizador.sincronizar(DIRECTORIO_DESCARGAS)
    
    # Retornar código de salida
    sys.exit(0 if exitoso else 1)


if __name__ == "__main__":
    main()
