#!/bin/bash

# ============================================================================
# CARVAJAL VENTAS - Setup Script para Rocky Linux (PRODUCCIÓN)
# ============================================================================
# Este script prepara el entorno en el servidor
# Uso: sudo bash setup_servidor.sh

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# ============================================================================
# FUNCIONES
# ============================================================================

check_docker() {
    print_header "Verificando Docker"
    
    if command -v docker &> /dev/null; then
        print_success "Docker instalado: $(docker --version)"
    else
        print_error "Docker no está instalado"
        print_warning "Instala Docker: sudo dnf install -y docker"
        exit 1
    fi
    
    if command -v docker-compose &> /dev/null; then
        print_success "docker-compose instalado: $(docker-compose --version)"
    elif docker compose version &> /dev/null; then
        print_success "docker compose (nuevo) disponible"
    else
        print_warning "docker-compose no disponible, pero puede funcionar con 'docker compose'"
    fi
}

create_directories() {
    print_header "Creando estructura de directorios"
    
    local dirs=(
        "descargas_reportes/ventas"
        "descargas_reportes/inventario"
        "procesados_ventas"
        "procesados_inventario"
        "logs_reportes"
        "backups"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Creado: $dir"
        else
            print_warning "Existe: $dir"
        fi
    done
}

set_permissions() {
    print_header "Configurando permisos"
    
    local dirs=(
        "descargas_reportes"
        "procesados_ventas"
        "procesados_inventario"
        "logs_reportes"
        "backups"
    )
    
    for dir in "${dirs[@]}"; do
        chmod 755 "$dir"
        print_success "Permisos configurados: $dir (755)"
    done
    
    # Archivo .env.docker.prod debe ser restrictivo
    if [ -f ".env.docker.prod" ]; then
        chmod 600 .env.docker.prod
        print_success "Permisos .env.docker.prod (600 - solo lectura propietario)"
    fi
}

verify_files() {
    print_header "Verificando archivos críticos"
    
    local files=(
        "docker-compose.yml"
        "Dockerfile"
        "requirements.txt"
        ".env.docker"
        "init_db.py"
        "run_api.py"
        "src/config.py"
        "src/api/main.py"
        "src/models/schema.py"
    )
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            print_success "Existe: $file"
        else
            print_error "FALTA: $file"
        fi
    done
}

create_env_prod() {
    print_header "Preparando configuración de producción"
    
    if [ -f ".env.docker.prod" ]; then
        print_warning ".env.docker.prod ya existe"
        read -p "¿Sobrescribir? (s/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            print_warning "Usando archivo existente de configuración"
            return
        fi
    fi
    
    if [ -f ".env.docker" ]; then
        cp .env.docker .env.docker.prod
        print_success "Archivo .env.docker.prod creado (copia de .env.docker)"
        print_warning "⚠️  EDITA ahora las credenciales reales:"
        print_warning "   nano .env.docker.prod"
    else
        print_error "No encontrado: .env.docker"
    fi
}

fix_line_endings() {
    print_header "Corrigiendo line endings (CRLF → LF)"
    
    if command -v dos2unix &> /dev/null; then
        for file in docker-help.sh init_db.py run_api.py; do
            if [ -f "$file" ]; then
                dos2unix "$file" 2>/dev/null
                chmod +x "$file"
                print_success "Convertido y ejecutable: $file"
            fi
        done
    else
        print_warning "dos2unix no instalado, saltando conversión"
        print_warning "Puedes instalar: sudo dnf install -y dos2unix"
        for file in docker-help.sh init_db.py run_api.py; do
            if [ -f "$file" ]; then
                chmod +x "$file"
                print_success "Marcado ejecutable: $file"
            fi
        done
    fi
}

setup_docker_network() {
    print_header "Configurando red Docker"
    
    if docker network inspect carvajal_network &>/dev/null; then
        print_success "Red 'carvajal_network' ya existe"
    else
        docker network create carvajal_network
        print_success "Red 'carvajal_network' creada"
    fi
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    print_header "SETUP CARVAJAL VENTAS - ROCKY LINUX"
    
    # Verificar que se ejecuta como directorio correcto
    if [ ! -f "docker-compose.yml" ]; then
        print_error "No estás en el directorio correcto"
        print_warning "Ejecuta desde: /opt/carvajal (o donde descargaste el proyecto)"
        exit 1
    fi
    
    # Verificar si es root (recomendado pero no obligatorio)
    if [ "$EUID" -ne 0 ]; then
        print_warning "Ejecutando como usuario normal (es mejor con sudo)"
    fi
    
    # Ejecutar verificaciones
    check_docker
    verify_files
    create_directories
    set_permissions
    fix_line_endings
    setup_docker_network
    create_env_prod
    
    echo
    print_header "SETUP COMPLETADO ✅"
    echo
    echo -e "${GREEN}Próximos pasos:${NC}"
    echo "1. Editar credenciales:"
    echo "   nano .env.docker.prod"
    echo
    echo "2. Empezar servicios:"
    echo "   docker-compose --env-file .env.docker.prod up -d"
    echo
    echo "3. Ver estado:"
    echo "   docker-compose ps"
    echo
    echo "4. Ver logs:"
    echo "   docker-compose logs -f app"
    echo
    echo -e "${YELLOW}Documentación: Lee DOCKER.md para más comandos${NC}"
    echo
}

# Ejecutar
main "$@"
