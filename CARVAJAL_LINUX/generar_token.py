#!/usr/bin/env python3
"""
🔑 GENERADOR DE TOKEN PARA PRUEBAS (API CARVAJAL)
Este script simula el proceso de login y genera un token JWT
para ser usado en las peticiones GET de la API.
"""

import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables desde .env si existe en el directorio actual
load_dotenv()

# =============================================================
# CONFIGURACIÓN (Ajustar si es necesario)
# =============================================================
BASE_URL = "http://192.168.1.254:10000"  # Cambiar por localhost si se corre local
AUTH_ENDPOINT = "/api/v1/auth/login"

# Credenciales por defecto (deben coincidir con .env)
USERNAME = os.getenv('ODOO_API_USER', 'odoo_integration')
PASSWORD = os.getenv('ODOO_API_PASSWORD', 'C@rvaj@l_Odoo_2026')

def generar_token():
    print(f"\n🔐 Intentando obtener token para el usuario: {USERNAME}")
    
    url = f"{BASE_URL}{AUTH_ENDPOINT}"
    
    # Datos en formato Form-Data (OAuth2 requiere esto)
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        # Realizar la petición POST
        response = requests.post(url, data=data)
        
        # Verificar si la petición fue exitosa
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            
            print("\n✅ ¡Token generado exitosamente!")
            print("-" * 60)
            print(f"TOKEN:\n{token}")
            print("-" * 60)
            print("\n💡 Instrucciones de uso en Postman:")
            print("1. Copia el token de arriba.")
            print("2. En tu petición GET, ve a la pestaña 'Authorization'.")
            print("3. Selecciona 'Bearer Token'.")
            print("4. Pega el token y listo.")
            
            # Guardar el token en un archivo temporal por si se necesita
            with open("token_actual.txt", "w") as f:
                f.write(token)
            print(f"\n📁 El token también se ha guardado en: {os.path.abspath('token_actual.txt')}")
            
        else:
            print(f"\n❌ Error al generar el token (Código: {response.status_code})")
            print(f"Detalle: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error de conexión: No se pudo contactar con {BASE_URL}")
        print("Asegúrate de que el servidor Docker esté corriendo y la IP sea correcta.")
    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado: {str(e)}")

if __name__ == "__main__":
    generar_token()
