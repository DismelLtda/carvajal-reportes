# Sistema de Descarga Automática de Reportes de Carvajal 

## 🎯 Estado: ✅ FUNCIONANDO

El sistema automatiza completamente el login y descarga de reportes de la plataforma Carvajal usando Python + Playwright.

## 📋 Características

✅ **Login automático** con manejo de modalidades de sesión
✅ **Reintentos automáticos** (hasta 3 intentos) ante fallos
✅ **Descarga de reportes** con nombres estructurados
✅ **Logging detallado** en archivo y consola (sin errores de encoding)
✅ **Manejo de paginación** para múltiples registros
✅ **Selección automática de formato XLSX**
✅ **Mantiene event loop vivo** durante descargas

## 🚀 Uso

```bash
python main.py
```

El script:
1. Abre Chromium en modo visible
2. Intenta login automáticamente (máx 3 intentos)
3. Maneja modales de sesión activa si aparecen
4. Navega a la página de reportes de Ventas
5. Busca todos los registros disponibles
6. Descarga cada reporte en formato XLSX
7. Registra logs detallados con timestamps

## 📁 Estructura de archivos

```
descargas_reportes/
  ├── VENTAS_PAGE1_FILA1_[TIMESTAMP].xlsx
  ├── VENTAS_PAGE1_FILA2_[TIMESTAMP].xlsx
  └── ...

logs_reportes/
  └── reporte_descargas_[TIMESTAMP].log
```

## 🔧 Configuración

Edita `main.py` para cambiar:
- **Credenciales**: Búscar `login_user` / `login_pass`
- **URLs de reportes**: `RE_VENTAS`, `RE_INVENTARIO` (líneas ~10-15)
- **Tiempos de espera**: Cambiar `timeout` en milisegundos

## 🐛 Problemas Resueltos

### ❌ → ✅ Event Loop Cerrado

**Problema original**: El Playwright AsyncIO event loop se cerraba al salir del bloque de login, causando:
```
Error: "Event loop is closed! Is Playwright already stopped?"
```

**Causa raíz**: Llamar a `descargar_reportes_con_paginacion()` **después** de que el `with sync_playwright()` finalizaba.

**Solución implementada** (línea 336-343):
```python
# Dentro del bloque de login exitoso, ANTES de salir del with:
try:
    descargar_reportes_con_paginacion(page, RE_VENTAS, "VENTAS")
    logger.info("OK Descarga de reportes completada")
except Exception as e:
    logger.error(f"Error descargando: {str(e)}")

login_exitoso = True  # Salir del while loop
# Event loop aún está vivo durante la descarga!
```

**Por qué funciona**: Mantenemos todas las operaciones de Playwright dentro de la sesión `with sync_playwright()`, evitando que el event loop se cierre.

### ✅ Encoding Unicode en Windows

**Problema**: Los emojis causaban `UnicodeEncodeError` en console de Windows
**Solución**: Reemplazar emojis con símbolos ASCII: `[OK]`, `[LOG]`, `[REPORT]`, `->`, etc.

## 📊 Ejemplo de log

```
2026-02-27 11:33:38,452 - [Intento 2] [OK] Login exitoso
2026-02-27 11:33:53,592 - Fila 1: [OK] Descargado: VENTAS_PAGE1_FILA1_[...].xlsx
2026-02-27 11:33:54,612 - [OK] Proceso completado
2026-02-27 11:33:54,612 - [REPORT] Total de descargas: 1 archivo(s)
```

## 💡 Próximas mejoras posibles

- [ ] Descarga de reportes de Inventario (solo descomentar líneas)
- [ ] Validación de integridad de archivos XLSX
- [ ] Email de notificación con resumen de descargas
- [ ] Filtros personalizados de rangos de fechas
- [ ] Compresión automática de archivos descargados
- [ ] Retenciónde archivos por N días


Si aún no aparece, refresque la página

Reintente login hasta un número máximo de intentos

Si falla completamente, cierre el navegador y muestre error

Una vez logueado correctamente, navegar a reportes específicos:

RE_VENTAS:
<https://cencarvajal.com/receivingadvicenewportal/#/home/consult-service?service=SLSRPT>

RE_INVENTARIO:
<https://cencarvajal.com/receivingadvicenewportal/#/home/consult-service?service=INVRPT>

En la sección de reportes (inicialmente ventas):

Detectar tabla con múltiples filas

Localizar botones de descarga en cada fila

Descargar automáticamente cada archivo

Guardarlos con nombre estructurado

🧠 Stack tecnológico

Python 3.10

Playwright (modo sync)

Automatización con Chromium

Manejo de descargas con context = browser.new_context(accept_downloads=True)

Uso de wait_for_selector en lugar de wait_for_url porque la aplicación es SPA (Angular)

⚠️ Consideraciones técnicas

La plataforma es SPA (Angular)

No siempre dispara navegación tradicional

Se debe usar detección por elementos visibles

Puede aparecer modal de sesión activa

Puede requerir reintentos y refresh

Puede tener reCAPTCHA invisible

📌 Estado actual

El login está implementado con:

Detección de texto "Tus servicios"

Manejo de botón "Continuar"

Lógica de reintentos

Refresh automático

Captura de screenshot final

Ahora se está trabajando en:
👉 Automatización de descarga masiva de reportes de ventas.

🎯 Lo que se necesita ahora

Diseñar la lógica más robusta posible para:

Detectar filas dinámicas

Manejar paginación si existe

Descargar múltiples archivos

Evitar errores por tiempo de carga

Manejar posibles nuevas pestañas

Optimizar estabilidad del scraper
