# 🐳 DOCKER - CARVAJAL VENTAS (v1.2.0)

## Estructura de Servicios

El sistema se compone de 3 servicios principales en Docker:
1. **`carvajal_postgres`**: Base de datos PostgreSQL 15.
2. **`carvajal_app`**: API REST FastAPI (Puerto 10000).
3. **`carvajal_downloader`**: Procesador continuo de archivos Excel.

## Inicio Rápido en Rocky Linux

### Paso 1: Configurar .env

Asegúrate de tener un archivo `.env` en la raíz con las credenciales de la base de datos:
```env
POSTGRES_USER=carvajal_user
POSTGRES_PASSWORD=tu_password
POSTGRES_DB=carvajal_reportes
DATABASE_URL=postgresql://carvajal_user:tu_password@postgres:5432/carvajal_reportes
```

### Paso 2: Levantar el Sistema

```bash
# Construir y levantar todo
docker-compose up -d --build
```

### Paso 3: Verificación

```bash
# Ver que los contenedores estén Up
docker-compose ps

# Ver logs del procesador (Downloader)
docker-compose logs -f downloader

# Ver logs de la API
docker-compose logs -f app
```

---

## Mantenimiento y Debugging

### Limpiar Datos y Reiniciar (Reset Completo)
Si cambias la estructura de las tablas o quieres procesar todo desde cero:
```bash
docker-compose down -v
docker-compose up -d --build
```

### Acceso a Base de Datos
```bash
# Entrar a la consola de Postgres
docker exec -it carvajal_postgres psql -U carvajal_user -d carvajal_reportes

# Ver cantidad de registros insertados
SELECT COUNT(*) FROM reporte_ventas_detalle;
SELECT COUNT(*) FROM reporte_inventario_detalle;
```

---

## Estructura de Carpetas y Volúmenes

El sistema mapea las carpetas del servidor Rocky Linux hacia el contenedor para persistencia:

| Carpeta Host | Carpeta Contenedor | Propósito |
| :--- | :--- | :--- |
| `./data/descargas_ventas` | `/app/data/descargas_ventas` | Entrada de Excels de Ventas |
| `./data/descargas_inventario` | `/app/data/descargas_inventario` | Entrada de Excels de Inventario |
| `./data/procesados_ventas` | `/app/data/procesados_ventas` | Histórico de Ventas ya cargadas |
| `./data/procesados_inventario` | `/app/data/procesados_inventario` | Histórico de Inventario ya cargado |
| `./logs` | `/app/logs` | Logs de errores y procesamiento |

---

## API Documentation
Una vez levantado, puedes acceder a la documentación interactiva en:
`http://[IP_SERVIDOR]:10000/docs`

---
**Versión**: 1.2.0  
**Entorno Recomendado**: Docker 24+ / Docker Compose 2.20+

# Posible solución: resetear volumen
docker-compose down -v
docker-compose up -d
```

### API no conecta a BD

```bash
# Verificar conectividad
docker-compose exec app ping postgres

# Ver variables de entorno
docker-compose exec app env | grep DATABASE
```

### Permisos de archivos

```bash
# Fijar permisos en el host
chmod 755 descargas_reportes procesados_* logs_reportes backups
```

### Puerto 5432 ya en uso

```bash
# Cambiar puerto en docker-compose.yml o en la línea de comandos
docker-compose -C POSTGRES_PORT=5433 up -d

# O matar proceso que usa el puerto
sudo lsof -i :5432
sudo kill -9 <PID>
```

---

## Deployment en Producción

### Opción 1: Docker Swarm

```bash
docker swarm init
docker stack deploy -c docker-compose.yml carvajal
```

### Opción 2: Kubernetes

```bash
kompose convert -f docker-compose.yml -o k8s/
kubectl apply -f k8s/
```

### Opción 3: Cloud (AWS ECS, Google Cloud Run)

Contactar con el equipo de DevOps

---

## Backups Automáticos

### Script de backup diario

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/carvajal_$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR

docker-compose exec -T postgres pg_dump -U carvajal_user carvajal_reportes > $BACKUP_FILE

# Comprimir
gzip $BACKUP_FILE

# Eliminar backups más antiguos de 30 días
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "✅ Backup completado: $BACKUP_FILE.gz"
```

Agregar a crontab:
```bash
0 2 * * * cd /path/to/carvajal && bash backup.sh
```

---

## Referencias

- 📚 [Docker Compose Documentation](https://docs.docker.com/compose/)
- 📚 [PostgreSQL in Docker](https://hub.docker.com/_/postgres)
- 📚 [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- 📚 [SQLAlchemy con PostgreSQL](https://docs.sqlalchemy.org/en/20/)

---

## Soporte

Para ayuda: soporte@dismelltda.com
