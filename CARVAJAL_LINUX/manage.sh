#!/bin/bash
# ============================================================================
# CARVAJAL VENTAS - Script Helper para Docker Compose en Rocky Linux
# ============================================================================
# Uso: ./manage.sh [comando]
# Ejemplo: ./manage.sh up
#          ./manage.sh logs downloader
#          ./manage.sh ps
#          ./manage.sh restart

set -e

# Colors para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.yml no encontrado${NC}"
    echo "Debes ejecutar este script desde /opt/carvajal"
    exit 1
fi

# Verificar que el archivo .env existe
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env no encontrado${NC}"
    echo "Debes copiar .env.docker.prod a .env"
    exit 1
fi

# Comando a ejecutar
COMMAND="${1:-help}"

# Funciones
show_help() {
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}CARVAJAL VENTAS - Docker Compose Management${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo -e "${YELLOW}Comandos disponibles:${NC}"
    echo "  up              - Inicia todos los servicios"
    echo "  down            - Detiene todos los servicios"
    echo "  ps              - Muestra el estado de los servicios"
    echo "  logs            - Muestra logs de todos los servicios (tail -f)"
    echo "  logs:app        - Logs de la API"
    echo "  logs:downloader - Logs del scheduler de descarga"
    echo "  logs:db         - Logs de la base de datos"
    echo "  restart         - Reinicia todos los servicios"
    echo "  restart:app     - Reinicia solo la API"
    echo "  restart:downloader - Reinicia solo el downloader"
    echo "  rebuild         - Reconstruye las imágenes Docker"
    echo "  shell:app       - Abre una shell en el contenedor app"
    echo "  shell:downloader - Abre una shell en el contenedor downloader"
    echo "  db              - Conecta a PostgreSQL (psql)"
    echo "  prune           - Limpia contenedores y volúmenes no usados"
    echo "  status          - Status detallado de los servicios"
    echo "  health          - Verifica salud de los servicios"
    echo "  help            - Muestra este mensaje"
    echo ""
    echo -e "${YELLOW}Ejemplos:${NC}"
    echo "  $0 up"
    echo "  $0 logs:downloader"
    echo "  $0 restart:app"
    echo ""
}

up_services() {
    echo -e "${GREEN}🚀 Iniciando servicios...${NC}"
    docker-compose up -d
    sleep 3
    echo ""
    status_services
}

down_services() {
    echo -e "${YELLOW}⏹️  Deteniendo servicios...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Servicios detenidos${NC}"
}

status_services() {
    echo -e "${BLUE}📊 Estado de los servicios:${NC}"
    docker-compose ps
}

view_logs() {
    local service="${1:-}"
    if [ -z "$service" ]; then
        echo -e "${BLUE}📋 Logs de todos los servicios:${NC}"
        docker-compose logs -f
    else
        echo -e "${BLUE}📋 Logs de $service:${NC}"
        docker-compose logs -f "$service"
    fi
}

restart_services() {
    local service="${1:-}"
    if [ -z "$service" ]; then
        echo -e "${YELLOW}🔄 Reiniciando todos los servicios...${NC}"
        docker-compose restart
    else
        echo -e "${YELLOW}🔄 Reiniciando $service...${NC}"
        docker-compose restart "$service"
    fi
    sleep 2
    echo ""
    status_services
}

rebuild_images() {
    echo -e "${YELLOW}🔨 Reconstruyendo imágenes...${NC}"
    docker-compose down
    docker-compose build --no-cache
    echo ""
    up_services
}

enter_shell() {
    local service="${1:-app}"
    echo -e "${BLUE}🔌 Abriendo shell en $service...${NC}"
    docker-compose exec "$service" /bin/sh
}

connect_db() {
    echo -e "${BLUE}🗄️  Conectando a PostgreSQL...${NC}"
    docker-compose exec postgres psql -U carvajal_user -d carvajal_reportes
}

prune_docker() {
    echo -e "${YELLOW}🧹 Limpiando Docker (contenedores, imágenes, volúmenes no usados)...${NC}"
    docker system prune -a -f
    echo -e "${GREEN}✅ Limpieza completada${NC}"
}

health_check() {
    echo -e "${BLUE}🏥 Verificando salud de los servicios...${NC}"
    echo ""
    
    echo -n "PostgreSQL: "
    if docker-compose exec postgres pg_isready -U carvajal_user &>/dev/null; then
        echo -e "${GREEN}✅ Healthy${NC}"
    else
        echo -e "${RED}❌ Unhealthy${NC}"
    fi
    
    echo -n "API (port 10000): "
    if curl -f -s http://localhost:10000/health &>/dev/null; then
        echo -e "${GREEN}✅ Healthy${NC}"
    else
        echo -e "${RED}❌ Unhealthy${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}Estado de los contenedores:${NC}"
    docker-compose ps
}

# Ejecutar comando
case "$COMMAND" in
    up)
        up_services
        ;;
    down)
        down_services
        ;;
    ps|status)
        status_services
        ;;
    logs)
        view_logs
        ;;
    logs:app)
        view_logs app
        ;;
    logs:downloader)
        view_logs downloader
        ;;
    logs:db|logs:postgres)
        view_logs postgres
        ;;
    restart)
        restart_services
        ;;
    restart:app)
        restart_services app
        ;;
    restart:downloader)
        restart_services downloader
        ;;
    restart:db|restart:postgres)
        restart_services postgres
        ;;
    rebuild)
        rebuild_images
        ;;
    shell:app)
        enter_shell app
        ;;
    shell:downloader)
        enter_shell downloader
        ;;
    db)
        connect_db
        ;;
    prune)
        prune_docker
        ;;
    health)
        health_check
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Comando desconocido: $COMMAND${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
