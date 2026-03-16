"""
🌐 API PRINCIPAL FASTAPI
Servidor REST para Odoo 14 integration
Expone endpoints para VENTAS e INVENTARIO
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from contextlib import asynccontextmanager
from pathlib import Path
import logging
from typing import Optional, List
from datetime import datetime, timedelta

# Importar modelos y utilidades
from sqlalchemy.orm import Session
import sys

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    DATABASE_URL, API_HOST, API_PORT, ENVIRONMENT, DEBUG,
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    ODOO_API_USER, ODOO_API_PASSWORD
)
from src.models import Base, crear_todas_tablas
from src.models.database import SessionLocal, engine
from src.processor import ReporteDetector, TipoReporte, ExcelParserVentas, ExcelParserInventario
from src.config import DESCARGAS_VENTAS_DIR, DESCARGAS_INVENTARIO_DIR

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# ============================================================================
# LIFESPAN (Startup/Shutdown)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona inicio y cierre de aplicación"""
    
    # Startup
    logger.info(f"🚀 Iniciando API (env={ENVIRONMENT})")
    logger.info(f"📊 BD: {DATABASE_URL[:50]}...")
    logger.info(f"🌐 http://{API_HOST}:{API_PORT}")
    
    # Asegurar tablas
    crear_todas_tablas(engine)
    
    yield
    
    # Shutdown
    logger.info("🛑 Cerrando API")
    engine.dispose()

# ============================================================================
# APP FASTAPI
# ============================================================================

