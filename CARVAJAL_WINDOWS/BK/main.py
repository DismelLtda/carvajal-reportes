from playwright.sync_api import sync_playwright, TimeoutError
import time
import os
from pathlib import Path
from datetime import datetime
import logging
import sys
from notificaciones import enviar_notificacion_error, enviar_notificacion_éxito

URL_LOGIN = "https://cencarvajal.com/#/portal/login"

USUARIO = "director.cadenas@dismelltda.com"
CONTRASENA = "Dismel05211921#$"

RE_INVENTARIO = "https://cencarvajal.com/receivingadvicenewportal/#/home/consult-service?service=INVRPT"
RE_VENTAS = "https://cencarvajal.com/receivingadvicenewportal/#/home/consult-service?service=SLSRPT"

MAX_INTENTOS = 3  # Cuántas veces intentará hacer login
DIRECTORIO_DESCARGAS = "descargas_reportes"
DIRECTORIO_LOGS = "logs_reportes"

# Crear directorios si no existen
Path(DIRECTORIO_DESCARGAS).mkdir(exist_ok=True)
Path(DIRECTORIO_LOGS).mkdir(exist_ok=True)

# Configurar logging
timestamp_log = datetime.now().strftime("%Y%m%d_%H%M%S")
archivo_log = os.path.join(DIRECTORIO_LOGS, f"reporte_descargas_{timestamp_log}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(archivo_log, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info("="*70)
logger.info(f"INICIO DE SESIÓN - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
logger.info("="*70)

def intentar_login(page):
    # Rellenar campos
    page.fill('input[formcontrolname="textUsuario"]', USUARIO)
    page.fill('input[formcontrolname="textClave"]', CONTRASENA)
    # Clic en Ingresar
    page.click('button:has-text("Ingresar")')

def descargar_reportes_con_paginacion(page, report_url, report_type="VENTAS"):
    """
    Descarga todos los reportes con manejo de búsqueda, tabla dinámicas y paginación.
    """
    logger.info("="*70)
    logger.info(f"[*] Iniciando descarga de Reportes {report_type}")
    logger.info("="*70)
    
    # Navegar al reporte
    logger.info(f"Navegando a: {report_url}")
    try:
        page.goto(report_url, wait_until="commit", timeout=30000)
    except Exception as e_nav:
        logger.warning(f"Advertencia en navegación inicial: {str(e_nav)}")
    
    # Dar tiempo a Angular para que cargue
    logger.info("Esperando que Angular cargue...")
    try:
        page.wait_for_load_state("domcontentloaded", timeout=30000)
    except Exception as e_dom:
        logger.warning(f"Timeout esperando DOMContentLoaded: {str(e_dom)}")
    
    # Esperar a que carguen los filtros
    try:
        page.wait_for_selector('button:has-text("Buscar")', timeout=15000)
        logger.info("✓ Formulario de filtros cargado")
    except TimeoutError:
        logger.error("✗ No se encontró el botón 'Buscar' en el formulario")
        return
    
    # Dar tiempo a que Angular renderice completamente
    time.sleep(2)
    
    # Rellenar campos de fecha (Fecha inicio: ayer, Fecha fin: hoy)
    try:
        from datetime import timedelta
        
        hoy = datetime.now()
        ayer = hoy - timedelta(days=1)
        
        fecha_inicio = ayer.strftime("%d/%m/%Y")
        fecha_fin = hoy.strftime("%d/%m/%Y")
        
        logger.info(f"Configurando filtro de fechas: {fecha_inicio} a {fecha_fin}")
        
        # Llenar campo "Fecha inicio"
        input_fecha_inicio = page.query_selector('input[placeholder="Fecha inicio"]')
        if input_fecha_inicio:
            input_fecha_inicio.fill(fecha_inicio)
            logger.info(f"Campo 'Fecha inicio' rellenado: {fecha_inicio}")
            # Presionar Tab para cerrar el calendario y pasar al siguiente campo
            input_fecha_inicio.press("Tab")
            time.sleep(0.5)
        else:
            logger.warning("No se encontró el campo 'Fecha inicio'")
        
        # Llenar campo "Fecha fin"
        input_fecha_fin = page.query_selector('input[placeholder="Fecha fin"]')
        if input_fecha_fin:
            input_fecha_fin.fill(fecha_fin)
            logger.info(f"Campo 'Fecha fin' rellenado: {fecha_fin}")
            # Presionar Escape para cerrar el calendario
            input_fecha_fin.press("Escape")
            time.sleep(0.5)
        else:
            logger.warning("No se encontró el campo 'Fecha fin'")
        
        time.sleep(1)  # Dar tiempo a que se registren los cambios
        logger.info("Calendarios cerrados, filtros de fecha configurados")
        
    except Exception as e:
        logger.warning(f"Error al rellenar fechas: {str(e)}")
    
    # Presionar botón "Buscar" para obtener listado
    try:
        logger.info("🔍 Presionando botón 'Buscar' para obtener el listado...")
        boton_buscar = page.query_selector('button:has-text("Buscar")')
        
        if boton_buscar:
            boton_buscar.click()
            # Esperar a que aparezca la tabla con resultados
            page.wait_for_selector('p-table table tbody tr', timeout=15000)
            logger.info("✓ Búsqueda completada y tabla cargada")
            time.sleep(2)  # Dar tiempo a Angular a renderizar completamente
        else:
            logger.error("✗ Botón 'Buscar' no encontrado para hacer clic")
            return
            
    except TimeoutError:
        logger.warning("⚠ No se encontraron registros en la búsqueda")
        return
    except Exception as e:
        logger.error(f"✗ Error al presionar Buscar: {str(e)}")
        return
    
    # Verificar si hay filas en la tabla
    filas = page.query_selector_all('p-table table tbody tr, table tbody tr')
    
    if not filas:
        logger.warning("⚠ No se encontraron registros en la búsqueda (tabla vacía)")
        return
    
    logger.info(f"✓ Se encontraron {len(filas)} registro(s)")
    
    contador_descargas = 0
    pagina_actual = 1
    max_paginas = 50  # Limite de seguridad
    
    while pagina_actual <= max_paginas:
        logger.info(f"📄 Procesando página {pagina_actual}...")
        
        try:
            # Obtener todas las filas visibles de la tabla
            filas = page.query_selector_all('p-table table tbody tr, table tbody tr')
            
            if not filas:
                logger.warning("⚠ No hay más filas. Fin de paginación.")
                break
            
            logger.info(f"  -> {len(filas)} fila(s) en esta página")
            
            # Procesar cada fila
            indice_fila = 0
            while True:
                filas = page.query_selector_all('p-table table tbody tr, table tbody tr')
                
                if indice_fila >= len(filas):
                    break
                
                fila = filas[indice_fila]
                idx = indice_fila + 1
                try:
                    # Obtener info de la fila
                    celdas = fila.query_selector_all('td')
                    
                    # Extraer información visible de las primeras celdas
                    info_celdas = []
                    for i, celda in enumerate(celdas[2:5]):  # Saltar checkbox y botón descarga
                        texto = celda.text_content().strip()[:35]
                        if texto:
                            info_celdas.append(texto)
                    info_fila = " | ".join(info_celdas) if info_celdas else f"Fila {idx}"
                    
                    # Buscar botón de descarga específicamente: button con icon "pi pi-download"
                    boton_descarga = fila.query_selector('button[icon*="download"], button.pi-download, button[class*="pi-download"]')
                    
                    if not boton_descarga:
                        # Si no encontró, buscar en la primera celda de datos (segunda celda)
                        if len(celdas) > 1:
                            primera_celda = celdas[1]
                            boton_descarga = primera_celda.query_selector('button')
                    
                    if boton_descarga:
                        logger.info(f"Fila {idx}: Iniciando descarga - {info_fila}")
                        
                        try:
                            # Hacer clic en descargar
                            boton_descarga.click()
                            
                            # Esperar a que aparezca el modal de selección de formato
                            try:
                                page.wait_for_selector('.download-modal, .p-dialog-content, [name="downloadOption"]', timeout=5000)
                                logger.info(f"Fila {idx}: Modal de formato abierto, esperando selección...")
                                time.sleep(1)  # Esperar a que se abra el modal
                                
                                # Seleccionar XLSX
                                radio_buttons = page.query_selector_all('p-radiobutton')
                                excel_encontrado = False
                                
                                for rb in radio_buttons:
                                    input_radio = rb.query_selector('input[value="XLSX"]')
                                    if input_radio:
                                        radiobox = rb.query_selector('.p-radiobutton-box')
                                        if radiobox:
                                            radiobox.click()
                                            logger.info(f"Fila {idx}: Formato XLSX seleccionado")
                                            excel_encontrado = True
                                            time.sleep(0.5)
                                            break
                                
                                if not excel_encontrado:
                                    input_xlsx = page.query_selector('input[value="XLSX"][name="downloadOption"]')
                                    if input_xlsx:
                                        input_xlsx.click()
                                        logger.info(f"Fila {idx}: Formato XLSX seleccionado (alternativa)")
                                    else:
                                        logger.warning(f"Fila {idx}: No se encontró opción XLSX")
                                
                                time.sleep(0.5)
                                
                                # Buscar botón Descargar
                                boton_descargar_modal = None
                                footer = page.query_selector('.download-modal .p-dialog-footer, .p-dialog .p-dialog-footer')
                                if footer:
                                    botones_footer = footer.query_selector_all('button')
                                    for btn in botones_footer:
                                        span_label = btn.query_selector('.p-button-label')
                                        if span_label:
                                            texto = (span_label.text_content() or "").strip().lower()
                                            if 'descargar' in texto:
                                                boton_descargar_modal = btn
                                                break
                                
                                if not boton_descargar_modal:
                                    botones_modal = page.query_selector_all('.download-modal button, .p-dialog button')
                                    for btn in botones_modal:
                                        texto_btn = (btn.text_content() or "").strip().lower()
                                        if 'descargar' in texto_btn:
                                            boton_descargar_modal = btn
                                            break
                                
                                if boton_descargar_modal:
                                    logger.info(f"Fila {idx}: Botón Descargar encontrado")
                                    time.sleep(0.5)
                                    
                                    try:
                                        with page.expect_download() as download_info:
                                            boton_descargar_modal.click()
                                            logger.info(f"Fila {idx}: Descargando archivo...")
                                            download = download_info.value
                                            time.sleep(2)
                                            
                                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                            nombre_archivo = f"{report_type}_PAGE{pagina_actual}_FILA{idx}_{timestamp}.xlsx"
                                            ruta_destino = os.path.join(DIRECTORIO_DESCARGAS, nombre_archivo)
                                            
                                            download.save_as(ruta_destino)
                                            contador_descargas += 1
                                            logger.info(f"Fila {idx}: [OK] Descargado exitosamente: {nombre_archivo}")
                                            time.sleep(1)
                                    except Exception as e:
                                        logger.error(f"Fila {idx}: Error en descarga: {str(e)}")
                                else:
                                    logger.error(f"Fila {idx}: Botón Descargar no encontrado")
                                    
                            except TimeoutError:
                                logger.error(f"Fila {idx}: Timeout esperando modal de formato")
                            except Exception as e:
                                logger.error(f"Fila {idx}: Error en proceso modal: {str(e)}")
                                
                        except Exception as e:
                            logger.error(f"Fila {idx}: Error al hacer clic en botón de descarga: {str(e)}")
                    else:
                        logger.warning(f"Fila {idx}: No se encontró botón de descarga")
                
                except Exception as e:
                    logger.error(f"Fila {idx}: Error procesando fila: {str(e)}")
                
                # Incrementar índice para siguiente fila
                indice_fila += 1
            
            # Buscar botón "siguiente" en el paginador
            try:
                paginador = page.query_selector('.p-paginator, [class*="p-paginator"]')
                
                if paginador:
                    siguiente_btn = paginador.query_selector('.p-paginator-next')
                    
                    # Verificar si el botón está deshabilitado (disabled)
                    if siguiente_btn:
                        esta_deshabilitado = siguiente_btn.get_attribute('disabled') is not None
                        
                        if not esta_deshabilitado:
                            logger.info(f"Navegando a página {pagina_actual + 1}...")
                            siguiente_btn.click()
                            pagina_actual += 1
                            
                            # Esperar a que cargue la nueva tabla
                            time.sleep(1)
                            try:
                                page.wait_for_selector('p-table table tbody tr, table tbody tr', timeout=10000)
                                # Verificar si hay filas en nueva página
                                filas_nuevas = page.query_selector_all('p-table table tbody tr, table tbody tr')
                                if filas_nuevas:
                                    logger.info(f"Página {pagina_actual} cargada con {len(filas_nuevas)} fila(s)")
                                else:
                                    logger.info("No hay más páginas. Fin de paginación.")
                                    break
                            except TimeoutError:
                                logger.warning("Timeout esperando tabla en siguiente página. Finalizando.")
                                break
                        else:
                            logger.info("No hay página siguiente. Fin de paginación.")
                            break
                    else:
                        logger.info("No se encontró botón siguiente. Fin de paginación.")
                        break
                else:
                    logger.info("No se encontró paginador. Fin de procesamiento.")
                    break
                
            except Exception as e:
                logger.error(f"Error en paginación: {str(e)}")
                break
        
        except Exception as e:
            logger.error(f"Error procesando página {pagina_actual}: {str(e)}")
            break
    
    logger.info("="*70)
    logger.info(f"[OK] Proceso completado")
    logger.info(f"[REPORT] Total de descargas: {contador_descargas} archivo(s)")
    logger.info(f"📁 Ubicación: {os.path.abspath(DIRECTORIO_DESCARGAS)}")
    logger.info(f"[LOG] Logs guardados en: {archivo_log}")
    logger.info("="*70)

def main():
    try:
        with sync_playwright() as p:
            logger.info("Iniciando Playwright...")
            browser = p.chromium.launch(headless=True)
            logger.info("Navegador (Chromium) lanzado en modo oculto")
            #browser = p.chromium.launch(headless=False)
            #logger.info("Navegador (Chromium) lanzado en modo visible")
            
            # Context con aceptar descargas
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            logger.info(f"Navegando a: {URL_LOGIN}")
            page.goto(URL_LOGIN)

            intentos = 0
            login_exitoso = False

            while intentos < MAX_INTENTOS and not login_exitoso:
                intentos += 1
                logger.info(f"[Intento {intentos}/{MAX_INTENTOS}] Intentando login…")

                try:
                    # Intentar hacer login
                    intentar_login(page)
                    logger.info(f"[Intento {intentos}] Formulario de login enviado")

                    # Esperar el texto que indica que llegó a la página de welcome
                    page.wait_for_selector('text="Tus servicios"', timeout=10000)
                    logger.info(f"[Intento {intentos}] [OK] Login exitoso - texto 'Tus servicios' encontrado")
                    # Esperar a que la página se estabilice completamente
                    logger.info(f"[Intento {intentos}] Esperando que la página se cargue completamente...")

                    time.sleep(2)
                    logger.info(f"[Intento {intentos}] Página estabilizada, listo para descargar")
                    
                    # Descargar reportes INMEDIATAMENTE dentro del bloque exitoso
                    try:
                        descargar_reportes_con_paginacion(page, RE_VENTAS, "VENTAS")
                        logger.info("✅ Descarga de reportes de ventas completada exitosamente")
                    except Exception as e_descarga:
                        logger.error(f"❌ Error descargando reportes: {str(e_descarga)}", exc_info=True)
                        # Enviar notificación de error
                        enviar_notificacion_error(
                            titulo_error="Error durante la descarga de reportes",
                            descripcion_error=f"Se presentó un error al intentar descargar los reportes de ventas del portal Cencarvajal.",
                            tipo_error="DESCARGA",
                            paso_fallido="Descarga de reportes de VENTAS",
                            detalles_tecnicos=str(e_descarga)
                        )
                    
                    login_exitoso = True

                except TimeoutError:
                    # No se encontró el texto; checamos si aparece un modal
                    logger.warning(f"[Intento {intentos}] No apareció 'Tus servicios' después de intentar login (posible modal)")

                    # Intentar clic en el botón Continuar si aparece
                    try:
                        page.click('button:has-text("Continuar")')
                        logger.info(f"[Intento {intentos}] Se hizo clic en botón 'Continuar' del modal")
                        time.sleep(2)  # Esperar a que el modal se cierre completamente
                    except Exception as err_modal:
                        logger.debug(f"[Intento {intentos}] No se encontró el modal Continuar: {err_modal}")

                    # Luego intentamos de nuevo encontrar el texto de bienvenida
                    try:
                        page.wait_for_selector('text="Tus servicios"', timeout=5000)
                        logger.info(f"[Intento {intentos}] [OK] Se encontró 'Tus servicios' tras aceptar modal")
                        login_exitoso = True
                    except TimeoutError:
                        logger.warning(f"[Intento {intentos}] Aún no aparece 'Tus servicios' tras aceptar modal")

                    # Si sigue sin aparecer, hacemos refresh si quedan intentos
                    if not login_exitoso:
                        if intentos < MAX_INTENTOS:
                            logger.info(f"[Intento {intentos}] Navegando de nuevo a login y reintentando...")
                            try:
                                page.goto(URL_LOGIN)
                                # Esperar que carguen los campos de login de nuevo
                                page.wait_for_selector('input[formcontrolname="textUsuario"]', timeout=5000)
                                logger.info(f"[Intento {intentos}] Página de login cargada nuevamente")
                            except Exception as e_reload:
                                logger.warning(f"[Intento {intentos}] Error al navegar: {str(e_reload)}")
                        else:
                            logger.error(f"[Intento {intentos}] Ya no quedan más reintentos de login")

        if not login_exitoso:
            logger.error("❌ No se pudo completar el login tras varios intentos")
            screenshot_error = "login_error.png"
            try:
                page.screenshot(path=screenshot_error)
                logger.info(f"Screenshot de error guardado: {screenshot_error}")
            except:
                logger.error("No se pudo capturar screenshot del error")
            
            # Enviar notificación de error por correo
            enviar_notificacion_error(
                titulo_error="Login fallido tras múltiples intentos",
                descripcion_error=f"No se pudieron completar exitosamente los intentos de login después de {MAX_INTENTOS} intentos. El sistema de autenticación no respondió como se esperaba.",
                tipo_error="LOGIN",
                paso_fallido="Autenticación en portal Cencarvajal",
                detalles_tecnicos=f"No se encontró el elemento 'Tus servicios' después de los intentos de login. Screenshot guardado en: {screenshot_error}"
            )
            
            # Cerrar con manejo seguro
            try:
                context.close()
            except:
                logger.warning("No se pudo cerrar context correctamente")
            try:
                browser.close()
            except:
                logger.warning("No se pudo cerrar browser correctamente")
            logger.error("Navegador cerrado. Proceso terminado con fallo de login.")
            return
        
        logger.info("\n[OK] Navegador cerrado. Proceso finalizado correctamente")
        logger.info(f"[LOG] Archivo de log: {archivo_log}")
        logger.info("="*70)
        
    except Exception as e:
        logger.critical(f"❌ Error crítico en main(): {str(e)}", exc_info=True)
        logger.error("Proceso terminado por error no controlado")
        
        # Enviar notificación de error crítico
        enviar_notificacion_error(
            titulo_error="Error crítico no controlado en el proceso principal",
            descripcion_error="Se presentó una excepción no manejada en la función principal del sistema de automatización.",
            tipo_error="CRÍTICO",
            paso_fallido="main()",
            detalles_tecnicos=str(e)
        )
        
        # Intentar cerrar sin errores
        try:
            context.close()
        except:
            pass
        try:
            browser.close()
        except:
            pass
        
        

if __name__ == "__main__":
    main()