# 🔧 SOLUCIÓN: Error del Servicio Downloader en Rocky Linux

## 📋 Problemas Identificados

1. **Servicio `downloader` en estado `Restarting` (exit code 2)**
2. **Variables de entorno no configuradas** - faltaba `.env.docker.prod`
3. **Atributo `version` obsoleto en docker-compose.yml**
4. **Archivo `notificaciones.py` con credenciales hardcodeadas**

## ✅ Cambios Realizados

### 1. Creado archivo `.env.docker.prod`
- Archivo de configuración específico para Rocky Linux
- Contiene todas las variables requeridas por Docker
- Ubicación: `/opt/carvajal/.env.docker.prod`

### 2. Actualizado `docker-compose.yml`
- Removida la línea `version: "3.8"` (obsoleta en Docker 20.10+)
- Mantiene funcionalidad idéntica

### 3. Actualizado `notificaciones.py`
- Ahora usa `os.getenv()` para leer variables de entorno
- Eliminadas credenciales hardcodeadas
- Las credenciales se pasan desde `.env.docker.prod`

---

## 🚀 INSTRUCCIONES PARA ROCKY LINUX

### Paso 1: Copiar el archivo .env.docker.prod
```bash
# En tu máquina local:
# Copia el archivo .env.docker.prod a Rocky Linux

scp .env.docker.prod root@[IP_ROCKY]:/opt/carvajal/
```

### Paso 2: Copiar notificaciones.py actualizado
```bash
scp notificaciones.py root@[IP_ROCKY]:/opt/carvajal/
```

### Paso 3: Copiar docker-compose.yml actualizado
```bash
scp docker-compose.yml root@[IP_ROCKY]:/opt/carvajal/
```

### Paso 4: Detener los contenedores actuales
```bash
cd /opt/carvajal
docker-compose down
```

### Paso 5: Ejecutar con el nuevo archivo .env
```bash
docker-compose --env-file .env.docker.prod up -d
```

### Paso 6: Verificar estado
```bash
# Ver estatus de los servicios
docker-compose ps

# Ver logs del downloader
docker-compose logs downloader

# Ver logs de la app
docker-compose logs app
```

---

## 🔍 DIAGNÓSTICO DEL DOWNLOADER

Si el downloader sigue fallando, ejecuta el script de debug:

### En tu máquina local:
```bash
python debug_downloader.py
```

Este script verificará:
- ✅ Variables de entorno configuradas
- ✅ Directorios existen
- ✅ Dependencias Python instaladas
- ✅ Conexión a base de datos
- ✅ Imports del scheduler

---

## 🐛 Problemas Comunes y Soluciones

### Error: "PASSWORD_CORREO variable is not set"
**Solución:** Asegúrate que el archivo `.env.docker.prod` está en `/opt/carvajal/` y contiene la línea:
```
PASSWORD_CORREO=muaebnciwfmoelgl
```

### Error: "Restarting (2)"
**Solución:** Revisa los logs:
```bash
docker-compose logs --tail 50 downloader
```

El exit code 2 puede deberse a:
1. Módulo Python no encontrado (ImportError)
2. Error en la inicialización de APScheduler
3. Error de conectividad con PostgreSQL
4. Error en las funciones de notificación

### Error: "connection refused postgres"
**Solución:** Verifica que PostgreSQL está healthy:
```bash
docker-compose ps | grep postgres
```

Debe mostrar: `Healthy` en la columna STATUS

---

## 📝 Verificación Final

Una vez que todo esté funcionando:

```bash
# 1. Verificar que todos los servicios están corriendo
docker-compose ps
# Debería mostrar:
# - postgres: Up (health: healthy)
# - app: Up
# - downloader: Up

# 2. Probar conectividad a la API
curl http://localhost:10000/health

# 3. Ver logs del scheduler
docker-compose logs downloader | tail -20

# 4. Logs de la app
docker-compose logs app | tail -20
```

---

## 🎯 Próximos Pasos

1. **Deploy en Rocky Linux:** Copia los 3 archivos actualizados
2. **Reinicia Docker:** `docker-compose down && docker-compose --env-file .env.docker.prod up -d`
3. **Monitorea:** `docker-compose logs -f`
4. **Valida:** Verifica que no hay errores en downloader después de 30 segundos

---

## 📞 Soporte

Si sigue habiendo problemas:

1. Ejecuta: `docker-compose logs downloader --tail 100`
2. Ejecuta: `python debug_downloader.py` (localmente)
3. Comparte los logs completos para análisis detallado

---

**Fecha de Actualización:** 6 de marzo de 2026  
**Versión Docker Compose:** 2.0+