app = FastAPI(
    title="CARVAJAL VENTAS API",
    description="Procesamiento automático de reportes VENTAS e INVENTARIO para Odoo 14",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Validar que sea el usuario de Odoo configurado
    if username != ODOO_API_USER:
        raise credentials_exception
        
    return username

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/login", tags=["Auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint para obtener token JWT. 
    Se debe enviar username y password en el cuerpo (form-data).
    """
    # Validar credenciales contra variables de entorno
    if form_data.username != ODOO_API_USER or form_data.password != ODOO_API_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ============================================================================
# DEPENDENCY: Database Session
# ============================================================================

def get_db():
    """Dependency para obtener sesión de BD"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """Verifica estado de la API y conexión a BD"""
    
    try:
        # Verificar BD
        db.execute("SELECT 1")
        db_status = "✅ OK"
    except Exception as e:
        db_status = f"❌ Error: {str(e)}"
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "✅ HEALTHY",
            "timestamp": datetime.now().isoformat(),
            "environment": ENVIRONMENT,
            "database": db_status,
            "api_version": "0.1.0"
        }
    )

# ============================================================================
# INFO
# ============================================================================

@app.get("/", tags=["Info"])
async def raiz():
    """Información principal de la API"""
    
    return JSONResponse(
        status_code=200,
        content={
            "nombre": "CARVAJAL VENTAS API",
            "version": "0.1.0",
            "descripcion": "Procesamiento automatizado de reportes",
            "endpoints": {
                "info": "/docs",
                "health": "/health",
                "ventas": "/api/v1/ventas/{endpoint}",
                "inventario": "/api/v1/inventario/{endpoint}"
            }
        }
    )

# ============================================================================
# ENDPOINTS VENTAS
# ============================================================================

@app.post("/api/v1/ventas/procesar", tags=["VENTAS"])
async def procesar_ventas(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Procesa un reporte de VENTAS
    Valida, extrae datos y almacena en BD
    """
    
    logger.info(f"📥 Recibiendo VENTAS: {file.filename}")
    
    try:
        # Guardar archivo temporalmente
        temp_path = Path(f"/tmp/{file.filename}")
        contents = await file.read()
        
        with open(temp_path, 'wb') as f:
            f.write(contents)
        
        # Procesar
        with ExcelParserVentas(temp_path) as parser:
            resultado = parser.procesar()
        
        # Limpiar
        temp_path.unlink()
        
        if not resultado['valido']:
            raise HTTPException(
                status_code=400,
                detail=f"Validación fallida: {resultado.get('errores', [])}"
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "✅ PROCESADO",
                "tipo": "VENTAS",
                "archivo": resultado['metadata'].archivo,
                "resumen": {
                    "filas": resultado['resumen']['total_filas'],
                    "total_dinero": resultado['resumen']['total_dinero'],
                    "total_cantidad": resultado['resumen']['total_cantidad'],
                }
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error procesando VENTAS: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ventas/registros", tags=["VENTAS"])
async def obtener_registros_ventas(
    limit: Optional[int] = None, 
    skip: int = 0, 
    fecha: str = None,
    id_informe: str = None,
    proveedor: str = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Obtiene todos los registros de VENTAS con todas sus columnas abreviadas.
    Permite filtrar por fecha, id_informe y proveedor.
    Retorna metadatos de paginación y la lista de registros.
    """
    from src.models import ReporteVentasDetalle, ReporteVentasCabecera
    
    try:
        query = db.query(ReporteVentasDetalle).join(ReporteVentasCabecera)
        
        if fecha:
            query = query.filter(ReporteVentasDetalle.fecha_inicial == fecha)
        if id_informe:
            query = query.filter(ReporteVentasCabecera.id_informe == id_informe)
        if proveedor:
            query = query.filter(ReporteVentasCabecera.proveedor.ilike(f"%{proveedor}%"))
            
        # Obtener total antes de aplicar offset/limit
        total = query.count()
        
        # Aplicar paginación solo si se solicita
        query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)
            
        registros = query.all()
        
        # Mapeo a nombres abreviados
        datos = []
        for r in registros:
            datos.append({
                "id": r.id,
                "id_informe": r.cabecera.id_informe,
                "proveedor": r.cabecera.proveedor,
                "punto_venta_ean": r.punto_venta_ean,
                "punto_venta": r.punto_venta_nombre,
                "codigo_almacen": r.codigo_almacen,
                "fecha_inicial": r.fecha_inicial,
                "fecha_final": r.fecha_final,
                "item_ean": r.item_ean,
                "item_descripcion": r.item_descripcion,
                "cantidad": r.cantidad_vendida,
                "unidad": r.unidad_medida,
                "precio_neto": r.precio_neto,
                "total_neto": r.total_neto,
                "precio_sin_impuestos": r.precio_sin_impuestos
            })
            
        return {
            "total": total,
            "limit": limit,
            "skip": skip,
            "registros": datos
        }
    except Exception as e:
        logger.error(f"❌ Error obteniendo registros VENTAS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ventas/resumen", tags=["VENTAS"])
async def obtener_resumen_ventas(db: Session = Depends(get_db)):
    """Obtiene resumen agregado de todas las VENTAS procesadas"""
    
    from src.models import ReporteVentasResumenDiario
    
    try:
        resumen = db.query(ReporteVentasResumenDiario).order_by(
            ReporteVentasResumenDiario.fecha_resumen.desc()
        ).first()
        
        if not resumen:
            return JSONResponse(
                status_code=200,
                content={"estado": "Sin datos", "total_filas": 0}
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "fecha": str(resumen.fecha_resumen),
                "total_cantidad_acumulada": resumen.total_cantidad_acumulada,
                "total_dinero_acumulado": resumen.total_dinero_acumulado,
                "transacciones": resumen.cantidad_transacciones,
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo resumen VENTAS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINTS INVENTARIO
# ============================================================================

@app.post("/api/v1/inventario/procesar", tags=["INVENTARIO"])
async def procesar_inventario(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Procesa un reporte de INVENTARIO
    Valida, extrae datos y almacena como snapshot en BD
    """
    
    logger.info(f"📥 Recibiendo INVENTARIO: {file.filename}")
    
    try:
        # Guardar archivo temporalmente
        temp_path = Path(f"/tmp/{file.filename}")
        contents = await file.read()
        
        with open(temp_path, 'wb') as f:
            f.write(contents)
        
        # Procesar
        with ExcelParserInventario(temp_path) as parser:
            resultado = parser.procesar()
        
        # Limpiar
        temp_path.unlink()
        
        if not resultado['valido']:
            raise HTTPException(
                status_code=400,
                detail=f"Validación fallida: {resultado.get('errores', [])}"
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "✅ PROCESADO",
                "tipo": "INVENTARIO",
                "archivo": resultado['metadata'].archivo,
                "resumen": {
                    "filas": resultado['resumen']['total_filas'],
                    "items_unicos": resultado['resumen']['total_items_unicos'],
                    "lugares_unicos": resultado['resumen']['total_lugares_unicos'],
                    "cantidad_total": resultado['resumen']['cantidad_total_fisica'],
                    "items_con_diferencia": resultado['resumen']['items_con_diferencia'],
                }
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error procesando INVENTARIO: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/inventario/registros", tags=["INVENTARIO"])
async def obtener_registros_inventario(
    limit: Optional[int] = None, 
    skip: int = 0, 
    fecha: str = None,
    id_informe: str = None,
    tienda: str = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Obtiene todos los registros de INVENTARIO con todas sus columnas abreviadas.
    Permite filtrar por fecha, id_informe y tienda.
    Retorna metadatos de paginación y la lista de registros.
    """
    from src.models import ReporteInventarioDetalle, ReporteInventarioCabecera
    
    try:
        query = db.query(ReporteInventarioDetalle).join(ReporteInventarioCabecera)
        
        if fecha:
            query = query.filter(ReporteInventarioDetalle.fecha_inventario == fecha)
        if id_informe:
            query = query.filter(ReporteInventarioCabecera.id_informe == id_informe)
        if tienda:
            query = query.filter(ReporteInventarioDetalle.nombre_lugar.ilike(f"%{tienda}%"))
            
        # Obtener total antes de aplicar offset/limit
        total = query.count()
        
        # Aplicar paginación solo si se solicita
        query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)
            
        registros = query.all()
        
        # Mapeo a nombres abreviados
        datos = []
        for r in registros:
            datos.append({
                "id": r.id,
                "id_informe": r.cabecera.id_informe,
                "emisor": r.cabecera.emisor,
                "item_ean": r.item_ean,
                "item_descripcion": r.item_descripcion,
                "codigo_almacen": r.codigo_almacen,
                "cantidad": r.cantidad,
                "codigo_lugar": r.codigo_lugar,
                "nombre_lugar": r.nombre_lugar,
                "item_codigo_comprador": r.item_codigo_comprador,
                "precio_lista": r.precio_lista,
                "precio_neto": r.precio_neto,
                "total_neto": r.total_neto,
                "fecha_inventario": r.fecha_inventario
            })
            
        return {
            "total": total,
            "limit": limit,
            "skip": skip,
            "registros": datos
        }
    except Exception as e:
        logger.error(f"❌ Error obteniendo registros INVENTARIO: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/inventario/stock/{ean}", tags=["INVENTARIO"])
async def obtener_stock_ean(ean: str, db: Session = Depends(get_db)):
    """Obtiene stock actual de un EAN en todos los lugares"""
    
    from src.models import ReporteInventarioResumenDiario
    
    try:
        stocks = db.query(ReporteInventarioResumenDiario).filter(
            ReporteInventarioResumenDiario.item_ean == ean
        ).order_by(
            ReporteInventarioResumenDiario.fecha_inventario.desc()
        ).all()
        
        if not stocks:
            return JSONResponse(
                status_code=404,
                content={"error": "EAN no encontrado"}
            )
        
        resultado = [
            {
                "fecha": str(stock.fecha_inventario),
                "lugar": stock.codigo_lugar,
                "cantidad": stock.cantidad_fisica,
            }
            for stock in stocks[:10]  # Últimos 10
        ]
        
        return JSONResponse(
            status_code=200,
            content={
                "ean": ean,
                "historico": resultado
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo stock: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Manejador personalizado para HTTPExceptions"""
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        reload=DEBUG,
        log_level="info" if not DEBUG else "debug"
    )
