-- ============================================================================
-- CARVAJAL VENTAS - Script de inicialización de PostgreSQL
-- ============================================================================
-- Este script se ejecuta DESPUÉS de que Docker crea la base de datos y el 
-- usuario configurados en las variables de entorno (POSTGRES_DB y USER).

-- 1. Asegurar que el usuario de la aplicación sea dueño del esquema público.
-- Esto es crítico en PostgreSQL 15+ para permitir la creación de tablas por la app.
ALTER SCHEMA public OWNER TO carvajal_user;

-- 2. Otorgar todos los privilegios sobre el esquema.
GRANT ALL PRIVILEGES ON SCHEMA public TO carvajal_user;

-- 3. Mensaje de éxito para los logs de inicialización.
SELECT '✅ Configuración de permisos de esquema completada' as status;
