#!/bin/bash

# ============================================================================
# CARVAJAL VENTAS - Docker Helper Script
# Facilita la ejecución de comandos Docker comunes
# ============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Funciones Auxiliares
# ============================================================================

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ============================================================================
# Comandos
# ============================================================================

cmd_help() {
    cat << 'EOF'
CARVAJAL VENTAS - Docker Helper

USO:
    ./docker-help.sh <comando> [opciones]

COMANDOS:
    up              Iniciar servicios
    down            Detener servicios
    restart         Reiniciar servicios
    logs            Ver logs (todos)
    logs-app        Ver logs de la aplicación
    logs-db         Ver logs de PostgreSQL
    status          Ver estado de servicios
    shell-app       Entrar al contenedor de la app
    shell-db        Entrar a PostgreSQL interactivamente
    backup          Hacer backup de la BD
    restore <file>  Restaurar backup
    clean           Eliminar volúmenes (⚠️ DESTRUCTIVO)
    test            Ejecutar pruebas
    help            Mostrar esta ayuda

EJEMPLOS:
    ./docker-help.sh up
    ./docker-help.sh logs -f
    ./docker-help.sh shell-app
    ./docker-help.sh backup
    ./docker-help.sh restore backup.sql.gz

EOF
}

cmd_up() {
    print_header "Iniciando servicios de Docker"
    
    # Verificar si existe archivo .env
    if [ ! -f ".env.docker.prod" ] && [ ! -f ".env.docker" ]; then
        print_error ".env.docker no encontrado"
        print_warning "Ejecuta primero: cp .env.docker .env.docker.prod && nano .env.docker.prod"
        exit 1
    fi
    
    ENV_FILE=.env.docker.prod
    if [ ! -f "$ENV_FILE" ]; then
        ENV_FILE=.env.docker
    fi
    
    print_info "Usando archivo: $ENV_FILE"
    
    docker-compose --env-file "$ENV_FILE" up -d
    
    print_success "Servicios iniciados"
    print_info "Espera 30 segundos para que PostgreSQL seleccione..."
    sleep 10
    print_info "Continuando..."
    
    echo
    print_header "Estado"
    docker-compose ps
}

cmd_down() {
    print_header "Deteniendo servicios"
    docker-compose down
    print_success "Servicios detenidos"
}

cmd_restart() {
    print_header "Reiniciando servicios"
    docker-compose restart
    print_success "Servicios reiniciados"
}

cmd_logs() {
    print_header "Logs de todos los servicios"
    docker-compose logs -f
}

cmd_logs_app() {
    print_header "Logs de la aplicación"
    docker-compose logs -f app
}

cmd_logs_db() {
    print_header "Logs de PostgreSQL"
    docker-compose logs -f postgres
}

cmd_status() {
    print_header "Estado de servicios"
    docker-compose ps
    
    echo
    print_info "Health Checks:"
    echo
    
    # App health
    if docker inspect --format='{{json .State.Health.Status}}' carvajal_app 2>/dev/null | grep -q "healthy"; then
        print_success "App: HEALTHY"
    else
        print_error "App: UNHEALTHY"
    fi
    
    # DB health
    if docker inspect --format='{{json .State.Health.Status}}' carvajal_postgres 2>/dev/null | grep -q "healthy"; then
        print_success "PostgreSQL: HEALTHY"
    else
        print_error "PostgreSQL: UNHEALTHY"
    fi
}

cmd_shell_app() {
    print_header "Entrando al contenedor de la app"
    docker-compose exec app sh
}

cmd_shell_db() {
    print_header "Entrando a PostgreSQL"
    docker-compose exec postgres psql -U carvajal_user -d carvajal_reportes
}

cmd_backup() {
    print_header "Haciendo backup de PostgreSQL"
    
    mkdir -p backups
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="backups/carvajal_$TIMESTAMP.sql"
    
    print_info "Archivo de backup: $BACKUP_FILE"
    
    docker-compose exec -T postgres pg_dump -U carvajal_user carvajal_reportes > "$BACKUP_FILE"
    
    gzip "$BACKUP_FILE"
    
    print_success "Backup completado: ${BACKUP_FILE}.gz"
    ls -lh "${BACKUP_FILE}.gz"
}

cmd_restore() {
    if [ -z "$1" ]; then
        print_error "Especifica archivo de backup"
        print_info "Uso: ./docker-help.sh restore <archivo.sql.gz>"
        exit 1
    fi
    
    BACKUP_FILE=$1
    
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Archivo no encontrado: $BACKUP_FILE"
        exit 1
    fi
    
    print_header "Restaurando backup"
    print_warning "⚠️  Esto eliminará la BD actual y la reemplazará"
    read -p "¿Continuar? (s/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        # Descomprimir si es necesario
        if [[ "$BACKUP_FILE" == *.gz ]]; then
            TEMP_FILE="${BACKUP_FILE%.gz}"
            gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
            BACKUP_FILE=$TEMP_FILE
        fi
        
        print_info "Restaurando..."
        docker-compose exec -T postgres psql -U carvajal_user carvajal_reportes < "$BACKUP_FILE"
        
        # Limpiar temp si fue necesario
        if [ -n "$TEMP_FILE" ]; then
            rm "$TEMP_FILE"
        fi
        
        print_success "Backup restaurado"
    else
        print_warning "Operación cancelada"
    fi
}

cmd_clean() {
    print_header "LIMPIANDO VOLÚMENES"
    print_error "⚠️  Esto eliminará TODOS los datos (BD, logs, descargas)"
    read -p "¿Realmente quieres eliminar todo? (escribe 'si' para confirmar): " -r
    
    if [ "$REPLY" = "si" ]; then
        docker-compose down -v
        print_success "Volúmenes eliminados"
    else
        print_warning "Operación cancelada"
    fi
}

cmd_test() {
    print_header "Ejecutando pruebas"
    
    print_info "Health check de la API..."
    if curl -f http://localhost:8000/health 2>/dev/null; then
        print_success "API respondiendo"
    else
        print_error "API no responde en http://localhost:8000"
    fi
    
    echo
    print_info "Conectando a BD..."
    if docker-compose exec -T postgres pg_isready -U carvajal_user >/dev/null 2>&1; then
        print_success "PostgreSQL respondiendo"
    else
        print_error "PostgreSQL no responde"
    fi
    
    echo
    print_info "Info del API..."
    curl -s http://localhost:8000/ | python -m json.tool 2>/dev/null || echo "No JSON response"
}

# ============================================================================
# Main
# ============================================================================

main() {
    # Si no hay comando, mostrar ayuda
    if [ -z "$1" ]; then
        cmd_help
        exit 0
    fi
    
    case "$1" in
        up)
            cmd_up
            ;;
        down)
            cmd_down
            ;;
        restart)
            cmd_restart
            ;;
        logs)
            shift
            cmd_logs "$@"
            ;;
        logs-app)
            cmd_logs_app
            ;;
        logs-db)
            cmd_logs_db
            ;;
        status)
            cmd_status
            ;;
        shell-app|shell_app)
            cmd_shell_app
            ;;
        shell-db|shell_db)
            cmd_shell_db
            ;;
        backup)
            cmd_backup
            ;;
        restore)
            cmd_restore "$2"
            ;;
        clean)
            cmd_clean
            ;;
        test)
            cmd_test
            ;;
        help|-h|--help)
            cmd_help
            ;;
        *)
            print_error "Comando desconocido: $1"
            echo
            cmd_help
            exit 1
            ;;
    esac
}

# Ejecutar main
main "$@"
