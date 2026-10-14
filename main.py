#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import threading
import time
import json
import hashlib
import random
import shutil
import socket
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template, redirect
from flask_cors import CORS
import webview

# ==================== DETECTAR SISTEMA OPERATIVO ====================
IS_WINDOWS = sys.platform == 'win32'
IS_LINUX = sys.platform == 'linux' or sys.platform == 'linux2'
IS_MAC = sys.platform == 'darwin'

# ==================== CONFIGURACION DE RUTAS ====================
def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.abspath(".")

def get_data_path():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, 'data')
    return os.path.abspath(".")

# ==================== CARPETAS ====================
BASE_PATH = get_base_path()
DATA_PATH = get_data_path()

CARPETA_DATOS = os.path.join(DATA_PATH, "datos")
CARPETA_PDF_FACTURAS = os.path.join(DATA_PATH, "pdf_facturas")
CARPETA_PDF_REPORTES = os.path.join(DATA_PATH, "pdf_reportes")
CARPETA_EXCEL_REPORTES = os.path.join(DATA_PATH, "excel_reportes")
CARPETA_BACKUPS = os.path.join(DATA_PATH, "backups")
CARPETA_LOGS = os.path.join(DATA_PATH, "logs")
CARPETA_TABLAS = os.path.join(DATA_PATH, "tablas")
CARPETA_PAGINAS = os.path.join(DATA_PATH, "paginas_hijo")
CARPETA_MODULOS_PY = os.path.join(BASE_PATH, "modulos_py")
CARPETA_IMAGENES_FONDO = os.path.join(CARPETA_DATOS, "imagenes_fondo")
CARPETA_IMAGENES_TEMPLATES = os.path.join(BASE_PATH, "templates", "modulos", "Imagenes")
ARCHIVO_PERMISOS_FACTURAS = os.path.join(CARPETA_DATOS, "permisos_facturas.json")

# ==================== CARPETAS PARA GESTIÓN CLIENTES ====================
CARPETA_EXCEL_CLIENTES = os.path.join(DATA_PATH, "excel_clientes")
CARPETA_PDF_CLIENTES = os.path.join(DATA_PATH, "pdf_clientes")

for carpeta in [CARPETA_DATOS, CARPETA_PDF_FACTURAS, CARPETA_PDF_REPORTES, 
                CARPETA_EXCEL_REPORTES, CARPETA_BACKUPS, CARPETA_LOGS, 
                CARPETA_TABLAS, CARPETA_PAGINAS, CARPETA_IMAGENES_FONDO, 
                CARPETA_IMAGENES_TEMPLATES, CARPETA_EXCEL_CLIENTES, 
                CARPETA_PDF_CLIENTES]:
    Path(carpeta).mkdir(parents=True, exist_ok=True)

# Agregar modulos_py al path
if os.path.exists(CARPETA_MODULOS_PY):
    sys.path.insert(0, CARPETA_MODULOS_PY)
    print(f"[INFO] Modulos Python cargados desde: {CARPETA_MODULOS_PY}")
else:
    print(f"[WARN] Carpeta modulos_py no encontrada: {CARPETA_MODULOS_PY}")
    if os.path.exists(os.path.join(os.getcwd(), "modulos_py")):
        sys.path.insert(0, os.path.join(os.getcwd(), "modulos_py"))
        print(f"[INFO] Modulos Python cargados desde: {os.path.join(os.getcwd(), 'modulos_py')}")

# ==================== ARCHIVOS JSON ====================
ARCHIVO_EMPRESAS = os.path.join(CARPETA_DATOS, "empresas.json")
ARCHIVO_PEDIDOS = os.path.join(CARPETA_DATOS, "pedidos_combustible.json")
ARCHIVO_PEDIDOS_FACTURACION = os.path.join(CARPETA_DATOS, "pedidos_facturacion.json")
ARCHIVO_FACTURAS = os.path.join(CARPETA_DATOS, "facturas_combustible.json")
ARCHIVO_CONDUCTORES = os.path.join(CARPETA_DATOS, "conductores.json")
ARCHIVO_CAMIONES = os.path.join(CARPETA_DATOS, "camiones.json")
ARCHIVO_COSTOS_TRASLADO = os.path.join(CARPETA_DATOS, "costos_traslado.json")
ARCHIVO_USUARIOS = os.path.join(CARPETA_DATOS, "usuarios.json")
ARCHIVO_CONFIG_IA = os.path.join(CARPETA_DATOS, "config_ia.json")
ARCHIVO_CONFIG_CORREO = os.path.join(CARPETA_DATOS, "config_correo.json")
ARCHIVO_CONFIG_SISTEMA = os.path.join(CARPETA_DATOS, "config_sistema.json")
ARCHIVO_BITACORA = os.path.join(CARPETA_LOGS, "bitacora.json")
ARCHIVO_TABLAS_EDITABLES = os.path.join(CARPETA_TABLAS, "tablas_editables.json")
ARCHIVO_BITACORA_DATA = os.path.join(CARPETA_TABLAS, "bitacora_data.json")
ARCHIVO_MANTENIMIENTO = os.path.join(CARPETA_DATOS, "mantenimiento.json")
ARCHIVO_PAGINAS = os.path.join(CARPETA_DATOS, "paginas.json")
ARCHIVO_URL_PUBLICA = os.path.join(CARPETA_DATOS, "url_publica.json")
ARCHIVO_OPERACIONES = os.path.join(CARPETA_DATOS, "operaciones.json")
ARCHIVO_CONFIG_FACTURA = os.path.join(CARPETA_DATOS, "config_factura.json")
ARCHIVO_COLUMNAS_MANTENIMIENTO = os.path.join(CARPETA_DATOS, "columnas_mantenimiento.json")
ARCHIVO_REPORTES_DATA = os.path.join(CARPETA_DATOS, "reportes_data.json")
ARCHIVO_ESTADOS_FACTURAS = os.path.join(CARPETA_DATOS, "estados_facturas.json")
ARCHIVO_UBICACIONES = os.path.join(CARPETA_DATOS, "ubicaciones.json")
ARCHIVO_CONFIG_CLIENTES = os.path.join(CARPETA_DATOS, "config_clientes.json")
ARCHIVO_CLIENTES = os.path.join(CARPETA_DATOS, "clientes.json")
ARCHIVO_OBSERVACIONES = os.path.join(CARPETA_DATOS, "observaciones.json")
ARCHIVO_CHAT = os.path.join(CARPETA_DATOS, "chat_mensajes.json")
ARCHIVO_TEMAS_USUARIOS = os.path.join(CARPETA_DATOS, "temas_usuarios.json")

# ==================== VERIFICAR DEPENDENCIAS ====================
try:
    import openpyxl
    print("[INFO] ✅ openpyxl disponible")
except ImportError:
    print("[WARN] ⚠️ openpyxl NO instalado. Ejecute: pip install openpyxl")

try:
    import reportlab
    print("[INFO] ✅ reportlab disponible")
except ImportError:
    print("[WARN] ⚠️ reportlab NO instalado. Ejecute: pip install reportlab")

# ==================== FUNCIONES JSON ====================
def cargar_json(ruta, default=None):
    if os.path.exists(ruta):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read().strip()
                if not contenido:
                    return default if default is not None else [] if isinstance(default, list) else {}
                return json.loads(contenido)
        except Exception as e:
            print(f"Error cargando {ruta}: {e}")
            return default if default is not None else [] if isinstance(default, list) else {}
    return default if default is not None else [] if isinstance(default, list) else {}

def guardar_json(ruta, data):
    try:
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error guardando {ruta}: {e}")
        return False

def registrar_bitacora(usuario, accion, detalles="", modulo=""):
    try:
        bitacora = cargar_json(ARCHIVO_BITACORA, [])
        bitacora.append({
            "id": str(random.randint(100000, 999999)),
            "fecha": datetime.now().isoformat(),
            "usuario": usuario,
            "accion": accion,
            "detalles": detalles,
            "modulo": modulo
        })
        if len(bitacora) > 10000:
            bitacora = bitacora[-10000:]
        guardar_json(ARCHIVO_BITACORA, bitacora)
    except:
        pass

def obtener_empresa(empresa_id):
    data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
    for emp in data.get("empresas", []):
        if emp.get("id") == empresa_id:
            return emp
    return None

def set_public_url(url):
    guardar_json(ARCHIVO_URL_PUBLICA, {"url": url, "fecha_actualizacion": datetime.now().isoformat()})

# ==================== SERVIDOR PUBLICO ====================
SERVIDOR_PUBLICO_DISPONIBLE = False
ID_FIJO = None
URL_CLOUDFLARE = None
PROCESO_CLOUDFLARE = None

try:
    from servidor_publico import (
        iniciar_servidor_publico,
        obtener_url_publica as obtener_url_publica_real,
        obtener_url_con_id,
        obtener_info_servidor,
        validar_dispositivo,
        ID_FIJO as ID_FIJO_REAL
    )
    SERVIDOR_PUBLICO_DISPONIBLE = True
    ID_FIJO = ID_FIJO_REAL
    print(f"[INFO] Servidor Público cargado. ID Fijo: {ID_FIJO}")
    
    def obtener_url_publica():
        return obtener_url_publica_real()
        
except ImportError as e:
    SERVIDOR_PUBLICO_DISPONIBLE = False
    ID_FIJO = None
    print(f"[WARN] Servidor Público no disponible: {e}")

    def obtener_url_publica(): 
        global URL_CLOUDFLARE
        if URL_CLOUDFLARE:
            return URL_CLOUDFLARE
        return None

# ==================== CLOUDFLARED - TUNEL ====================
_URL_PUBLICA_PAGINAS = None

def set_public_url_paginas(url):
    global _URL_PUBLICA_PAGINAS
    _URL_PUBLICA_PAGINAS = url
    print(f"[INFO] URL pública para páginas hijo: {url}")
    try:
        data = {"url": url, "fecha_actualizacion": datetime.now().isoformat()}
        guardar_json(ARCHIVO_URL_PUBLICA, data)
    except Exception as e:
        print(f"[WARN] Error guardando URL pública: {e}")

def obtener_url_publica_paginas():
    global _URL_PUBLICA_PAGINAS, URL_CLOUDFLARE
    if URL_CLOUDFLARE:
        return URL_CLOUDFLARE
    if _URL_PUBLICA_PAGINAS:
        return _URL_PUBLICA_PAGINAS
    try:
        data = cargar_json(ARCHIVO_URL_PUBLICA, {})
        return data.get("url")
    except:
        return None

def iniciar_cloudflared():
    global PROCESO_CLOUDFLARE, URL_CLOUDFLARE
    
    if PROCESO_CLOUDFLARE:
        try:
            if PROCESO_CLOUDFLARE.poll() is None:
                print("[INFO] Cloudflared ya está ejecutándose")
                return
        except:
            PROCESO_CLOUDFLARE = None
            URL_CLOUDFLARE = None
    
    cloudflared_paths = [
        os.path.join(BASE_PATH, 'templates', 'flare', 'cloudflared.exe'),
        os.path.join(BASE_PATH, 'cloudflared.exe'),
        os.path.join(os.path.dirname(sys.executable), 'cloudflared.exe'),
        'cloudflared.exe'
    ]
    
    cloudflared_path = None
    for path in cloudflared_paths:
        if os.path.exists(path):
            cloudflared_path = path
            break
    
    if not cloudflared_path:
        print("[WARN] cloudflared.exe no encontrado. El túnel no se iniciará.")
        return
    
    print(f"[INFO] Cloudflared encontrado en: {cloudflared_path}")
    
    try:
        cmd = [cloudflared_path, 'tunnel', '--url', 'http://localhost:5000']
        
        print(f"[INFO] Ejecutando: {' '.join(cmd)}")
        
        if IS_WINDOWS:
            PROCESO_CLOUDFLARE = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        else:
            PROCESO_CLOUDFLARE = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        print("[INFO] ✅ Cloudflared iniciado. Esperando URL...")
        
        def leer_salida_cloudflared():
            global URL_CLOUDFLARE
            try:
                for line in iter(PROCESO_CLOUDFLARE.stderr.readline, ''):
                    if line:
                        match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
                        if match:
                            URL_CLOUDFLARE = match.group(0)
                            print(f"[INFO] 🌐 Túnel Cloudflare activo: {URL_CLOUDFLARE}")
                            set_public_url(URL_CLOUDFLARE)
                            set_public_url_paginas(URL_CLOUDFLARE)
                            break
            except:
                pass
        
        hilo_lectura = threading.Thread(target=leer_salida_cloudflared, daemon=True)
        hilo_lectura.start()
        
        time.sleep(5)
        
        if URL_CLOUDFLARE:
            print(f"[INFO] ✅ Cloudflared URL: {URL_CLOUDFLARE}")
            set_public_url_paginas(URL_CLOUDFLARE)
        else:
            print("[INFO] Cloudflared iniciado (URL aún no disponible)")
            
    except Exception as e:
        print(f"[ERROR] Error iniciando Cloudflared: {e}")
        PROCESO_CLOUDFLARE = None

def detener_cloudflared():
    global PROCESO_CLOUDFLARE, URL_CLOUDFLARE
    if PROCESO_CLOUDFLARE:
        try:
            PROCESO_CLOUDFLARE.terminate()
            PROCESO_CLOUDFLARE.wait(timeout=5)
            print("[INFO] Cloudflared detenido")
        except:
            try:
                PROCESO_CLOUDFLARE.kill()
            except:
                pass
        PROCESO_CLOUDFLARE = None
        URL_CLOUDFLARE = None

# ==================== FUNCIONES DE TEMAS ====================
TEMAS_DISPONIBLES = {
    "default": {
        "nombre": "Por Defecto",
        "descripcion": "Gradiente oscuro",
        "clase": "default-theme",
        "fondo": "radial-gradient(circle at 10% 20%, #0a0f1c, #03060c)",
        "color_texto": "#f0f3fa",
        "color_primario": "#f59e0b",
        "color_secundario": "#d97706"
    },
    "dark": {
        "nombre": "Oscuro Sólido",
        "descripcion": "Fondo negro sólido",
        "clase": "dark-theme",
        "fondo": "#0a0e1a",
        "color_texto": "#ffffff",
        "color_primario": "#f59e0b",
        "color_secundario": "#d97706"
    },
    "light": {
        "nombre": "Claro",
        "descripcion": "Fondo blanco/gris",
        "clase": "light-theme",
        "fondo": "#f5f7fa",
        "color_texto": "#1a1a2e",
        "color_primario": "#f59e0b",
        "color_secundario": "#d97706"
    },
    "navy": {
        "nombre": "Azul Marino",
        "descripcion": "Gradiente vibrante",
        "clase": "navy-theme",
        "fondo": "linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb4d)",
        "color_texto": "#ffffff",
        "color_primario": "#fdbb4d",
        "color_secundario": "#f59e0b"
    },
    "nature": {
        "nombre": "Naturaleza",
        "descripcion": "Verdes relajantes",
        "clase": "nature-theme",
        "fondo": "linear-gradient(135deg, #134e5e, #71b280)",
        "color_texto": "#ffffff",
        "color_primario": "#71b280",
        "color_secundario": "#134e5e"
    },
    "image": {
        "nombre": "Imagen Personalizada",
        "descripcion": "Usa tu propia imagen",
        "clase": "image-theme",
        "fondo": "url('https://images.unsplash.com/photo-1508514177221-188f0d9d8c5f?q=80&w=2070&auto=format')",
        "color_texto": "#ffffff",
        "color_primario": "#f59e0b",
        "color_secundario": "#d97706"
    }
}

COLORES_POR_DEFECTO = {
    "texto": "#f0f3fa",
    "primario": "#f59e0b",
    "secundario": "#d97706",
    "logo": "#f59e0b",
    "titulo": "#ffffff",
    "topBarFondo": "#0f0f1a",
    "topBarTexto": "#c0c0d0",
    "topBarBorde": "#f59e0b",
    "menuFondo": "#0f0f1a",
    "menuTexto": "#c0c0d0",
    "menuActivo": "#f59e0b",
    "menuActivoTexto": "#ffffff",
    "moduloFondo": "#1a1a2e",
    "moduloBorde": "#2a2a3e",
    "moduloTexto": "#e0e0e0",
    "moduloCard": "#1e1e2f",
    "moduloEtiqueta": "#f59e0b",
    "moduloAcento": "#f59e0b"
}

LOGO_POR_DEFECTO = {
    "icono": "fa-gas-pump",
    "iconoColor": "#ffffff",
    "titulo": "GRUPO GSN",
    "subtitulo": "Sistema de Gestión de Combustible"
}

TRANSPARENCIA_POR_DEFECTO = {
    "fondo": 0.08,
    "tarjetas": 0.05,
    "bordes": 0.02,
    "blur": 30
}

BRILLO_POR_DEFECTO = {
    "brilloTextos": 1.5,
    "brilloTitulos": 1.8,
    "colorTexto": "#ffffff",
    "colorDestacado": "#fbbf24",
    "colorTitulo": "#ffffff",
    "colorEtiqueta": "#f59e0b"
}

MODULOS_POR_DEFECTO = [
    "dashboard", "operaciones", "empresas", "facturacion",
    "flota", "costos", "reportes", "paginas_hijo",
    "tablas_editables", "configuracion", "ubicacion"
]

# ==================== FUNCIONES DE USUARIO ====================
def obtener_clave_usuario(usuario_id, email=None):
    if usuario_id:
        return f"usuario_{usuario_id}"
    elif email:
        return f"usuario_{hashlib.md5(email.lower().encode()).hexdigest()[:8]}"
    return "usuario_default"

def obtener_carpeta_usuario(email):
    if email:
        hash_email = hashlib.md5(email.lower().encode()).hexdigest()[:16]
        carpeta = os.path.join(CARPETA_IMAGENES_FONDO, hash_email)
        Path(carpeta).mkdir(parents=True, exist_ok=True)
        return carpeta
    return CARPETA_IMAGENES_FONDO

def obtener_tema_usuario(usuario_id, email=None):
    temas = cargar_json(ARCHIVO_TEMAS_USUARIOS, {})
    clave = obtener_clave_usuario(usuario_id, email)
    
    if clave in temas:
        tema_data = temas[clave]
        colores = tema_data.get("colores", {})
        colores_completos = {**COLORES_POR_DEFECTO, **colores}
        logo = tema_data.get("logo", {})
        logo_completo = {**LOGO_POR_DEFECTO, **logo}
        transparencia = tema_data.get("transparencia", {})
        transparencia_completa = {**TRANSPARENCIA_POR_DEFECTO, **transparencia}
        brillo = tema_data.get("brillo", {})
        brillo_completo = {**BRILLO_POR_DEFECTO, **brillo}
        
        return {
            "tema": tema_data.get("tema", "default"),
            "imagen_url": tema_data.get("imagen_url"),
            "fecha_actualizacion": tema_data.get("fecha_actualizacion", datetime.now().isoformat()),
            "color_primario": tema_data.get("color_primario", "#f59e0b"),
            "color_secundario": tema_data.get("color_secundario", "#d97706"),
            "colores": colores_completos,
            "logo": logo_completo,
            "transparencia": transparencia_completa,
            "brillo": brillo_completo
        }
    
    return {
        "tema": "default",
        "imagen_url": None,
        "fecha_actualizacion": datetime.now().isoformat(),
        "color_primario": TEMAS_DISPONIBLES["default"]["color_primario"],
        "color_secundario": TEMAS_DISPONIBLES["default"]["color_secundario"],
        "colores": COLORES_POR_DEFECTO.copy(),
        "logo": LOGO_POR_DEFECTO.copy(),
        "transparencia": TRANSPARENCIA_POR_DEFECTO.copy(),
        "brillo": BRILLO_POR_DEFECTO.copy()
    }

def guardar_tema_completo(usuario_id, tema, imagen_url, colores, logo, email=None, transparencia=None, brillo=None):
    temas = cargar_json(ARCHIVO_TEMAS_USUARIOS, {})
    clave = obtener_clave_usuario(usuario_id, email)
    
    if tema not in TEMAS_DISPONIBLES and tema != "image":
        tema = "default"
    
    colores_completos = {
        "texto": colores.get("texto", "#f0f3fa"),
        "primario": colores.get("primario", "#f59e0b"),
        "secundario": colores.get("secundario", "#d97706"),
        "logo": colores.get("logo", "#f59e0b"),
        "titulo": colores.get("titulo", "#ffffff"),
        "topBarFondo": colores.get("topBarFondo", "#0f0f1a"),
        "topBarTexto": colores.get("topBarTexto", "#c0c0d0"),
        "topBarBorde": colores.get("topBarBorde", "#f59e0b"),
        "menuFondo": colores.get("menuFondo", "#0f0f1a"),
        "menuTexto": colores.get("menuTexto", "#c0c0d0"),
        "menuActivo": colores.get("menuActivo", "#f59e0b"),
        "menuActivoTexto": colores.get("menuActivoTexto", "#ffffff"),
        "moduloFondo": colores.get("moduloFondo", "#1a1a2e"),
        "moduloBorde": colores.get("moduloBorde", "#2a2a3e"),
        "moduloTexto": colores.get("moduloTexto", "#e0e0e0"),
        "moduloCard": colores.get("moduloCard", "#1e1e2f"),
        "moduloEtiqueta": colores.get("moduloEtiqueta", "#f59e0b"),
        "moduloAcento": colores.get("moduloAcento", "#f59e0b")
    }
    
    logo_completo = {
        "icono": logo.get("icono", "fa-gas-pump"),
        "iconoColor": logo.get("iconoColor", "#ffffff"),
        "titulo": logo.get("titulo", "GRUPO GSN"),
        "subtitulo": logo.get("subtitulo", "Sistema de Gestión de Combustible")
    }
    
    transparencia_completa = {
        "fondo": transparencia.get("fondo", 0.08) if transparencia else 0.08,
        "tarjetas": transparencia.get("tarjetas", 0.05) if transparencia else 0.05,
        "bordes": transparencia.get("bordes", 0.02) if transparencia else 0.02,
        "blur": transparencia.get("blur", 30) if transparencia else 30
    }
    
    brillo_completo = {
        "brilloTextos": brillo.get("brilloTextos", 1.5) if brillo else 1.5,
        "brilloTitulos": brillo.get("brilloTitulos", 1.8) if brillo else 1.8,
        "colorTexto": brillo.get("colorTexto", "#ffffff") if brillo else "#ffffff",
        "colorDestacado": brillo.get("colorDestacado", "#fbbf24") if brillo else "#fbbf24",
        "colorTitulo": brillo.get("colorTitulo", "#ffffff") if brillo else "#ffffff",
        "colorEtiqueta": brillo.get("colorEtiqueta", "#f59e0b") if brillo else "#f59e0b"
    }
    
    temas[clave] = {
        "tema": tema,
        "imagen_url": imagen_url,
        "colores": colores_completos,
        "logo": logo_completo,
        "transparencia": transparencia_completa,
        "brillo": brillo_completo,
        "fecha_actualizacion": datetime.now().isoformat(),
        "color_primario": colores_completos["primario"],
        "color_secundario": colores_completos["secundario"]
    }
    
    return guardar_json(ARCHIVO_TEMAS_USUARIOS, temas)

def guardar_tema_usuario(usuario_id, tema, imagen_url=None, email=None):
    temas = cargar_json(ARCHIVO_TEMAS_USUARIOS, {})
    clave = obtener_clave_usuario(usuario_id, email)
    
    if tema not in TEMAS_DISPONIBLES and tema != "image":
        tema = "default"
    
    tema_existente = temas.get(clave, {})
    colores = tema_existente.get("colores", COLORES_POR_DEFECTO.copy())
    logo = tema_existente.get("logo", LOGO_POR_DEFECTO.copy())
    
    temas[clave] = {
        "tema": tema,
        "imagen_url": imagen_url if tema == "image" else None,
        "fecha_actualizacion": datetime.now().isoformat(),
        "color_primario": TEMAS_DISPONIBLES[tema]["color_primario"] if tema in TEMAS_DISPONIBLES else TEMAS_DISPONIBLES["default"]["color_primario"],
        "color_secundario": TEMAS_DISPONIBLES[tema]["color_secundario"] if tema in TEMAS_DISPONIBLES else TEMAS_DISPONIBLES["default"]["color_secundario"],
        "colores": colores,
        "logo": logo
    }
    
    return guardar_json(ARCHIVO_TEMAS_USUARIOS, temas)

def guardar_tema_por_email(email, tema, imagen_url=None):
    if not email:
        return False
    
    temas = cargar_json(ARCHIVO_TEMAS_USUARIOS, {})
    clave = f"usuario_{hashlib.md5(email.lower().encode()).hexdigest()[:8]}"
    
    if tema not in TEMAS_DISPONIBLES and tema != "image":
        tema = "default"
    
    tema_existente = temas.get(clave, {})
    colores = tema_existente.get("colores", COLORES_POR_DEFECTO.copy())
    logo = tema_existente.get("logo", LOGO_POR_DEFECTO.copy())
    
    temas[clave] = {
        "tema": tema,
        "imagen_url": imagen_url if tema == "image" else None,
        "fecha_actualizacion": datetime.now().isoformat(),
        "color_primario": TEMAS_DISPONIBLES[tema]["color_primario"] if tema in TEMAS_DISPONIBLES else TEMAS_DISPONIBLES["default"]["color_primario"],
        "color_secundario": TEMAS_DISPONIBLES[tema]["color_secundario"] if tema in TEMAS_DISPONIBLES else TEMAS_DISPONIBLES["default"]["color_secundario"],
        "colores": colores,
        "logo": logo
    }
    
    return guardar_json(ARCHIVO_TEMAS_USUARIOS, temas)

def obtener_tema_por_email(email):
    if not email:
        return None
    
    clave = f"usuario_{hashlib.md5(email.lower().encode()).hexdigest()[:8]}"
    temas = cargar_json(ARCHIVO_TEMAS_USUARIOS, {})
    
    if clave in temas:
        tema_data = temas[clave]
        colores = tema_data.get("colores", {})
        colores_completos = {**COLORES_POR_DEFECTO, **colores}
        logo = tema_data.get("logo", {})
        logo_completo = {**LOGO_POR_DEFECTO, **logo}
        transparencia = tema_data.get("transparencia", {})
        transparencia_completa = {**TRANSPARENCIA_POR_DEFECTO, **transparencia}
        brillo = tema_data.get("brillo", {})
        brillo_completo = {**BRILLO_POR_DEFECTO, **brillo}
        
        return {
            "tema": tema_data.get("tema", "default"),
            "imagen_url": tema_data.get("imagen_url"),
            "fecha_actualizacion": tema_data.get("fecha_actualizacion", datetime.now().isoformat()),
            "color_primario": tema_data.get("color_primario", "#f59e0b"),
            "color_secundario": tema_data.get("color_secundario", "#d97706"),
            "colores": colores_completos,
            "logo": logo_completo,
            "transparencia": transparencia_completa,
            "brillo": brillo_completo
        }
    
    return {
        "tema": "default",
        "imagen_url": None,
        "fecha_actualizacion": datetime.now().isoformat(),
        "color_primario": TEMAS_DISPONIBLES["default"]["color_primario"],
        "color_secundario": TEMAS_DISPONIBLES["default"]["color_secundario"],
        "colores": COLORES_POR_DEFECTO.copy(),
        "logo": LOGO_POR_DEFECTO.copy(),
        "transparencia": TRANSPARENCIA_POR_DEFECTO.copy(),
        "brillo": BRILLO_POR_DEFECTO.copy()
    }

def eliminar_tema_usuario(usuario_id, email=None):
    temas = cargar_json(ARCHIVO_TEMAS_USUARIOS, {})
    clave = obtener_clave_usuario(usuario_id, email)
    
    if clave in temas:
        del temas[clave]
        return guardar_json(ARCHIVO_TEMAS_USUARIOS, temas)
    return True

# ==================== DATOS DEMO ====================
def inicializar_datos_demo():
    if not os.path.exists(ARCHIVO_EMPRESAS):
        empresas = {
            "empresas": [
                {"id": "SANTA-RITA-001", "nombre": "SANTA RITA MINING S.A.", "contacto": "Carlos Rodriguez", 
                 "cedula": "J0310000012345", "telefono": "505 8888 7777", "email": "santarita@example.com", 
                 "direccion": "Managua", "destino": "Rosita-RAAN", "conductor": "Luis Gonzalez",
                 "tipo": "Cliente", "placa": "M337072", "fecha_registro": datetime.now().isoformat(), 
                 "pedidos": 0, "activo": True, "credito": 15000.0, "limite_credito": 100000.0,
                 "origen": "Managua", "destino_ruta": "Rosita", "precio_diesel": 162.50,
                 "precio_diesel_max": 170.00, "precio_gasolina": 145.00, "precio_gasolina_max": 152.00,
                 "bono1": "", "bono2": "", "viatico1": 200.0, "viatico2": 0,
                 "costo_traslado": 1500.0, "distancia_km": 788.0,
                 "columnas_adicionales": {},
                 "formula_calculos": "=E+F+G+H+K+L+M+N",
                 "costo_total": 0.0}
            ],
            "ultimo_id": 1
        }
        guardar_json(ARCHIVO_EMPRESAS, empresas)
        print("[OK] 1 Empresa demo creada con costos de ruta")
    
    if not os.path.exists(ARCHIVO_CONDUCTORES):
        conductores = {
            "conductores": [
                {"id": "CON-001", "nombre": "YADER SEQUEIRA", "cedula": "001-010199-0001A", 
                 "licencia": "D-12345", "telefono": "505 8888 1111", "direccion": "Managua", "activo": True}
            ],
            "ultimo_id": 1
        }
        guardar_json(ARCHIVO_CONDUCTORES, conductores)
        print("[OK] 1 Conductor demo creado")
    
    if not os.path.exists(ARCHIVO_CAMIONES):
        camiones = {
            "camiones": [
                {"id": "CAM-001", "placa": "M337072", "marca": "FORD", "modelo": "F-350", 
                 "anio": "2020", "capacidad_galones": 4000, "tipo": "Cisterna", 
                 "conductor_asignado": "YADER SEQUEIRA", "estado": "Disponible", "activo": True}
            ],
            "ultimo_id": 1
        }
        guardar_json(ARCHIVO_CAMIONES, camiones)
        print("[OK] 1 Camión demo creado")
    
    if not os.path.exists(ARCHIVO_USUARIOS):
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        usuarios = {
            "usuarios": [
                {"id": "USR-001", "nombre": "Administrador", "email": "admin@gruposn.com", 
                 "rol": "admin", "password": admin_hash, "estado": "activo",
                 "password_plain": "admin123",
                 "cedula": "", "telefono": "", "empresa_id": None, "empresa_nombre": "",
                 "modulos_permitidos": ["*"],
                 "fecha_creacion": datetime.now().isoformat()}
            ],
            "ultimo_id": 1
        }
        guardar_json(ARCHIVO_USUARIOS, usuarios)
        print("[OK] Usuario admin creado")
    
    if not os.path.exists(ARCHIVO_PEDIDOS):
        fecha = datetime.now()
        galones = 1000
        precio = 162.50
        costo_combustible = galones * precio
        costo_traslado = 1500
        costo_total = costo_combustible + costo_traslado
        
        pedido = {
            "id": f"PED-{datetime.now().strftime('%Y%m%d')}-001",
            "empresa_id": "SANTA-RITA-001",
            "nombre": "SANTA RITA MINING S.A.",
            "fecha": fecha.isoformat(),
            "fecha_str": fecha.strftime("%Y-%m-%d"),
            "origen": "Managua",
            "destino": "Rosita-RAAN",
            "tipo_combustible": "DIESEL",
            "galones": galones,
            "precio_por_galon": precio,
            "costo_combustible": round(costo_combustible, 2),
            "costo_traslado": costo_traslado,
            "costo_total": round(costo_total, 2),
            "iva": round(costo_total * 0.19, 2),
            "importe": round(costo_total * 1.19, 2),
            "facturado": False,
            "estado_operacion": "espera",
            "conductor_asignado": "",
            "camion_asignado": "",
            "bono_cupon": "",
            "viatico": 0
        }
        guardar_json(ARCHIVO_PEDIDOS, [pedido])
        print(f"[OK] 1 Pedido demo creado en estado ESPERA")
    
    archivos_default = {
        ARCHIVO_PEDIDOS_FACTURACION: [],
        ARCHIVO_FACTURAS: {"facturas": []},
        ARCHIVO_CONFIG_IA: {},
        ARCHIVO_CONFIG_CORREO: {},
        ARCHIVO_CONFIG_SISTEMA: {"version": "2.0", "empresa_nombre": "GRUPO GSN"},
        ARCHIVO_PAGINAS: {"paginas": []},
        ARCHIVO_MANTENIMIENTO: [],
        ARCHIVO_OPERACIONES: {},
        ARCHIVO_CONFIG_FACTURA: {
            "empresa": {"nombre": "GRUPO GSN", "ruc": "J0310000012345", "telefono": "+505 2278 1234", 
                       "direccion": "Managua, Nicaragua", "email": "info@gruposn.com", 
                       "slogan": "Sistema de Gestion de Combustible"},
            "colores": {"primario": "#f59e0b", "titulo": "#f59e0b", "fondo": "#ffffff", "tablaHeader": "#f59e0b"},
            "visibles": {"mostrarSlogan": True, "mostrarRuc": True, "mostrarTelefono": True, 
                        "mostrarEmail": True, "mostrarDireccion": True},
            "camposAdicionales": []
        },
        ARCHIVO_REPORTES_DATA: {"columnas_personalizadas": [], "datos_tabla": [], "totals_editados": {}, "ultima_actualizacion": datetime.now().isoformat()},
        ARCHIVO_ESTADOS_FACTURAS: {},
        ARCHIVO_BITACORA_DATA: {"empresas": [], "pedidos": [], "costos": [], "conductores": [], "camiones": [], "facturas": [], "ultima_actualizacion": datetime.now().isoformat()},
        ARCHIVO_UBICACIONES: {"ultima_actualizacion": datetime.now().isoformat(), "vehiculos": []},
        ARCHIVO_COSTOS_TRASLADO: {"costos": [], "columnas_adicionales": []},
        ARCHIVO_OBSERVACIONES: {},
        ARCHIVO_CONFIG_CLIENTES: {
            "columnas": [
                "CLIENTE", "TIPO", "ORIGEN", "DESTINO",
                "DIESEL", "DIESEL MAX", "GASOLINA", "GASOLINA MAX",
                "BONO 1", "BONO 2", "VIATICO 1", "VIATICO 2",
                "TRASLADO", "DISTANCIA", "COSTO TOTAL"
            ],
            "nombres_mostrados": {
                "CLIENTE": "Cliente",
                "TIPO": "Tipo",
                "ORIGEN": "Origen",
                "DESTINO": "Destino",
                "DIESEL": "Diesel",
                "DIESEL MAX": "Diesel Max",
                "GASOLINA": "Gasolina",
                "GASOLINA MAX": "Gasolina Max",
                "BONO 1": "Bono 1",
                "BONO 2": "Bono 2",
                "VIATICO 1": "Viático 1",
                "VIATICO 2": "Viático 2",
                "TRASLADO": "Traslado",
                "DISTANCIA": "Distancia",
                "COSTO TOTAL": "Costo Total"
            },
            "columnas_protegidas": [
                "CLIENTE", "TIPO", "ORIGEN", "DESTINO",
                "DIESEL", "DIESEL MAX", "GASOLINA", "GASOLINA MAX",
                "BONO 1", "BONO 2", "VIATICO 1", "VIATICO 2",
                "TRASLADO", "DISTANCIA", "COSTO TOTAL"
            ],
            "columnas_numericas": [
                "DIESEL", "DIESEL MAX", "GASOLINA", "GASOLINA MAX",
                "VIATICO 1", "VIATICO 2", "TRASLADO", "DISTANCIA", "COSTO TOTAL"
            ],
            "version": "2.0",
            "fecha_actualizacion": datetime.now().isoformat()
        },
        ARCHIVO_CLIENTES: {"clientes": [], "ultimo_id": 0},
        ARCHIVO_CHAT: {"mensajes_por_conductor": {}, "ubicaciones": {}, "conductores": {}, "chats_activos": {}}
    }
    
    for archivo, default in archivos_default.items():
        if not os.path.exists(archivo):
            guardar_json(archivo, default)
            print(f"[OK] Archivo creado: {os.path.basename(archivo)}")
    
    print("[OK] Todos los datos demo inicializados")

# ==================== CREAR APP FLASK ====================
app = Flask(__name__, 
            template_folder=os.path.join(BASE_PATH, "templates"),
            static_folder=os.path.join(BASE_PATH, "static"))

# ===== CONFIGURACIÓN CORS =====
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept", "X-User-Data", "Authorization"]
    }
})

# ===== CONFIGURACIÓN TAMAÑO MÁXIMO =====
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['MAX_FORM_MEMORY_SIZE'] = 50 * 1024 * 1024

# ===== MANEJADOR DE ERRORES =====
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"ok": False, "error": "El archivo es demasiado grande. Máximo 50 MB"}), 413

# ==================== IMPORTAR MODULOS ====================
main_funciones = {
    'cargar_json': cargar_json,
    'guardar_json': guardar_json,
    'registrar_bitacora': registrar_bitacora,
    'obtener_empresa': obtener_empresa,
    'set_public_url': set_public_url,
    'obtener_url_publica': obtener_url_publica,
    'archivo_clientes': ARCHIVO_CLIENTES,
    'archivo_empresas': ARCHIVO_EMPRESAS,
    'openpyxl_disponible': True,
    'reportlab_disponible': True
}

rutas_config = {
    'pedidos': ARCHIVO_PEDIDOS,
    'pedidos_facturacion': ARCHIVO_PEDIDOS_FACTURACION,
    'facturas': ARCHIVO_FACTURAS,
    'conductores': ARCHIVO_CONDUCTORES,
    'camiones': ARCHIVO_CAMIONES,
    'costos_traslado': ARCHIVO_COSTOS_TRASLADO,
    'config_ia': ARCHIVO_CONFIG_IA,
    'config_correo': ARCHIVO_CONFIG_CORREO,
    'config_sistema': ARCHIVO_CONFIG_SISTEMA,
    'bitacora': ARCHIVO_BITACORA,
    'tablas_editables': ARCHIVO_TABLAS_EDITABLES,
    'mantenimiento': ARCHIVO_MANTENIMIENTO,
    'paginas': ARCHIVO_PAGINAS,
    'operaciones': ARCHIVO_OPERACIONES,
    'excel_reportes': CARPETA_EXCEL_REPORTES,
    'pdf_reportes': CARPETA_PDF_REPORTES,
    'reportes_data': ARCHIVO_REPORTES_DATA,
    'ubicaciones': ARCHIVO_UBICACIONES,
    'excel_clientes': CARPETA_EXCEL_CLIENTES,
    'pdf_clientes': CARPETA_PDF_CLIENTES,
    'config_clientes': ARCHIVO_CONFIG_CLIENTES,
    'clientes': ARCHIVO_CLIENTES,
    'observaciones': ARCHIVO_OBSERVACIONES,
    'chat': ARCHIVO_CHAT
}

api_funciones = {}

# ==================== IMPORTAR MODULOS DEL SISTEMA ====================

# 1. Importar módulo Recepcion
try:
    from recepcion import (
        inicializar_recepcion,
        api_pedidos_recientes, api_estadisticas_recepcion,
        api_datos_graficas, api_forzar_actualizacion,
        api_obtener_pedidos_actualizados,
        api_obtener_pedidos_pendientes,
        api_obtener_pedidos_camino,
        api_obtener_pedidos_entregados,
        api_obtener_todas_observaciones
    )
    print("[INFO] Modulo Recepcion importado")
    inicializar_recepcion(ARCHIVO_PEDIDOS, ARCHIVO_FACTURAS, cargar_json, guardar_json, ARCHIVO_PEDIDOS_FACTURACION)
    api_funciones['recepcion'] = {
        'pedidos_recientes': api_pedidos_recientes,
        'estadisticas': api_estadisticas_recepcion,
        'datos_graficas': api_datos_graficas,
        'forzar_actualizacion': api_forzar_actualizacion,
        'pedidos_actualizados': api_obtener_pedidos_actualizados,
        'pedidos_pendientes': api_obtener_pedidos_pendientes,
        'pedidos_camino': api_obtener_pedidos_camino,
        'pedidos_entregados': api_obtener_pedidos_entregados,
        'obtener_todas_observaciones': api_obtener_todas_observaciones
    }
except ImportError as e:
    print(f"[ERROR] Recepcion: {e}")
    
# 2. Importar módulo Operaciones
try:
    from operaciones import (
        inicializar_operaciones, configurar_archivos as config_operaciones_archivos,
        api_obtener_conductores, api_obtener_camiones,
        api_obtener_resumen_operaciones, api_actualizar_flota_pedido,
        api_enviar_a_facturacion, api_actualizar_estado_operacion,
        api_actualizar_estado_con_factura, api_marcar_como_entregado,
        api_obtener_estados_facturas, api_guardar_estado_factura,
        api_guardar_observacion, api_obtener_observacion,
        api_obtener_estado_operaciones,
        api_guardar_asignacion,
        api_cargar_asignacion,
        api_guardar_pedido_seleccionado,
        api_cargar_pedido_seleccionado,
        api_limpiar_datos_falsos,
        api_pedidos_facturacion,
        api_actualizar_pedido_desde_factura,
        api_obtener_bonos_viaticos_directo,
        api_obtener_datos_cliente_desde_gestion,
        api_obtener_credito_cliente,
        api_crear_pedido_manual
    )
    print("[INFO] Modulo Operaciones importado")
    inicializar_operaciones(ARCHIVO_OPERACIONES, main_funciones)
    config_operaciones_archivos(
        ARCHIVO_PEDIDOS, ARCHIVO_PEDIDOS_FACTURACION, ARCHIVO_CONDUCTORES,
        ARCHIVO_CAMIONES, ARCHIVO_BITACORA, ARCHIVO_TABLAS_EDITABLES, ARCHIVO_FACTURAS,
        ARCHIVO_COSTOS_TRASLADO, ARCHIVO_EMPRESAS
    )
    api_funciones['operaciones'] = {
        'conductores': api_obtener_conductores,
        'camiones': api_obtener_camiones,
        'resumen': api_obtener_resumen_operaciones,
        'actualizar_flota': api_actualizar_flota_pedido,
        'enviar_facturacion': api_enviar_a_facturacion,
        'actualizar_estado': api_actualizar_estado_operacion,
        'actualizar_estado_con_factura': api_actualizar_estado_con_factura,
        'marcar_entregado': api_marcar_como_entregado,
        'obtener_estados_facturas': api_obtener_estados_facturas,
        'guardar_estado_factura': api_guardar_estado_factura,
        'guardar_observacion': api_guardar_observacion,
        'obtener_observacion': api_obtener_observacion,
        'obtener_estado': api_obtener_estado_operaciones,
        'guardar_asignacion': api_guardar_asignacion,
        'cargar_asignacion': api_cargar_asignacion,
        'guardar_pedido_seleccionado': api_guardar_pedido_seleccionado,
        'cargar_pedido_seleccionado': api_cargar_pedido_seleccionado,
        'limpiar_falsos': api_limpiar_datos_falsos,
        'pedidos_facturacion': api_pedidos_facturacion,
        'actualizar_pedido_desde_factura': api_actualizar_pedido_desde_factura,
        'obtener_bonos_viaticos_directo': api_obtener_bonos_viaticos_directo,
        'obtener_datos_cliente': api_obtener_datos_cliente_desde_gestion,
        'obtener_credito': api_obtener_credito_cliente,
        'crear_pedido_manual': api_crear_pedido_manual
    }
except ImportError as e:
    print(f"[ERROR] Operaciones: {e}")

# 3. Importar módulo Facturacion
try:
    from facturacion import (
        inicializar_facturacion, configurar_archivos as config_factura_archivos,
        api_guardar_config_factura, api_obtener_config_factura,
        api_facturar_pedidos, api_facturas_lista, descargar_factura,
        api_enviar_factura_correo, api_mis_facturas_detalle, api_factura,
        api_eliminar_pedido_facturacion, api_actualizar_pedido,
        api_pedidos_facturacion, api_limpiar_facturas, api_estado_limpieza,
        api_actualizar_factura,
        api_facturas_permitidas_cliente,
        api_obtener_permisos as api_obtener_permisos_facturas,
        api_actualizar_permiso as api_actualizar_permiso_factura
    )
    print("[INFO] Modulo Facturacion importado")
    inicializar_facturacion(CARPETA_PDF_FACTURAS, True, main_funciones)
    config_factura_archivos(ARCHIVO_PEDIDOS, ARCHIVO_FACTURAS, ARCHIVO_PEDIDOS_FACTURACION)
    api_funciones['facturacion'] = {
        'guardar_config': api_guardar_config_factura,
        'obtener_config': api_obtener_config_factura,
        'facturar': api_facturar_pedidos,
        'listar_facturas': api_facturas_lista,
        'descargar_factura': descargar_factura,
        'enviar_correo': api_enviar_factura_correo,
        'mis_facturas': api_mis_facturas_detalle,
        'factura': api_factura,
        'eliminar_pedido': api_eliminar_pedido_facturacion,
        'actualizar_pedido': api_actualizar_pedido,
        'pedidos_pendientes': api_pedidos_facturacion,
        'limpiar_facturas': api_limpiar_facturas,
        'estado_limpieza': api_estado_limpieza,
        'actualizar_factura': api_actualizar_factura,
        'facturas_permitidas_cliente': api_facturas_permitidas_cliente,
        'obtener_permisos': api_obtener_permisos_facturas,
        'actualizar_permiso': api_actualizar_permiso_factura
    }
except ImportError as e:
    print(f"[ERROR] Facturacion: {e}")
    
# 4. Importar módulo Gestión Clientes
try:
    from gestion_clientes import (
        inicializar_gestion_clientes,
        api_clientes_completos,
        api_obtener_cliente,
        api_guardar_cliente,
        api_eliminar_cliente,
        api_actualizar_credito,
        api_extender_limite,
        api_alertas_credito,
        api_estado_credito,
        api_validar_cliente,
        api_exportar_excel,
        api_exportar_pdf,
        api_guardar_config,
        api_obtener_config,
        registrar_rutas
    )
    print("[INFO] Modulo Gestión Clientes importado")
    inicializar_gestion_clientes(main_funciones, rutas_config)
    api_funciones['gestion_clientes'] = {
        'clientes_completos': api_clientes_completos,
        'obtener_cliente': api_obtener_cliente,
        'guardar_cliente': api_guardar_cliente,
        'eliminar_cliente': api_eliminar_cliente,
        'actualizar_credito': api_actualizar_credito,
        'extender_limite': api_extender_limite,
        'alertas': api_alertas_credito,
        'estado_credito': api_estado_credito,
        'validar': api_validar_cliente,
        'exportar_excel': api_exportar_excel,
        'exportar_pdf': api_exportar_pdf,
        'guardar_config': api_guardar_config,
        'obtener_config': api_obtener_config
    }
    registrar_rutas(app)
    print("[INFO] Rutas de Gestión Clientes registradas")
except ImportError as e:
    print(f"[ERROR] Gestión Clientes: {e}")
    import traceback
    traceback.print_exc()

# 5. Importar módulo Configuracion
try:
    from configuracion import (
        inicializar_configuracion,
        api_config_ia, api_config_correo, api_config_sistema,
        api_probar_correo, api_enviar_ia_ahora,
        api_obtener_usuarios, api_registrar_usuario,
        api_actualizar_usuario, api_eliminar_usuario
    )
    print("[INFO] Modulo Configuracion importado")
    inicializar_configuracion(main_funciones, rutas_config)
    api_funciones['configuracion'] = {
        'ia': api_config_ia,
        'correo': api_config_correo,
        'sistema': api_config_sistema,
        'probar_correo': api_probar_correo,
        'enviar_ia': api_enviar_ia_ahora,
        'usuarios': api_obtener_usuarios,
        'registrar_usuario': api_registrar_usuario,
        'actualizar_usuario': api_actualizar_usuario,
        'eliminar_usuario': api_eliminar_usuario
    }
except ImportError as e:
    print(f"[ERROR] Configuracion: {e}")
    
# 6. Importar módulo Paginas Hijo
try:
    from paginas_hijo import (
        inicializar_modulo as inicializar_paginas,
        api_paginas, api_crear_pagina, api_eliminar_pagina,
        api_obtener_pagina, api_actualizar_pagina,
        api_obtener_enlaces,
        set_public_url as set_public_url_paginas_import,
        cargar_paginas, crear_pagina, obtener_pagina_por_url,
        regenerar_todas_paginas
    )
    print("[INFO] Modulo Paginas Hijo importado")
    inicializar_paginas(ARCHIVO_PAGINAS, CARPETA_PAGINAS, None, main_funciones)
    api_funciones['paginas'] = {
        'listar': api_paginas,
        'crear': api_crear_pagina,
        'eliminar': api_eliminar_pagina,
        'obtener': api_obtener_pagina,
        'actualizar': api_actualizar_pagina,
        'regenerar': regenerar_todas_paginas,
        'obtener_enlaces': api_obtener_enlaces
    }
    set_public_url_paginas = set_public_url_paginas_import
except ImportError as e:
    print(f"[ERROR] Paginas Hijo: {e}")
    def set_public_url_paginas(url): pass
    def regenerar_todas_paginas(): pass

# 7. Importar módulo Reportes
try:
    from reportes import (
        inicializar_reportes,
        api_estadisticas, api_exportar_excel, api_exportar_pdf, 
        api_descargar_reporte, api_recargar, api_estadisticas_avanzadas,
        api_guardar_datos_tabla, 
        api_cargar_datos_tabla,
        api_guardar_celda_tabla, 
        api_guardar_columnas_tabla,
        api_guardar_totales
    )
    print("[INFO] Modulo Reportes importado")
    inicializar_reportes(main_funciones, rutas_config)
    api_funciones['reportes'] = {
        'estadisticas': api_estadisticas,
        'exportar_excel': api_exportar_excel,
        'exportar_pdf': api_exportar_pdf,
        'descargar': api_descargar_reporte,
        'recargar': api_recargar,
        'estadisticas_avanzadas': api_estadisticas_avanzadas,
        'guardar_datos': api_guardar_datos_tabla,
        'cargar_datos': api_cargar_datos_tabla,
        'guardar_celda': api_guardar_celda_tabla,
        'guardar_columnas': api_guardar_columnas_tabla,
        'guardar_totales': api_guardar_totales
    }
except ImportError as e:
    print(f"[ERROR] Reportes: {e}")
    
# 8. Importar módulo Flota
try:
    from flota import (
        inicializar_flota,
        api_obtener_conductores as flota_conductores,
        api_crear_conductor, api_actualizar_conductor, api_eliminar_conductor,
        api_obtener_camiones as flota_camiones,
        api_crear_camion, api_actualizar_camion, api_eliminar_camion,
        api_obtener_mantenimiento, api_crear_mantenimiento,
        api_actualizar_mantenimiento, api_eliminar_mantenimiento,
        api_exportar_mantenimiento_excel
    )
    print("[INFO] Modulo Flota importado")
    inicializar_flota(ARCHIVO_CONDUCTORES, ARCHIVO_CAMIONES, ARCHIVO_MANTENIMIENTO, cargar_json, guardar_json)
    api_funciones['flota'] = {
        'conductores': flota_conductores,
        'crear_conductor': api_crear_conductor,
        'actualizar_conductor': api_actualizar_conductor,
        'eliminar_conductor': api_eliminar_conductor,
        'camiones': flota_camiones,
        'crear_camion': api_crear_camion,
        'actualizar_camion': api_actualizar_camion,
        'eliminar_camion': api_eliminar_camion,
        'mantenimiento': api_obtener_mantenimiento,
        'crear_mantenimiento': api_crear_mantenimiento,
        'actualizar_mantenimiento': api_actualizar_mantenimiento,
        'eliminar_mantenimiento': api_eliminar_mantenimiento,
        'exportar_mantenimiento_excel': api_exportar_mantenimiento_excel
    }
except ImportError as e:
    print(f"[ERROR] Flota: {e}")

# 9. Importar módulo Tablas Editables
try:
    from tablas_editables import (
        inicializar_tablas_editables,
        api_limpiar_por_fechas,
        api_obtener_bitacora,
        api_sincronizar_bitacora,
        api_guardar_tabla_empresas,
        api_cargar_tabla_empresas,
        api_guardar_tabla_pedidos,
        api_cargar_tabla_pedidos,
        api_guardar_tabla_costos,
        api_cargar_tabla_costos,
        api_exportar_excel,
        api_exportar_pdf
    )
    print("[INFO] Modulo Tablas Editables importado")
    inicializar_tablas_editables(ARCHIVO_BITACORA_DATA)
    api_funciones['tablas_editables'] = {
        'limpiar_por_fechas': api_limpiar_por_fechas,
        'obtener_bitacora': api_obtener_bitacora,
        'sincronizar_bitacora': api_sincronizar_bitacora,
        'guardar_empresas': api_guardar_tabla_empresas,
        'cargar_empresas': api_cargar_tabla_empresas,
        'guardar_pedidos': api_guardar_tabla_pedidos,
        'cargar_pedidos': api_cargar_tabla_pedidos,
        'guardar_costos': api_guardar_tabla_costos,
        'cargar_costos': api_cargar_tabla_costos,
        'exportar_excel': api_exportar_excel,
        'exportar_pdf': api_exportar_pdf
    }
except ImportError as e:
    print(f"[ERROR] Tablas Editables: {e}")

# 10. Importar módulo Ubicacion GPS
try:
    from ubicacion import (
        inicializar_ubicacion,
        api_obtener_ubicaciones,
        api_actualizar_ubicacion,
        api_actualizar_estado_vehiculo,
        api_obtener_vehiculo,
        api_sincronizar_con_flota,
        api_ciudades_nicaragua,
        api_vehiculos_cercanos,
        api_obtener_conductores_chat,
        api_mensajes_conductor,
        api_limpiar_mensajes_conductor,
        api_limpiar_todos_mensajes,
        api_eliminar_mensaje,
        api_descargar_archivo_chat
    )
    print("[INFO] Modulo Ubicacion GPS importado")
    inicializar_ubicacion(rutas_config, main_funciones)
    api_funciones['ubicacion'] = {
        'listar': api_obtener_ubicaciones,
        'actualizar': api_actualizar_ubicacion,
        'actualizar_estado': api_actualizar_estado_vehiculo,
        'obtener': api_obtener_vehiculo,
        'sincronizar': api_sincronizar_con_flota,
        'ciudades': api_ciudades_nicaragua,
        'cercanos': api_vehiculos_cercanos,
        'conductores_chat': api_obtener_conductores_chat,
        'mensajes_conductor': api_mensajes_conductor,
        'limpiar_mensajes_conductor': api_limpiar_mensajes_conductor,
        'limpiar_todos_mensajes': api_limpiar_todos_mensajes,
        'eliminar_mensaje': api_eliminar_mensaje,
        'descargar_archivo': api_descargar_archivo_chat
    }
except ImportError as e:
    print(f"[ERROR] Ubicacion GPS: {e}")

# 11. Importar módulo Chat Conductores
try:
    from chat_conductores import (
        inicializar_chat,
        api_registrar_chat,
        api_enviar_mensaje,
        api_obtener_mensajes,
        api_actualizar_ubicacion,
        api_obtener_chats_activos,
        api_obtener_mensajes_globales,
        api_obtener_ubicacion_conductores,
        api_registrar_conductor,
        api_enviar_mensaje_conductor,
        api_obtener_mensajes_conductor,
        api_actualizar_ubicacion_conductor,
        api_obtener_conductores_conectados,
        api_obtener_conductores_con_mensajes,
        api_limpiar_mensajes_conductor as chat_limpiar_mensajes_conductor,
        api_limpiar_todos_mensajes as chat_limpiar_todos_mensajes,
        api_eliminar_mensaje as chat_eliminar_mensaje,
        api_obtener_todos_mensajes,
        api_descargar_archivo
    )
    print("[INFO] Modulo Chat Conductores importado")
    inicializar_chat(main_funciones, rutas_config)
    api_funciones['chat'] = {
        'registrar': api_registrar_chat,
        'enviar': api_enviar_mensaje,
        'obtener': api_obtener_mensajes,
        'actualizar_ubicacion': api_actualizar_ubicacion,
        'chats_activos': api_obtener_chats_activos,
        'mensajes_globales': api_obtener_mensajes_globales,
        'ubicacion_conductores': api_obtener_ubicacion_conductores,
        'registrar_conductor': api_registrar_conductor,
        'enviar_mensaje_conductor': api_enviar_mensaje_conductor,
        'obtener_mensajes_conductor': api_obtener_mensajes_conductor,
        'actualizar_ubicacion_conductor': api_actualizar_ubicacion_conductor,
        'conductores_conectados': api_obtener_conductores_conectados,
        'conductores_con_mensajes': api_obtener_conductores_con_mensajes,
        'limpiar_mensajes_conductor': chat_limpiar_mensajes_conductor,
        'limpiar_todos_mensajes': chat_limpiar_todos_mensajes,
        'eliminar_mensaje': chat_eliminar_mensaje,
        'todos_mensajes': api_obtener_todos_mensajes,
        'descargar_archivo': api_descargar_archivo
    }
except ImportError as e:
    print(f"[ERROR] Chat Conductores: {e}")
    import traceback
    traceback.print_exc()

# ==================== 12. IMPORTAR MÓDULO TOM (CORREGIDO) ====================
try:
    print("[INFO] Intentando importar módulo TOM...")
    print(f"[INFO] Ruta de búsqueda: {sys.path}")
    
    from tom import (
        api_tom_dashboard,
        api_tom_empresas,
        api_tom_empresa,
        api_tom_pedidos,
        api_tom_facturas,
        api_tom_estadisticas,
        api_tom_resumen,
        api_tom_hablar,
        api_tom_preguntar,
        api_tom_buscar,
        api_tom_costos_traslado,
        api_tom_conductores,
        api_tom_camiones,
        api_tom_usuarios,
        api_tom_sistema_archivos,
        api_tom_sistema_leer,
        api_tom_sistema_buscar,
        api_tom_sistema_estructura,
        api_tom_soporte,
        api_tom_clientes
    )
    print("[TOM] ✅ Módulo TOM importado correctamente!")
    
    api_funciones['tom'] = {
        'dashboard': api_tom_dashboard,
        'empresas': api_tom_empresas,
        'empresa': api_tom_empresa,
        'pedidos': api_tom_pedidos,
        'facturas': api_tom_facturas,
        'estadisticas': api_tom_estadisticas,
        'resumen': api_tom_resumen,
        'hablar': api_tom_hablar,
        'preguntar': api_tom_preguntar,
        'buscar': api_tom_buscar,
        'costos': api_tom_costos_traslado,
        'conductores': api_tom_conductores,
        'camiones': api_tom_camiones,
        'usuarios': api_tom_usuarios,
        'sistema_archivos': api_tom_sistema_archivos,
        'sistema_leer': api_tom_sistema_leer,
        'sistema_buscar': api_tom_sistema_buscar,
        'sistema_estructura': api_tom_sistema_estructura,
        'soporte': api_tom_soporte,
        'clientes': api_tom_clientes
    }
    print("[TOM] ✅ Funciones de TOM registradas en API")
    
except ImportError as e:
    print(f"[ERROR] TOM - ImportError: {e}")
    print("[ERROR] Verifica que tom.py exista en modulos_py/ o en el directorio actual")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"[ERROR] TOM - Error inesperado: {e}")
    import traceback
    traceback.print_exc()

# 13. Importar módulo Editor Visual
try:
    from editor_visual import (
        inicializar_editor,
        api_listar_paginas_editor,
        api_obtener_pagina_editor,
        api_guardar_pagina_editor,
        api_previsualizar_pagina
    )
    print("[INFO] Modulo Editor Visual importado")
    try:
        inicializar_editor(api_funciones.get('paginas', None))
    except:
        pass
    api_funciones['editor_visual'] = {
        'listar_paginas': api_listar_paginas_editor,
        'obtener_pagina': api_obtener_pagina_editor,
        'guardar_pagina': api_guardar_pagina_editor,
        'previsualizar': api_previsualizar_pagina
    }
except ImportError as e:
    print(f"[ERROR] Editor Visual: {e}")

# ==================== RUTAS DEL SERVIDOR PUBLICO ====================
@app.route('/fijo')
def pagina_servidor_fijo():
    try:
        if SERVIDOR_PUBLICO_DISPONIBLE:
            info = obtener_info_servidor()
            ip_publica = info.get('ip_publica', 'No disponible')
            ultima_act = info.get('ultima_actualizacion', datetime.now().isoformat())
            id_fijo = info.get('id', ID_FIJO)
        else:
            ip_publica = 'No disponible'
            ultima_act = datetime.now().isoformat()
            id_fijo = 'NO-DISPONIBLE'
        
        url_publica = URL_CLOUDFLARE or obtener_url_publica() or "http://127.0.0.1:5000"
        url_con_id = obtener_url_con_id() if SERVIDOR_PUBLICO_DISPONIBLE else None
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Servidor Fijo - Grupo GSN</title>
        <style>
            *{{margin:0;padding:0;box-sizing:border-box;}}
            body{{font-family:system-ui,sans-serif;background:#0a0f1c;color:#34d399;min-height:100vh;display:flex;justify-content:center;align-items:center;padding:20px;}}
            .container{{max-width:600px;width:100%;background:rgba(10,26,10,0.05);backdrop-filter:blur(30px);border-radius:28px;border:1px solid rgba(16,185,129,0.05);padding:40px 30px;text-align:center;animation:fadeIn 0.5s ease;}}
            @keyframes fadeIn{{from{{opacity:0;transform:translateY(20px);}}to{{opacity:1;transform:translateY(0);}}}}
            .logo{{font-size:3rem;margin-bottom:15px;}}
            .badge-fijo{{background:rgba(245,158,11,0.1);color:#f59e0b;padding:4px 14px;border-radius:20px;font-size:0.6rem;font-weight:600;border:1px solid rgba(245,158,11,0.1);display:inline-block;margin-bottom:10px;}}
            h1{{font-size:1.5rem;color:#10b981;margin-bottom:5px;}}
            .subtitle{{font-size:0.8rem;opacity:0.3;margin-bottom:20px;}}
            .id-box{{background:rgba(16,185,129,0.05);padding:15px 20px;border-radius:16px;font-family:monospace;font-size:2rem;color:#10b981;letter-spacing:4px;border:2px solid rgba(16,185,129,0.1);margin:15px 0;}}
            .id-box .label{{font-size:0.6rem;text-transform:uppercase;letter-spacing:2px;color:#34d399;opacity:0.3;display:block;margin-bottom:5px;}}
            .id-box .fijo-label{{font-size:0.5rem;color:#f59e0b;opacity:0.6;display:block;margin-top:5px;}}
            .enlace-publico{{background:rgba(16,185,129,0.05);padding:12px 16px;border-radius:12px;border:1px solid rgba(16,185,129,0.1);margin:10px 0;word-break:break-all;}}
            .enlace-publico .label{{font-size:0.55rem;text-transform:uppercase;letter-spacing:1px;color:#34d399;opacity:0.3;display:block;margin-bottom:4px;}}
            .enlace-publico .value{{font-size:0.85rem;color:#f59e0b;font-family:monospace;}}
            .grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:20px 0;}}
            .grid .item{{background:rgba(16,185,129,0.03);padding:12px;border-radius:12px;border:1px solid rgba(16,185,129,0.03);}}
            .grid .item .label{{font-size:0.55rem;text-transform:uppercase;letter-spacing:1px;color:#34d399;opacity:0.3;}}
            .grid .item .value{{font-size:0.85rem;font-weight:600;margin-top:4px;color:#10b981;word-break:break-all;}}
            .grid .item .value.ip-actual{{color:#f59e0b;font-size:0.9rem;}}
            .status{{display:inline-block;padding:4px 14px;border-radius:20px;font-size:0.7rem;font-weight:600;background:rgba(16,185,129,0.1);color:#34d399;}}
            .status.online{{background:rgba(16,185,129,0.15);color:#34d399;animation:pulse 2s infinite;}}
            @keyframes pulse{{0%,100%{{opacity:1;}}50%{{opacity:0.6;}}}}
            .btn{{display:inline-block;padding:14px 30px;margin:8px 5px;background:linear-gradient(135deg,#10b981,#059669);border:none;border-radius:40px;color:white;text-decoration:none;font-weight:600;font-size:0.9rem;cursor:pointer;transition:all 0.3s ease;}}
            .btn:hover{{transform:translateY(-2px);box-shadow:0 8px 25px rgba(16,185,129,0.3);}}
            .btn-secondary{{background:transparent;border:1px solid rgba(16,185,129,0.1);color:#34d399;}}
            .btn-secondary:hover{{background:rgba(16,185,129,0.05);}}
            .conectar-area{{margin-top:25px;padding-top:25px;border-top:1px solid rgba(16,185,129,0.05);}}
            .conectar-area input{{width:100%;padding:14px 18px;background:rgba(10,26,10,0.05);border:1px solid rgba(16,185,129,0.05);border-radius:14px;color:#34d399;font-size:1.1rem;text-align:center;font-family:monospace;letter-spacing:2px;margin-bottom:12px;}}
            .conectar-area input:focus{{outline:none;border-color:rgba(16,185,129,0.1);}}
            .conectar-area input::placeholder{{color:#34d399;opacity:0.2;}}
            .info{{margin-top:20px;font-size:0.6rem;color:#34d399;opacity:0.15;}}
            .ultima-act{{font-size:0.55rem;color:#34d399;opacity:0.2;margin-top:5px;}}
            .mensaje-conexion{{margin-top:12px;font-size:0.8rem;min-height:20px;color:#fbbf24;}}
            .mensaje-conexion.error{{color:#f87171;}}
            .mensaje-conexion.ok{{color:#34d399;}}
            .copy-btn{{background:rgba(16,185,129,0.05);border:none;color:#34d399;padding:4px 12px;border-radius:8px;cursor:pointer;font-size:0.7rem;margin-left:8px;}}
            .copy-btn:hover{{background:rgba(16,185,129,0.1);}}
            @media(max-width:480px){{.container{{padding:25px 18px;}}.id-box{{font-size:1.4rem;}}.grid{{grid-template-columns:1fr;}}}}
        </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">🔒</div>
                <div class="badge-fijo">ID FIJO - NUNCA CAMBIA</div>
                <h1>Servidor Fijo</h1>
                <p class="subtitle">Conéctate desde cualquier red usando tu ID</p>
                <div class="id-box"><span class="label">🆔 TU ID FIJO</span>{id_fijo}<span class="fijo-label">🔒 Este ID es permanente</span></div>
                <div class="enlace-publico"><span class="label">🌐 ENLACE PÚBLICO (Comparte con otros)</span><div class="value" id="enlacePublico">{url_publica or 'No disponible'}</div><button class="copy-btn" onclick="copiarEnlace()">📋 Copiar enlace</button></div>
                <div class="enlace-publico" style="border-color:rgba(245,158,11,0.2);"><span class="label">🔗 ENLACE DIRECTO CON TU ID</span><div class="value" id="enlaceDirecto" style="font-size:0.7rem;color:#fbbf24;">{url_con_id or 'No disponible'}</div><button class="copy-btn" onclick="copiarEnlaceDirecto()">📋 Copiar</button></div>
                <div><span class="status online">🟢 Servidor activo</span></div>
                <div class="grid">
                    <div class="item"><div class="label">IP Pública Actual</div><div class="value ip-actual" id="ipPublica">{ip_publica}</div></div>
                    <div class="item"><div class="label">Puerto</div><div class="value">{5000}</div></div>
                    <div class="item"><div class="label">Estado</div><div class="value" style="color:#34d399;">✅ Activo</div></div>
                    <div class="item"><div class="label">Última Actualización</div><div class="value" style="font-size:0.7rem;">{ultima_act[:19]}</div></div>
                </div>
                <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;"><a href="/" class="btn">🏠 Ir al Sistema</a><button class="btn btn-secondary" onclick="copiarID()">📋 Copiar ID</button></div>
                <div class="conectar-area"><p style="font-size:0.8rem; opacity:0.3; margin-bottom:12px;">🔗 Conectar a otro dispositivo por ID</p><input type="text" id="idBuscar" placeholder="Ingresa el ID del otro dispositivo" value=""><button class="btn" onclick="conectarPorID()" style="width:100%;">🔗 Conectar</button><div id="mensajeConexion" class="mensaje-conexion"></div></div>
                <div class="ultima-act">🕐 Última actualización: {ultima_act}</div>
                <div class="info">Grupo GSN - ID Fijo | {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
            </div>
            <script>
                function copiarID(){{const id="{id_fijo}";navigator.clipboard.writeText(id).then(()=>{{const btn=event.target;btn.textContent='✅ Copiado!';setTimeout(()=>btn.textContent='📋 Copiar ID',2000);}});}}
                function copiarEnlace(){{const texto=document.getElementById('enlacePublico').textContent;navigator.clipboard.writeText(texto).then(()=>{{const btn=event.target;btn.textContent='✅ Copiado!';setTimeout(()=>btn.textContent='📋 Copiar enlace',2000);}});}}
                function copiarEnlaceDirecto(){{const texto=document.getElementById('enlaceDirecto').textContent;navigator.clipboard.writeText(texto).then(()=>{{const btn=event.target;btn.textContent='✅ Copiado!';setTimeout(()=>btn.textContent='📋 Copiar',2000);}});}}
                function conectarPorID(){{const input=document.getElementById('idBuscar');const id=input.value.trim().toUpperCase();const msg=document.getElementById('mensajeConexion');if(!id){{msg.textContent='⚠️ Ingresa un ID válido';msg.className='mensaje-conexion error';return;}}msg.textContent='🔄 Buscando dispositivo...';msg.className='mensaje-conexion';fetch('/api/servidor_publico/validar/'+id).then(res=>res.json()).then(data=>{{if(data.ok&&data.valido){{msg.innerHTML='✅ Conectado a <strong>'+data.dispositivo.nombre+'</strong><br>📡 IP: '+data.dispositivo.ip_publica;msg.className='mensaje-conexion ok';setTimeout(()=>{{window.location.href='/?conectar='+id;}},1500);}}else{{msg.textContent='❌ ID no válido o dispositivo inactivo';msg.className='mensaje-conexion error';}}}}).catch(err=>{{msg.textContent='❌ Error: '+err.message;msg.className='mensaje-conexion error';}});}}
                document.getElementById('idBuscar').addEventListener('keypress',function(e){{if(e.key==='Enter')conectarPorID();}});
            </script>
        </body>
        </html>
        """
    except Exception as e:
        return f"<h1>Error</h1><p>{e}</p>", 500

# ==================== RUTAS API - SERVIDOR PUBLICO ====================
@app.route('/api/servidor_publico/info', methods=['GET', 'OPTIONS'])
def api_servidor_publico_info():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        if SERVIDOR_PUBLICO_DISPONIBLE:
            info = obtener_info_servidor()
            return jsonify({
                "ok": True,
                "id": info.get("id"),
                "nombre": info.get("nombre"),
                "ip_publica": info.get("ip_publica"),
                "ip_local": info.get("ip_local"),
                "puerto": info.get("puerto"),
                "ultima_actualizacion": info.get("ultima_actualizacion"),
                "url": URL_CLOUDFLARE or obtener_url_publica(),
                "url_con_id": obtener_url_con_id()
            })
        return jsonify({"ok": False, "error": "Servidor Público no disponible"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route('/api/servidor_publico/validar/<id_dispositivo>', methods=['GET', 'OPTIONS'])
def api_servidor_publico_validar(id_dispositivo):
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        if not SERVIDOR_PUBLICO_DISPONIBLE:
            return jsonify({"ok": False, "error": "Servidor Público no disponible"})
        dispositivo = validar_dispositivo(id_dispositivo)
        if dispositivo:
            return jsonify({"ok": True, "valido": True, "activo": dispositivo.get("activo", True), "dispositivo": dispositivo})
        return jsonify({"ok": True, "valido": False})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==================== RUTAS API - CLOUDFLARE ====================
@app.route('/api/cloudflare_url', methods=['GET', 'OPTIONS'])
def api_cloudflare_url():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    global URL_CLOUDFLARE
    try:
        url = URL_CLOUDFLARE or obtener_url_publica()
        if url:
            return jsonify({"ok": True, "activo": True, "url": url})
        return jsonify({"ok": True, "activo": False, "url": None})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "activo": False, "url": None})

@app.route('/api/estado_cloudflare', methods=['GET', 'OPTIONS'])
def api_estado_cloudflare():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    global URL_CLOUDFLARE
    try:
        url_publica = URL_CLOUDFLARE or obtener_url_publica()
        if url_publica:
            return jsonify({"ok": True, "activo": True, "tunel_activo": True, "url_publica": url_publica, "id": ID_FIJO, "mensaje": "Túnel activo"})
        return jsonify({"ok": True, "activo": False, "tunel_activo": False, "url_publica": None, "mensaje": "Túnel no activo"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route('/api/listar_enlaces', methods=['GET', 'OPTIONS'])
def api_listar_enlaces():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    global URL_CLOUDFLARE
    try:
        enlaces = [{"id": "local", "nombre": "Enlace Local", "url": "http://127.0.0.1:5000", "activo": True, "tipo": "local"}]
        if SERVIDOR_PUBLICO_DISPONIBLE:
            url_publica = obtener_url_publica()
            url_con_id = obtener_url_con_id()
            if url_publica:
                enlaces.append({"id": "publico", "nombre": "Enlace Público", "url": url_publica, "activo": True, "tipo": "publico"})
            if url_con_id:
                enlaces.append({"id": "fijo", "nombre": "Enlace con ID Fijo", "url": url_con_id, "activo": True, "tipo": "fijo"})
        if URL_CLOUDFLARE:
            enlaces.append({"id": "cloudflare", "nombre": "Túnel Cloudflare", "url": URL_CLOUDFLARE, "activo": True, "tipo": "cloudflare"})
        return jsonify({"ok": True, "enlaces": enlaces, "total": len(enlaces)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "enlaces": []})

@app.route('/api/iniciar_cloudflare', methods=['POST', 'OPTIONS'])
def api_iniciar_cloudflare():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        iniciar_cloudflared()
        if URL_CLOUDFLARE:
            return jsonify({"ok": True, "url": URL_CLOUDFLARE, "mensaje": "Túnel iniciado"})
        return jsonify({"ok": True, "mensaje": "Túnel iniciando... espera unos segundos"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route('/api/detener_cloudflare', methods=['POST', 'OPTIONS'])
def api_detener_cloudflare():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        detener_cloudflared()
        return jsonify({"ok": True, "mensaje": "Túnel detenido"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==================== RUTAS API - PERMISOS FACTURAS ====================
@app.route('/api/obtener_permisos_facturas', methods=['GET', 'OPTIONS'])
def api_obtener_permisos_facturas():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        permisos = cargar_json(ARCHIVO_PERMISOS_FACTURAS, {})
        return jsonify({"ok": True, "permisos": permisos})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "permisos": {}})

@app.route('/api/actualizar_permiso_factura', methods=['POST', 'OPTIONS'])
def api_actualizar_permiso_factura():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        data = request.get_json()
        factura_id = data.get('factura_id')
        permitido = data.get('permitido', False)
        
        if not factura_id:
            return jsonify({"ok": False, "error": "factura_id requerido"})
        
        permisos = cargar_json(ARCHIVO_PERMISOS_FACTURAS, {})
        permisos[factura_id] = permitido
        guardar_json(ARCHIVO_PERMISOS_FACTURAS, permisos)
        
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route('/api/facturas_permitidas/<empresa_id>', methods=['GET', 'OPTIONS'])
def api_facturas_permitidas(empresa_id):
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        facturas = cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
        permisos = cargar_json(ARCHIVO_PERMISOS_FACTURAS, {})
        
        facturas_permitidas = []
        for f in facturas.get("facturas", []):
            if f.get("empresa_id") == empresa_id or f.get("empresa_nombre") == empresa_id:
                if permisos.get(f.get("id"), False):
                    facturas_permitidas.append(f)
        
        facturas_permitidas.sort(key=lambda x: x.get('fecha_emision', ''), reverse=True)
        
        return jsonify({"ok": True, "facturas": facturas_permitidas})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "facturas": []})

# ==================== RUTAS API - PEDIDOS COMBUSTIBLE ====================
@app.route('/api/pedidos_combustible', methods=['GET', 'OPTIONS'])
def api_pedidos_combustible():
    if request.method == 'OPTIONS':
        response = jsonify({"ok": True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response
    
    try:
        pedidos = cargar_json(ARCHIVO_PEDIDOS, [])
        return jsonify({"ok": True, "pedidos": pedidos})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "pedidos": []})

# ==================== RUTAS API - CLIENTES UNIFICADO ====================
@app.route('/api/clientes', methods=['GET', 'OPTIONS'])
def api_clientes_unificado():
    if request.method == 'OPTIONS':
        response = jsonify({"ok": True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response
    
    try:
        clientes_data = cargar_json(ARCHIVO_CLIENTES, {"clientes": []})
        clientes = clientes_data.get("clientes", [])
        
        empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
        empresas = empresas_data.get("empresas", [])
        
        clientes_unificados = []
        ids_vistos = set()
        
        for c in clientes:
            if c.get("id") and c.get("id") not in ids_vistos:
                ids_vistos.add(c.get("id"))
                c_limpio = {
                    "id": c.get("id"),
                    "nombre": c.get("nombre", "Cliente"),
                    "contacto": c.get("contacto", ""),
                    "telefono": c.get("telefono", ""),
                    "email": c.get("email", ""),
                    "direccion": c.get("direccion", ""),
                    "origen": c.get("origen", ""),
                    "destino": c.get("destino", ""),
                    "distancia": c.get("distancia", 0),
                    "placa": c.get("placa", ""),
                    "conductor": c.get("conductor", ""),
                    "credito": c.get("credito", 0),
                    "limite_credito": c.get("limite_credito", 0),
                    "diesel": c.get("diesel", 0),
                    "diesel_max": c.get("diesel_max", 0),
                    "gasolina": c.get("gasolina", 0),
                    "gasolina_max": c.get("gasolina_max", 0),
                    "bono1": c.get("bono1", ""),
                    "bono2": c.get("bono2", ""),
                    "viatico1": c.get("viatico1", 0),
                    "viatico2": c.get("viatico2", 0),
                    "traslado": c.get("traslado", 0),
                    "activo": c.get("activo", True),
                    "tipo": c.get("tipo", "Cliente"),
                    "fecha_registro": c.get("fecha_registro", datetime.now().isoformat())
                }
                clientes_unificados.append(c_limpio)
        
        for e in empresas:
            if e.get("id") and e.get("id") not in ids_vistos:
                ids_vistos.add(e.get("id"))
                e_limpio = {
                    "id": e.get("id"),
                    "nombre": e.get("nombre", "Empresa"),
                    "contacto": e.get("contacto", ""),
                    "telefono": e.get("telefono", ""),
                    "email": e.get("email", ""),
                    "direccion": e.get("direccion", ""),
                    "origen": e.get("origen", ""),
                    "destino": e.get("destino", ""),
                    "distancia": e.get("distancia_km", 0),
                    "placa": e.get("placa", ""),
                    "conductor": e.get("conductor", ""),
                    "credito": e.get("credito", 0),
                    "limite_credito": e.get("limite_credito", 0),
                    "diesel": e.get("precio_diesel", 0),
                    "diesel_max": e.get("precio_diesel_max", 0),
                    "gasolina": e.get("precio_gasolina", 0),
                    "gasolina_max": e.get("precio_gasolina_max", 0),
                    "bono1": e.get("bono1", ""),
                    "bono2": e.get("bono2", ""),
                    "viatico1": e.get("viatico1", 0),
                    "viatico2": e.get("viatico2", 0),
                    "traslado": e.get("costo_traslado", 0),
                    "activo": e.get("activo", True),
                    "tipo": e.get("tipo", "Empresa"),
                    "fecha_registro": e.get("fecha_registro", datetime.now().isoformat())
                }
                clientes_unificados.append(e_limpio)
        
        return jsonify({
            "ok": True,
            "clientes": clientes_unificados,
            "total": len(clientes_unificados)
        })
    except Exception as e:
        print(f"[ERROR] api_clientes_unificado: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e), "clientes": []})

# ==================== RUTAS API - CREAR PEDIDO ====================
@app.route('/api/primogenito/crear_pedido', methods=['POST', 'OPTIONS'])
def api_primogenito_crear_pedido():
    if request.method == 'OPTIONS':
        response = jsonify({"ok": True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept, X-User-Data')
        return response
    
    try:
        data = request.get_json()
        print(f"[PRIMOGENITO] Recibiendo pedido: {data}")
        
        cliente_id = data.get('cliente_id')
        if not cliente_id:
            return jsonify({"ok": False, "error": "cliente_id es requerido"})
        
        galones = float(data.get('galones', 0))
        if galones <= 0:
            return jsonify({"ok": False, "error": "Cantidad de galones inválida"})
        
        tipo_combustible = data.get('tipo_combustible')
        if not tipo_combustible:
            return jsonify({"ok": False, "error": "Tipo de combustible requerido"})
        
        clientes_data = cargar_json(ARCHIVO_CLIENTES, {"clientes": []})
        cliente = None
        for c in clientes_data.get("clientes", []):
            if c.get("id") == cliente_id:
                cliente = c
                break
        
        if not cliente:
            empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
            for e in empresas_data.get("empresas", []):
                if e.get("id") == cliente_id:
                    cliente = e
                    break
        
        if not cliente:
            return jsonify({"ok": False, "error": f"Cliente no encontrado: {cliente_id}"})
        
        precios = {
            "DIESEL": float(cliente.get('diesel', cliente.get('precio_diesel', 0))),
            "DIESEL_PREMIUM": float(cliente.get('diesel_max', cliente.get('precio_diesel_max', 0))),
            "GASOLINA": float(cliente.get('gasolina', cliente.get('precio_gasolina', 0))),
            "GASOLINA_PREMIUM": float(cliente.get('gasolina_max', cliente.get('precio_gasolina_max', 0)))
        }
        
        precio_galon = precios.get(tipo_combustible, 0)
        if precio_galon <= 0:
            return jsonify({"ok": False, "error": f"Precio no configurado para {tipo_combustible}"})
        
        costo_combustible = galones * precio_galon
        costo_traslado = float(cliente.get('traslado', cliente.get('costo_traslado', 0)))
        costo_total = costo_combustible + costo_traslado
        
        credito_actual = float(cliente.get('credito', 0))
        limite_credito = float(cliente.get('limite_credito', 0))
        
        if limite_credito > 0 and (credito_actual + costo_total) > limite_credito:
            return jsonify({
                "ok": False, 
                "error": "Crédito insuficiente",
                "credito_actual": credito_actual,
                "limite_credito": limite_credito,
                "costo_total": costo_total,
                "disponible": limite_credito - credito_actual
            })
        
        nuevo_id = f"PED-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"
        
        nuevo_pedido = {
            "id": nuevo_id,
            "empresa_id": cliente_id,
            "nombre": cliente.get("nombre", "Cliente"),
            "origen": cliente.get("origen", data.get('origen', 'Managua')),
            "destino": cliente.get("destino", data.get('destino', 'León')),
            "tipo_combustible": tipo_combustible,
            "galones": galones,
            "precio_por_galon": round(precio_galon, 2),
            "costo_combustible": round(costo_combustible, 2),
            "costo_traslado": round(costo_traslado, 2),
            "costo_total": round(costo_total, 2),
            "iva": round(costo_total * 0.19, 2),
            "importe": round(costo_total * 1.19, 2),
            "facturado": False,
            "estado_operacion": "espera",
            "conductor_asignado": cliente.get("conductor", ""),
            "camion_asignado": cliente.get("placa", ""),
            "bono1": cliente.get("bono1", ""),
            "bono2": cliente.get("bono2", ""),
            "viatico1": float(cliente.get("viatico1", 0)),
            "viatico2": float(cliente.get("viatico2", 0)),
            "fecha": datetime.now().isoformat(),
            "fecha_str": datetime.now().strftime("%Y-%m-%d"),
            "es_prioritario": True,
            "dispositivo": "primogenito_apk",
            "origen_pedido": "primogenito_apk",
            "ubicacion_pedido": data.get('ubicacion_pedido'),
            "observacion": data.get('observacion', "Pedido desde APK Primogénito"),
            "credito_antes": credito_actual,
            "credito_despues": credito_actual + costo_total
        }
        
        pedidos = cargar_json(ARCHIVO_PEDIDOS, [])
        pedidos.append(nuevo_pedido)
        guardar_json(ARCHIVO_PEDIDOS, pedidos)
        
        cliente['credito'] = round(credito_actual + costo_total, 2)
        guardar_json(ARCHIVO_CLIENTES, clientes_data)
        
        registrar_bitacora(
            "primogenito_apk",
            "Crear Pedido Prioritario",
            f"ID: {nuevo_id} - {cliente.get('nombre')} - {galones} gal - {tipo_combustible} - Total: C${round(costo_total, 2)}",
            "Primogénito"
        )
        
        print(f"[PRIMOGENITO] ✅ Pedido {nuevo_id} creado desde APK")
        
        return jsonify({
            "ok": True,
            "pedido": nuevo_pedido,
            "mensaje": "Pedido prioritario creado correctamente",
            "credito_actual": round(credito_actual + costo_total, 2)
        })
        
    except Exception as e:
        print(f"[ERROR] api_primogenito_crear_pedido: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

# ==================== RUTAS PRIMOGÉNITO - OBTENER CLIENTE ====================
@app.route('/api/primogenito/cliente/<cliente_id>', methods=['GET', 'OPTIONS'])
def api_primogenito_obtener_cliente(cliente_id):
    if request.method == 'OPTIONS':
        response = jsonify({"ok": True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response
    
    try:
        clientes_data = cargar_json(ARCHIVO_CLIENTES, {"clientes": []})
        cliente = None
        for c in clientes_data.get("clientes", []):
            if c.get("id") == cliente_id:
                cliente = c
                break
        
        if not cliente:
            empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
            for e in empresas_data.get("empresas", []):
                if e.get("id") == cliente_id:
                    cliente = e
                    break
        
        if not cliente:
            return jsonify({"ok": False, "error": "Cliente no encontrado"})
        
        datos_cliente = {
            "id": cliente.get("id"),
            "nombre": cliente.get("nombre"),
            "origen": cliente.get("origen", ""),
            "destino": cliente.get("destino", ""),
            "distancia": float(cliente.get("distancia", cliente.get("distancia_km", 0))),
            "placa": cliente.get("placa", ""),
            "conductor": cliente.get("conductor", ""),
            "credito": float(cliente.get("credito", 0)),
            "limite_credito": float(cliente.get("limite_credito", 0)),
            "diesel": float(cliente.get("diesel", cliente.get("precio_diesel", 0))),
            "diesel_max": float(cliente.get("diesel_max", cliente.get("precio_diesel_max", 0))),
            "gasolina": float(cliente.get("gasolina", cliente.get("precio_gasolina", 0))),
            "gasolina_max": float(cliente.get("gasolina_max", cliente.get("precio_gasolina_max", 0))),
            "bono1": cliente.get("bono1", ""),
            "bono2": cliente.get("bono2", ""),
            "viatico1": float(cliente.get("viatico1", 0)),
            "viatico2": float(cliente.get("viatico2", 0)),
            "traslado": float(cliente.get("traslado", cliente.get("costo_traslado", 0))),
            "activo": cliente.get("activo", True)
        }
        
        return jsonify({"ok": True, "cliente": datos_cliente})
    except Exception as e:
        print(f"[ERROR] api_primogenito_obtener_cliente: {e}")
        return jsonify({"ok": False, "error": str(e)})

# ==================== RUTAS API - CREAR PEDIDO (GENERAL) ====================
@app.route('/api/crear_pedido', methods=['POST', 'OPTIONS'])
def api_crear_pedido():
    if request.method == 'OPTIONS':
        response = jsonify({"ok": True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response
    
    try:
        data = request.get_json()
        print(f"[DEBUG] Creando pedido: {data}")
        
        cliente_id = data.get('cliente_id')
        if not cliente_id:
            return jsonify({"ok": False, "error": "cliente_id es requerido"})
        
        galones = float(data.get('galones', 0))
        if galones <= 0:
            return jsonify({"ok": False, "error": "Cantidad de galones inválida"})
        
        tipo_combustible = data.get('tipo_combustible')
        if not tipo_combustible:
            return jsonify({"ok": False, "error": "Tipo de combustible requerido"})
        
        clientes_data = cargar_json(ARCHIVO_CLIENTES, {"clientes": []})
        cliente = None
        for c in clientes_data.get("clientes", []):
            if c.get("id") == cliente_id:
                cliente = c
                break
        
        if not cliente:
            empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
            for e in empresas_data.get("empresas", []):
                if e.get("id") == cliente_id:
                    cliente = e
                    break
        
        if not cliente:
            return jsonify({"ok": False, "error": "Cliente no encontrado"})
        
        precios = {
            "DIESEL": float(cliente.get('diesel', cliente.get('precio_diesel', 0))),
            "DIESEL_PREMIUM": float(cliente.get('diesel_max', cliente.get('precio_diesel_max', 0))),
            "GASOLINA": float(cliente.get('gasolina', cliente.get('precio_gasolina', 0))),
            "GASOLINA_PREMIUM": float(cliente.get('gasolina_max', cliente.get('precio_gasolina_max', 0)))
        }
        
        precio_galon = precios.get(tipo_combustible, 0)
        if precio_galon <= 0:
            return jsonify({"ok": False, "error": f"Precio no configurado para {tipo_combustible}"})
        
        costo_combustible = galones * precio_galon
        costo_traslado = float(cliente.get('traslado', cliente.get('costo_traslado', 0)))
        costo_total = costo_combustible + costo_traslado
        
        nuevo_id = f"PED-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"
        
        nuevo_pedido = {
            "id": nuevo_id,
            "empresa_id": cliente_id,
            "nombre": cliente.get("nombre", "Cliente"),
            "origen": cliente.get("origen", "Managua"),
            "destino": cliente.get("destino", "León"),
            "tipo_combustible": tipo_combustible,
            "galones": galones,
            "precio_por_galon": round(precio_galon, 2),
            "costo_combustible": round(costo_combustible, 2),
            "costo_traslado": round(costo_traslado, 2),
            "costo_total": round(costo_total, 2),
            "iva": round(costo_total * 0.19, 2),
            "importe": round(costo_total * 1.19, 2),
            "facturado": False,
            "estado_operacion": "espera",
            "conductor_asignado": cliente.get("conductor", ""),
            "camion_asignado": cliente.get("placa", ""),
            "fecha": datetime.now().isoformat(),
            "fecha_str": datetime.now().strftime("%Y-%m-%d"),
            "es_prioritario": data.get('es_prioritario', False),
            "dispositivo": data.get('dispositivo', 'web'),
            "ubicacion_pedido": data.get('ubicacion_pedido'),
            "observacion": data.get('observacion', "")
        }
        
        pedidos = cargar_json(ARCHIVO_PEDIDOS, [])
        pedidos.append(nuevo_pedido)
        guardar_json(ARCHIVO_PEDIDOS, pedidos)
        
        registrar_bitacora(
            data.get('usuario', 'cliente'),
            "Crear Pedido",
            f"ID: {nuevo_id} - {cliente.get('nombre')} - {galones} gal - {'⭐ PRIORITARIO' if data.get('es_prioritario') else ''}",
            "Pedidos"
        )
        
        return jsonify({
            "ok": True,
            "pedido": nuevo_pedido,
            "mensaje": "Pedido creado correctamente"
        })
        
    except Exception as e:
        print(f"[ERROR] api_crear_pedido: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

# ==================== RUTAS API - RECEPCION ====================
@app.route('/api/pedidos_recientes', methods=['GET', 'OPTIONS'])
def api_pedidos_recientes_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'recepcion' in api_funciones and 'pedidos_recientes' in api_funciones['recepcion']:
        return api_funciones['recepcion']['pedidos_recientes']()
    return jsonify({"ok": False, "pedidos": []})

@app.route('/api/estadisticas_recepcion', methods=['GET', 'OPTIONS'])
def api_estadisticas_recepcion_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'recepcion' in api_funciones and 'estadisticas' in api_funciones['recepcion']:
        return api_funciones['recepcion']['estadisticas']()
    return jsonify({"ok": False})

@app.route('/api/datos_graficas', methods=['GET', 'OPTIONS'])
def api_datos_graficas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'recepcion' in api_funciones and 'datos_graficas' in api_funciones['recepcion']:
        return api_funciones['recepcion']['datos_graficas']()
    return jsonify({"ok": False})

@app.route('/api/forzar_actualizacion', methods=['GET', 'POST', 'OPTIONS'])
def api_forzar_actualizacion_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'recepcion' in api_funciones and 'forzar_actualizacion' in api_funciones['recepcion']:
        return api_funciones['recepcion']['forzar_actualizacion']()
    return jsonify({"ok": False})

@app.route('/api/obtener_pedidos_actualizados', methods=['GET', 'OPTIONS'])
def api_obtener_pedidos_actualizados_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'recepcion' in api_funciones and 'pedidos_actualizados' in api_funciones['recepcion']:
        return api_funciones['recepcion']['pedidos_actualizados']()
    return jsonify({"ok": False, "pedidos": [], "pendientes": 0, "camino": 0, "entregados": 0})

@app.route('/api/obtener_pedidos_pendientes', methods=['GET', 'OPTIONS'])
def api_obtener_pedidos_pendientes_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'recepcion' in api_funciones and 'pedidos_pendientes' in api_funciones['recepcion']:
        return api_funciones['recepcion']['pedidos_pendientes']()
    return jsonify({"ok": False, "pedidos": []})

@app.route('/api/obtener_pedidos_camino', methods=['GET', 'OPTIONS'])
def api_obtener_pedidos_camino_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'recepcion' in api_funciones and 'pedidos_camino' in api_funciones['recepcion']:
        return api_funciones['recepcion']['pedidos_camino']()
    return jsonify({"ok": False, "pedidos": []})

@app.route('/api/obtener_pedidos_entregados', methods=['GET', 'OPTIONS'])
def api_obtener_pedidos_entregados_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'recepcion' in api_funciones and 'pedidos_entregados' in api_funciones['recepcion']:
        return api_funciones['recepcion']['pedidos_entregados']()
    return jsonify({"ok": False, "pedidos": []})

@app.route('/api/obtener_todas_observaciones', methods=['GET', 'OPTIONS'])
def api_obtener_todas_observaciones_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'recepcion' in api_funciones and 'obtener_todas_observaciones' in api_funciones['recepcion']:
        return api_funciones['recepcion']['obtener_todas_observaciones']()
    return jsonify({"ok": False, "observaciones": {}})

# ==================== RUTAS API - PAGINAS ====================
@app.route('/api/paginas', methods=['GET', 'OPTIONS'])
def api_paginas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'paginas' in api_funciones:
        return api_funciones['paginas']['listar']()
    return jsonify({"paginas": []})

@app.route('/api/crear_pagina', methods=['POST', 'OPTIONS'])
def api_crear_pagina_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'paginas' in api_funciones:
        return api_funciones['paginas']['crear']()
    return jsonify({"ok": False})

@app.route('/api/eliminar_pagina', methods=['POST', 'OPTIONS'])
def api_eliminar_pagina_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'paginas' in api_funciones:
        return api_funciones['paginas']['eliminar']()
    return jsonify({"ok": False})

@app.route('/api/obtener_pagina/<id_pagina>', methods=['GET', 'OPTIONS'])
def api_obtener_pagina_route(id_pagina):
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'paginas' in api_funciones and 'obtener' in api_funciones['paginas']:
        return api_funciones['paginas']['obtener'](id_pagina)
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/actualizar_pagina', methods=['POST', 'OPTIONS'])
def api_actualizar_pagina_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'paginas' in api_funciones and 'actualizar' in api_funciones['paginas']:
        return api_funciones['paginas']['actualizar']()
    return jsonify({"ok": False})

@app.route('/api/obtener_enlaces', methods=['GET', 'OPTIONS'])
def api_obtener_enlaces_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        if 'paginas' in api_funciones and 'obtener_enlaces' in api_funciones['paginas']:
            return api_funciones['paginas']['obtener_enlaces']()
        return jsonify({"ok": False, "error": "No disponible", "enlaces": {}})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "enlaces": {}})

@app.route('/api/regenerar_paginas', methods=['POST', 'OPTIONS'])
def api_regenerar_paginas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        regenerar_todas_paginas()
        return jsonify({"ok": True, "mensaje": "Páginas regeneradas"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==================== RUTAS PARA SERVIR MODULOS Y TEMPLATES ====================
@app.route('/')
def index():
    return render_template('modulos/presentacion.html')

@app.route('/madre')
def madre_dashboard():
    return render_template('madre_dashboard.html')

@app.route('/modulos/<path:filename>')
def servir_modulo(filename):
    ruta = os.path.join(BASE_PATH, 'templates', 'modulos', filename)
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    return "Modulo no encontrado", 404

@app.route('/templates/modulos/<path:filename>')
def servir_template_modulo(filename):
    """Sirve archivos desde templates/modulos/ (para tablas_editables.html y otros)"""
    ruta = os.path.join(BASE_PATH, 'templates', 'modulos', filename)
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    return "Archivo no encontrado", 404

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(BASE_PATH, 'static'), filename)

@app.route('/p/<url_id>')
def ver_pagina_hijo(url_id):
    paginas_data = cargar_json(ARCHIVO_PAGINAS, {"paginas": []})
    for p in paginas_data.get("paginas", []):
        if p.get("url_id") == url_id:
            pagina_path = os.path.join(CARPETA_PAGINAS, f"{p.get('id')}.html")
            if os.path.exists(pagina_path):
                with open(pagina_path, 'r', encoding='utf-8') as f:
                    return f.read()
    return "Pagina no encontrada", 404

# ==================== RUTAS API - FACTURACION ====================
@app.route('/api/pedidos_facturacion', methods=['GET', 'OPTIONS'])
def api_pedidos_facturacion_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones and 'pedidos_facturacion' in api_funciones['operaciones']:
        return api_funciones['operaciones']['pedidos_facturacion']()
    if 'facturacion' in api_funciones and 'pedidos_pendientes' in api_funciones['facturacion']:
        return api_funciones['facturacion']['pedidos_pendientes']()
    return jsonify({"ok": False, "error": "No disponible", "pedidos": []})

# ==================== RUTA API - FACTURAR PEDIDOS ====================
@app.route('/api/facturar_pedidos', methods=['POST', 'OPTIONS'])
def api_facturar_pedidos_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'facturacion' in api_funciones and 'facturar' in api_funciones['facturacion']:
        return api_funciones['facturacion']['facturar']()
    return jsonify({"ok": False, "error": "Módulo de facturación no disponible"})

# ==================== RUTA API - GUARDAR CONFIG FACTURA ====================
@app.route('/api/guardar_config_factura', methods=['POST', 'OPTIONS'])
def api_guardar_config_factura_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'facturacion' in api_funciones and 'guardar_config' in api_funciones['facturacion']:
        return api_funciones['facturacion']['guardar_config']()
    return jsonify({"ok": False, "error": "No disponible"})

# ==================== RUTA API - OBTENER CONFIG FACTURA ====================
@app.route('/api/obtener_config_factura', methods=['GET', 'OPTIONS'])
def api_obtener_config_factura_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'facturacion' in api_funciones and 'obtener_config' in api_funciones['facturacion']:
        return api_funciones['facturacion']['obtener_config']()
    return jsonify({"ok": False, "error": "No disponible"})

# ==================== RUTA API - ACTUALIZAR FACTURA ====================
@app.route('/api/actualizar_factura', methods=['POST', 'OPTIONS'])
def api_actualizar_factura_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'facturacion' in api_funciones and 'actualizar_factura' in api_funciones['facturacion']:
        return api_funciones['facturacion']['actualizar_factura']()
    return jsonify({"ok": False, "error": "No disponible"})

# ==================== RUTA API - OBTENER FACTURA POR ID ====================
@app.route('/api/factura/<factura_id>', methods=['GET', 'OPTIONS'])
def api_factura_route(factura_id):
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'facturacion' in api_funciones and 'factura' in api_funciones['facturacion']:
        return api_funciones['facturacion']['factura'](factura_id)
    return jsonify({"ok": False, "error": "No disponible"})

# ==================== RUTA API - LIMPIAR FACTURAS ====================
@app.route('/api/limpiar_facturas', methods=['POST', 'OPTIONS'])
def api_limpiar_facturas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'facturacion' in api_funciones and 'limpiar_facturas' in api_funciones['facturacion']:
        return api_funciones['facturacion']['limpiar_facturas']()
    return jsonify({"ok": False, "error": "No disponible"})

# ==================== RUTA API - ESTADO LIMPIEZA ====================
@app.route('/api/estado_limpieza', methods=['GET', 'OPTIONS'])
def api_estado_limpieza_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'facturacion' in api_funciones and 'estado_limpieza' in api_funciones['facturacion']:
        return api_funciones['facturacion']['estado_limpieza']()
    return jsonify({"ok": False, "error": "No disponible"})

# ==================== RUTA API - ENVIAR FACTURA CORREO ====================
@app.route('/api/enviar_factura_correo', methods=['POST', 'OPTIONS'])
def api_enviar_factura_correo_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'facturacion' in api_funciones and 'enviar_correo' in api_funciones['facturacion']:
        return api_funciones['facturacion']['enviar_correo']()
    return jsonify({"ok": False, "error": "No disponible"})

# ==================== RUTA API - FACTURAS PERMITIDAS PARA CLIENTES ====================
@app.route('/api/facturas_permitidas_cliente', methods=['GET', 'OPTIONS'])
def api_facturas_permitidas_cliente_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'facturacion' in api_funciones and 'facturas_permitidas_cliente' in api_funciones['facturacion']:
        return api_funciones['facturacion']['facturas_permitidas_cliente']()
    return jsonify({"ok": False, "error": "No disponible", "facturas": []})

# ==================== RUTAS API - OPERACIONES PEDIDOS FACTURACION ====================
@app.route('/api/operaciones/pedidos_facturacion', methods=['GET', 'OPTIONS'])
def api_operaciones_pedidos_facturacion():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    
    try:
        pedidos = cargar_json(ARCHIVO_PEDIDOS_FACTURACION, [])
        pedidos_pendientes = [p for p in pedidos if not p.get('facturado', False)]
        pedidos_pendientes.sort(key=lambda x: x.get('fecha', ''), reverse=True)
        
        print(f"[FACTURACION] Pedidos pendientes enviados: {len(pedidos_pendientes)}")
        
        return jsonify({
            "ok": True,
            "pedidos": pedidos_pendientes,
            "total": len(pedidos_pendientes)
        })
    except Exception as e:
        print(f"[ERROR] api_operaciones_pedidos_facturacion: {e}")
        return jsonify({"ok": False, "error": str(e), "pedidos": []})

@app.route('/api/notificar_pedido_facturacion', methods=['POST', 'OPTIONS'])
def api_notificar_pedido_facturacion():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    
    try:
        data = request.get_json() or {}
        pedido_id = data.get('pedido_id')
        
        print(f"[NOTIFICACION] Nuevo pedido para facturación: {pedido_id}")
        
        registrar_bitacora(
            "sistema",
            "Notificación a Facturación",
            f"Nuevo pedido para facturar: {pedido_id}",
            "Facturación"
        )
        
        return jsonify({"ok": True, "mensaje": f"Pedido {pedido_id} notificado"})
    except Exception as e:
        print(f"[ERROR] api_notificar_pedido_facturacion: {e}")
        return jsonify({"ok": False, "error": str(e)})

@app.route('/api/facturas_lista', methods=['GET', 'OPTIONS'])
def api_facturas_lista_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'facturacion' in api_funciones:
        return api_funciones['facturacion']['listar_facturas']()
    return jsonify({"facturas": []})

@app.route('/descargar_factura/<factura_id>', methods=['GET', 'OPTIONS'])
def descargar_factura_route(factura_id):
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'facturacion' in api_funciones:
        return api_funciones['facturacion']['descargar_factura'](factura_id)
    return jsonify({"error": "No disponible"}), 404

# ==================== RUTAS API - OPERACIONES ====================
@app.route('/api/conductores', methods=['GET', 'OPTIONS'])
def api_conductores_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones:
        return api_funciones['operaciones']['conductores']()
    return jsonify({"conductores": []})

@app.route('/api/camiones', methods=['GET', 'OPTIONS'])
def api_camiones_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones:
        return api_funciones['operaciones']['camiones']()
    return jsonify({"camiones": []})

@app.route('/api/resumen_operaciones', methods=['GET', 'OPTIONS'])
def api_resumen_operaciones_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones:
        return api_funciones['operaciones']['resumen']()
    return jsonify({})

@app.route('/api/actualizar_flota_pedido', methods=['POST', 'OPTIONS'])
def api_actualizar_flota_pedido_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones:
        return api_funciones['operaciones']['actualizar_flota']()
    return jsonify({"ok": False})

@app.route('/api/operaciones/enviar_facturacion', methods=['POST', 'OPTIONS'])
def api_operaciones_enviar_facturacion_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones:
        return api_funciones['operaciones']['enviar_facturacion']()
    return jsonify({"ok": False})

@app.route('/api/actualizar_estado_operacion', methods=['POST', 'OPTIONS'])
def api_actualizar_estado_operacion_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones:
        return api_funciones['operaciones']['actualizar_estado']()
    return jsonify({"ok": False})

@app.route('/api/obtener_estados_facturas', methods=['GET', 'OPTIONS'])
def api_obtener_estados_facturas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones:
        return api_funciones['operaciones']['obtener_estados_facturas']()
    return jsonify({"estados": {}})

@app.route('/api/guardar_estado_factura', methods=['POST', 'OPTIONS'])
def api_guardar_estado_factura_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones:
        return api_funciones['operaciones']['guardar_estado_factura']()
    return jsonify({"ok": False})

@app.route('/api/marcar_como_entregado', methods=['POST', 'OPTIONS'])
def api_marcar_como_entregado_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones:
        return api_funciones['operaciones']['marcar_entregado']()
    return jsonify({"ok": False})

@app.route('/api/guardar_observacion', methods=['POST', 'OPTIONS'])
def api_guardar_observacion_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones:
        return api_funciones['operaciones']['guardar_observacion']()
    return jsonify({"ok": False})

@app.route('/api/obtener_observacion', methods=['GET', 'OPTIONS'])
def api_obtener_observacion_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones and 'obtener_observacion' in api_funciones['operaciones']:
        return api_funciones['operaciones']['obtener_observacion']()
    
    factura_id = request.args.get('factura_id')
    if not factura_id:
        return jsonify({"ok": False, "error": "Se requiere factura_id", "observacion": ""})
    
    observaciones = cargar_json(ARCHIVO_OBSERVACIONES, {})
    if factura_id in observaciones:
        return jsonify({"ok": True, "observacion": observaciones[factura_id].get('observacion', '')})
    return jsonify({"ok": True, "observacion": ""})

# ==================== RUTAS API - OPERACIONES (NUEVAS) ====================
@app.route('/api/operaciones/obtener_bonos_viaticos', methods=['GET', 'OPTIONS'])
def api_operaciones_obtener_bonos_viaticos_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones and 'obtener_bonos_viaticos_directo' in api_funciones['operaciones']:
        return api_funciones['operaciones']['obtener_bonos_viaticos_directo']()
    return jsonify({"ok": False, "error": "No disponible", "bono1": "", "bono2": "", "viatico1": 0, "viatico2": 0})

@app.route('/api/operaciones/obtener_datos_cliente', methods=['GET', 'OPTIONS'])
def api_operaciones_obtener_datos_cliente_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones and 'obtener_datos_cliente' in api_funciones['operaciones']:
        return api_funciones['operaciones']['obtener_datos_cliente']()
    return jsonify({"ok": False, "error": "No disponible", "datos": {}})

@app.route('/api/operaciones/obtener_credito', methods=['GET', 'OPTIONS'])
def api_operaciones_obtener_credito_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones and 'obtener_credito' in api_funciones['operaciones']:
        return api_funciones['operaciones']['obtener_credito']()
    return jsonify({"ok": False, "error": "No disponible", "credito": {"credito": 0, "limite_credito": 0, "disponible": 0}})

@app.route('/api/operaciones/crear_pedido_manual', methods=['POST', 'OPTIONS'])
def api_operaciones_crear_pedido_manual_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'operaciones' in api_funciones and 'crear_pedido_manual' in api_funciones['operaciones']:
        return api_funciones['operaciones']['crear_pedido_manual']()
    return jsonify({"ok": False, "error": "No disponible"})

# ==================== RUTAS API - REPORTES ====================
@app.route('/api/estadisticas', methods=['GET', 'OPTIONS'])
def api_estadisticas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'reportes' in api_funciones and 'estadisticas' in api_funciones['reportes']:
        return api_funciones['reportes']['estadisticas']()
    return jsonify({})

@app.route('/api/reportes/estadisticas', methods=['GET', 'OPTIONS'])
def api_reportes_estadisticas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'reportes' in api_funciones and 'estadisticas' in api_funciones['reportes']:
        return api_funciones['reportes']['estadisticas']()
    return jsonify({})

@app.route('/api/reportes/exportar_excel', methods=['GET', 'OPTIONS'])
def api_reportes_exportar_excel_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'reportes' in api_funciones and 'exportar_excel' in api_funciones['reportes']:
        return api_funciones['reportes']['exportar_excel']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/exportar_excel', methods=['GET', 'OPTIONS'])
def api_exportar_excel_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'reportes' in api_funciones and 'exportar_excel' in api_funciones['reportes']:
        return api_funciones['reportes']['exportar_excel']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/reportes/exportar_pdf', methods=['GET', 'OPTIONS'])
def api_reportes_exportar_pdf_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'reportes' in api_funciones and 'exportar_pdf' in api_funciones['reportes']:
        return api_funciones['reportes']['exportar_pdf']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/exportar_pdf', methods=['GET', 'OPTIONS'])
def api_exportar_pdf_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'reportes' in api_funciones and 'exportar_pdf' in api_funciones['reportes']:
        return api_funciones['reportes']['exportar_pdf']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/reportes/descargar', methods=['GET', 'OPTIONS'])
def api_reportes_descargar_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'reportes' in api_funciones and 'descargar' in api_funciones['reportes']:
        return api_funciones['reportes']['descargar']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/reportes/recargar', methods=['GET', 'POST', 'OPTIONS'])
def api_reportes_recargar_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'reportes' in api_funciones and 'recargar' in api_funciones['reportes']:
        return api_funciones['reportes']['recargar']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/reportes/estadisticas_avanzadas', methods=['GET', 'OPTIONS'])
def api_reportes_estadisticas_avanzadas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'reportes' in api_funciones and 'estadisticas_avanzadas' in api_funciones['reportes']:
        return api_funciones['reportes']['estadisticas_avanzadas']()
    return jsonify({"ok": False, "error": "No disponible"})

# ==================== RUTAS API - REPORTES (DATOS TABLA) ====================
@app.route('/api/reportes/guardar_datos', methods=['POST', 'OPTIONS'])
def api_reportes_guardar_datos_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'reportes' in api_funciones and 'guardar_datos' in api_funciones['reportes']:
        return api_funciones['reportes']['guardar_datos']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/reportes/cargar_datos', methods=['GET', 'OPTIONS'])
def api_reportes_cargar_datos_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'reportes' in api_funciones and 'cargar_datos' in api_funciones['reportes']:
        return api_funciones['reportes']['cargar_datos']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/reportes/guardar_celda', methods=['POST', 'OPTIONS'])
def api_reportes_guardar_celda_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'reportes' in api_funciones and 'guardar_celda' in api_funciones['reportes']:
        return api_funciones['reportes']['guardar_celda']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/reportes/guardar_columnas', methods=['POST', 'OPTIONS'])
def api_reportes_guardar_columnas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'reportes' in api_funciones and 'guardar_columnas' in api_funciones['reportes']:
        return api_funciones['reportes']['guardar_columnas']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/reportes/guardar_totales', methods=['POST', 'OPTIONS'])
def api_reportes_guardar_totales_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'reportes' in api_funciones and 'guardar_totales' in api_funciones['reportes']:
        return api_funciones['reportes']['guardar_totales']()
    return jsonify({"ok": False, "error": "No disponible"})

# ==================== RUTAS API - USUARIOS ====================
@app.route('/api/login', methods=['POST', 'OPTIONS'])
def api_login_route():
    if request.method == 'OPTIONS':
        response = jsonify({"ok": True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response
    try:
        data = request.get_json()
        email = data.get('email', '')
        password = data.get('password', '')
        
        usuarios = cargar_json(ARCHIVO_USUARIOS, {"usuarios": []})
        for u in usuarios.get("usuarios", []):
            if u.get('email', '').lower() == email.lower():
                if u.get('password') == hashlib.sha256(password.encode()).hexdigest():
                    u_copy = u.copy()
                    u_copy.pop('password', None)
                    registrar_bitacora(email, "Login", "Inicio de sesion exitoso", "Autenticacion")
                    return jsonify({"ok": True, "usuario": u_copy})
                return jsonify({"ok": False, "error": "Contrasena incorrecta"})
        return jsonify({"ok": False, "error": "Usuario no encontrado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==================== RUTAS API - USUARIOS (GESTIÓN) ====================
@app.route('/api/usuarios', methods=['GET', 'OPTIONS'])
def api_usuarios_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'configuracion' in api_funciones and 'usuarios' in api_funciones['configuracion']:
        return api_funciones['configuracion']['usuarios']()
    return jsonify({"ok": False, "error": "No disponible", "usuarios": []})

@app.route('/api/registrar_usuario', methods=['POST', 'OPTIONS'])
def api_registrar_usuario_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'configuracion' in api_funciones and 'registrar_usuario' in api_funciones['configuracion']:
        return api_funciones['configuracion']['registrar_usuario']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/actualizar_usuario', methods=['POST', 'OPTIONS'])
def api_actualizar_usuario_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'configuracion' in api_funciones and 'actualizar_usuario' in api_funciones['configuracion']:
        return api_funciones['configuracion']['actualizar_usuario']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/eliminar_usuario', methods=['POST', 'OPTIONS'])
def api_eliminar_usuario_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'configuracion' in api_funciones and 'eliminar_usuario' in api_funciones['configuracion']:
        return api_funciones['configuracion']['eliminar_usuario']()
    return jsonify({"ok": False, "error": "No disponible"})

# ==================== RUTAS PARA APPS (PRIMOGÉNITO Y CONDUCTOR) ====================
@app.route('/primogenito')
def primogenito():
    try:
        ruta = os.path.join(CARPETA_PAGINAS, 'primogenito.html')
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                html = f.read()
                url_publica = obtener_url_publica_paginas() or URL_CLOUDFLARE or obtener_url_publica() or "http://127.0.0.1:5000"
                html = html.replace('var API_URL = "";', f'var API_URL = "{url_publica}";')
                return html
        return "Primogenito no encontrado", 404
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/primogenito/<url_id>')
def primogenito_cliente(url_id):
    try:
        paginas = cargar_json(ARCHIVO_PAGINAS, {"paginas": []})
        pagina = None
        for p in paginas.get("paginas", []):
            if p.get("url_id") == url_id and p.get("tipo_enlace") == "primogenito":
                pagina = p
                break
        
        if not pagina:
            for p in paginas.get("paginas", []):
                cliente_info = p.get("cliente_info", {})
                if cliente_info.get("id") == url_id or cliente_info.get("nombre") == url_id:
                    if p.get("tipo_enlace") == "primogenito":
                        pagina = p
                        break
        
        if not pagina:
            return redirect('/primogenito')
        
        cliente_info = pagina.get("cliente_info", {})
        cliente_nombre = cliente_info.get("nombre", "Cliente")
        cliente_id = cliente_info.get("id", "")
        
        ruta_base = os.path.join(CARPETA_PAGINAS, f"{pagina['id']}.html")
        if os.path.exists(ruta_base):
            with open(ruta_base, 'r', encoding='utf-8') as f:
                html = f.read()
                url_publica = obtener_url_publica_paginas() or URL_CLOUDFLARE or obtener_url_publica() or "http://127.0.0.1:5000"
                html = html.replace('var API_URL = "";', f'var API_URL = "{url_publica}";')
                if cliente_id:
                    html = html.replace('id="empresaId"', f'id="empresaId" value="{cliente_id}" readonly style="background:rgba(0,0,0,0.3);color:#60a5fa;font-weight:bold;"')
                    html = html.replace('id="btnConectar"', 'id="btnConectar" style="display:none;"')
                    html = html.replace('</body>', f'<script>document.addEventListener("DOMContentLoaded", function() {{ setTimeout(conectar, 500); }});</script></body>')
                return html
        
        return redirect('/primogenito')
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/conductor')
def conductor():
    try:
        ruta = os.path.join(CARPETA_PAGINAS, 'conductor.html')
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                html = f.read()
                url_publica = obtener_url_publica_paginas() or URL_CLOUDFLARE or obtener_url_publica() or "http://127.0.0.1:5000"
                html = html.replace('var API_URL = "";', f'var API_URL = "{url_publica}";')
                return html
        return "Conductor no encontrado", 404
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/conductor/<url_id>')
def conductor_cliente(url_id):
    try:
        paginas = cargar_json(ARCHIVO_PAGINAS, {"paginas": []})
        pagina = None
        for p in paginas.get("paginas", []):
            if p.get("url_id") == url_id and p.get("tipo_enlace") == "conductor":
                pagina = p
                break
        
        if not pagina:
            for p in paginas.get("paginas", []):
                cliente_info = p.get("cliente_info", {})
                if cliente_info.get("id") == url_id or cliente_info.get("nombre") == url_id:
                    if p.get("tipo_enlace") == "conductor":
                        pagina = p
                        break
        
        if not pagina:
            return redirect('/conductor')
        
        cliente_info = pagina.get("cliente_info", {})
        cliente_id = cliente_info.get("id", "")
        
        ruta_base = os.path.join(CARPETA_PAGINAS, f"{pagina['id']}.html")
        if os.path.exists(ruta_base):
            with open(ruta_base, 'r', encoding='utf-8') as f:
                html = f.read()
                url_publica = obtener_url_publica_paginas() or URL_CLOUDFLARE or obtener_url_publica() or "http://127.0.0.1:5000"
                html = html.replace('var API_URL = "";', f'var API_URL = "{url_publica}";')
                if cliente_id:
                    html = html.replace('id="conductorId"', f'id="conductorId" value="{cliente_id}"')
                return html
        
        return redirect('/conductor')
    except Exception as e:
        return f"Error: {e}", 500

# ==================== RUTAS API - TOM ====================
@app.route('/api/tom/dashboard', methods=['GET', 'OPTIONS'])
def api_tom_dashboard_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'dashboard' in api_funciones['tom']:
        return api_funciones['tom']['dashboard']()
    return jsonify({"error": "TOM no disponible"})

@app.route('/api/tom/empresas', methods=['GET', 'OPTIONS'])
def api_tom_empresas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'empresas' in api_funciones['tom']:
        return api_funciones['tom']['empresas']()
    return jsonify({"ok": False, "empresas": []})

@app.route('/api/tom/empresa/<empresa_id>', methods=['GET', 'OPTIONS'])
def api_tom_empresa_route(empresa_id):
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'empresa' in api_funciones['tom']:
        return api_funciones['tom']['empresa'](empresa_id)
    return jsonify({"ok": False, "error": "TOM no disponible"})

@app.route('/api/tom/pedidos', methods=['GET', 'OPTIONS'])
def api_tom_pedidos_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'pedidos' in api_funciones['tom']:
        return api_funciones['tom']['pedidos']()
    return jsonify({"ok": False, "pedidos": []})

@app.route('/api/tom/facturas', methods=['GET', 'OPTIONS'])
def api_tom_facturas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'facturas' in api_funciones['tom']:
        return api_funciones['tom']['facturas']()
    return jsonify({"ok": False, "facturas": []})

@app.route('/api/tom/estadisticas', methods=['GET', 'OPTIONS'])
def api_tom_estadisticas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'estadisticas' in api_funciones['tom']:
        return api_funciones['tom']['estadisticas']()
    return jsonify({"ok": False, "error": "TOM no disponible"})

@app.route('/api/tom/resumen', methods=['GET', 'OPTIONS'])
def api_tom_resumen_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'resumen' in api_funciones['tom']:
        return api_funciones['tom']['resumen']()
    return jsonify({"ok": False, "error": "TOM no disponible"})

@app.route('/api/tom/hablar', methods=['POST', 'OPTIONS'])
def api_tom_hablar_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'hablar' in api_funciones['tom']:
        return api_funciones['tom']['hablar']()
    return jsonify({"ok": False, "error": "TOM no disponible"})

@app.route('/api/tom/preguntar', methods=['POST', 'OPTIONS'])
def api_tom_preguntar_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'preguntar' in api_funciones['tom']:
        return api_funciones['tom']['preguntar']()
    return jsonify({"ok": False, "error": "TOM no disponible"})

@app.route('/api/tom/buscar', methods=['GET', 'OPTIONS'])
def api_tom_buscar_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'buscar' in api_funciones['tom']:
        return api_funciones['tom']['buscar']()
    return jsonify({"ok": False, "resultados": []})

@app.route('/api/tom/costos', methods=['GET', 'OPTIONS'])
def api_tom_costos_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'costos' in api_funciones['tom']:
        return api_funciones['tom']['costos']()
    return jsonify({"ok": False, "costos": []})

@app.route('/api/tom/conductores', methods=['GET', 'OPTIONS'])
def api_tom_conductores_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'conductores' in api_funciones['tom']:
        return api_funciones['tom']['conductores']()
    return jsonify({"ok": False, "conductores": []})

@app.route('/api/tom/camiones', methods=['GET', 'OPTIONS'])
def api_tom_camiones_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'camiones' in api_funciones['tom']:
        return api_funciones['tom']['camiones']()
    return jsonify({"ok": False, "camiones": []})

@app.route('/api/tom/usuarios', methods=['GET', 'OPTIONS'])
def api_tom_usuarios_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'usuarios' in api_funciones['tom']:
        return api_funciones['tom']['usuarios']()
    return jsonify({"ok": False, "usuarios": []})

@app.route('/api/tom/sistema/archivos', methods=['GET', 'OPTIONS'])
def api_tom_sistema_archivos_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'sistema_archivos' in api_funciones['tom']:
        return api_funciones['tom']['sistema_archivos']()
    return jsonify({"ok": False, "archivos": []})

@app.route('/api/tom/sistema/leer', methods=['GET', 'OPTIONS'])
def api_tom_sistema_leer_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'sistema_leer' in api_funciones['tom']:
        return api_funciones['tom']['sistema_leer']()
    return jsonify({"ok": False, "error": "TOM no disponible"})

@app.route('/api/tom/sistema/buscar', methods=['GET', 'OPTIONS'])
def api_tom_sistema_buscar_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'sistema_buscar' in api_funciones['tom']:
        return api_funciones['tom']['sistema_buscar']()
    return jsonify({"ok": False, "resultados": []})

@app.route('/api/tom/sistema/estructura', methods=['GET', 'OPTIONS'])
def api_tom_sistema_estructura_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'sistema_estructura' in api_funciones['tom']:
        return api_funciones['tom']['sistema_estructura']()
    return jsonify({"ok": False, "error": "TOM no disponible"})

@app.route('/api/tom/soporte', methods=['GET', 'OPTIONS'])
def api_tom_soporte_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tom' in api_funciones and 'soporte' in api_funciones['tom']:
        return api_funciones['tom']['soporte']()
    return jsonify({"ok": False, "error": "TOM no disponible"})

# ==================== RUTAS API - EDITOR VISUAL ====================
@app.route('/api/editor/paginas', methods=['GET', 'OPTIONS'])
def api_editor_paginas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'editor_visual' in api_funciones and 'listar_paginas' in api_funciones['editor_visual']:
        return api_funciones['editor_visual']['listar_paginas']()
    return jsonify({"ok": False, "error": "Editor Visual no disponible", "paginas": []})

@app.route('/api/editor/pagina/<pagina_id>', methods=['GET', 'OPTIONS'])
def api_editor_pagina_route(pagina_id):
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'editor_visual' in api_funciones and 'obtener_pagina' in api_funciones['editor_visual']:
        return api_funciones['editor_visual']['obtener_pagina'](pagina_id)
    return jsonify({"ok": False, "error": "Editor Visual no disponible"})

@app.route('/api/editor/guardar', methods=['POST', 'OPTIONS'])
def api_editor_guardar_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'editor_visual' in api_funciones and 'guardar_pagina' in api_funciones['editor_visual']:
        return api_funciones['editor_visual']['guardar_pagina']()
    return jsonify({"ok": False, "error": "Editor Visual no disponible"})

@app.route('/api/editor/previsualizar', methods=['POST', 'OPTIONS'])
def api_editor_previsualizar_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'editor_visual' in api_funciones and 'previsualizar' in api_funciones['editor_visual']:
        return api_funciones['editor_visual']['previsualizar']()
    return jsonify({"ok": False, "error": "Editor Visual no disponible"})

# ==================== RUTAS API - FLOTA ====================
@app.route('/api/flota/conductores', methods=['GET', 'OPTIONS'])
def api_flota_conductores_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'flota' in api_funciones:
        return api_funciones['flota']['conductores']()
    return jsonify({"conductores": []})

@app.route('/api/flota/crear_conductor', methods=['POST', 'OPTIONS'])
def api_flota_crear_conductor_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'flota' in api_funciones:
        return api_funciones['flota']['crear_conductor']()
    return jsonify({"ok": False})

@app.route('/api/flota/actualizar_conductor', methods=['POST', 'OPTIONS'])
def api_flota_actualizar_conductor_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'flota' in api_funciones:
        return api_funciones['flota']['actualizar_conductor']()
    return jsonify({"ok": False})

@app.route('/api/flota/eliminar_conductor', methods=['POST', 'OPTIONS'])
def api_flota_eliminar_conductor_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'flota' in api_funciones:
        return api_funciones['flota']['eliminar_conductor']()
    return jsonify({"ok": False})

@app.route('/api/flota/camiones', methods=['GET', 'OPTIONS'])
def api_flota_camiones_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'flota' in api_funciones:
        return api_funciones['flota']['camiones']()
    return jsonify({"camiones": []})

@app.route('/api/flota/crear_camion', methods=['POST', 'OPTIONS'])
def api_flota_crear_camion_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'flota' in api_funciones:
        return api_funciones['flota']['crear_camion']()
    return jsonify({"ok": False})

@app.route('/api/flota/actualizar_camion', methods=['POST', 'OPTIONS'])
def api_flota_actualizar_camion_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'flota' in api_funciones:
        return api_funciones['flota']['actualizar_camion']()
    return jsonify({"ok": False})

@app.route('/api/flota/eliminar_camion', methods=['POST', 'OPTIONS'])
def api_flota_eliminar_camion_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'flota' in api_funciones:
        return api_funciones['flota']['eliminar_camion']()
    return jsonify({"ok": False})

@app.route('/api/flota/mantenimiento', methods=['GET', 'OPTIONS'])
def api_flota_mantenimiento_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'flota' in api_funciones:
        return api_funciones['flota']['mantenimiento']()
    return jsonify({"registros": []})

@app.route('/api/flota/crear_mantenimiento', methods=['POST', 'OPTIONS'])
def api_flota_crear_mantenimiento_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'flota' in api_funciones:
        return api_funciones['flota']['crear_mantenimiento']()
    return jsonify({"ok": False})

# ==================== RUTAS API - TABLAS EDITABLES ====================
@app.route('/api/obtener_bitacora', methods=['GET', 'OPTIONS'])
def api_obtener_bitacora_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tablas_editables' in api_funciones and 'obtener_bitacora' in api_funciones['tablas_editables']:
        return api_funciones['tablas_editables']['obtener_bitacora']()
    return jsonify({"ok": False, "error": "No disponible", "datos": {}})

@app.route('/api/sincronizar_bitacora', methods=['POST', 'OPTIONS'])
def api_sincronizar_bitacora_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tablas_editables' in api_funciones and 'sincronizar_bitacora' in api_funciones['tablas_editables']:
        return api_funciones['tablas_editables']['sincronizar_bitacora']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/limpiar_por_fechas', methods=['POST', 'OPTIONS'])
def api_limpiar_por_fechas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'tablas_editables' in api_funciones and 'limpiar_por_fechas' in api_funciones['tablas_editables']:
        return api_funciones['tablas_editables']['limpiar_por_fechas']()
    return jsonify({"ok": False, "error": "No disponible"})

# ==================== RUTAS API - TABLAS EDITABLES (EXPORTAR) ====================
@app.route('/api/tablas_editables/exportar_excel', methods=['GET', 'OPTIONS'])
def api_tablas_editables_exportar_excel():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        from tablas_editables import api_exportar_excel
        return api_exportar_excel()
    except ImportError as e:
        print(f"[ERROR] Importando api_exportar_excel: {e}")
        return jsonify({"ok": False, "error": "Función no disponible"}), 404
    except Exception as e:
        print(f"[ERROR] api_tablas_editables_exportar_excel: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/tablas_editables/exportar_pdf', methods=['GET', 'OPTIONS'])
def api_tablas_editables_exportar_pdf():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        from tablas_editables import api_exportar_pdf
        return api_exportar_pdf()
    except ImportError as e:
        print(f"[ERROR] Importando api_exportar_pdf: {e}")
        return jsonify({"ok": False, "error": "Función no disponible"}), 404
    except Exception as e:
        print(f"[ERROR] api_tablas_editables_exportar_pdf: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

# ==================== RUTAS API - UBICACION GPS ====================
@app.route('/api/ubicaciones', methods=['GET', 'OPTIONS'])
def api_ubicaciones_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'ubicacion' in api_funciones:
        return api_funciones['ubicacion']['listar']()
    return jsonify({"ok": False, "error": "No disponible", "vehiculos": []})

@app.route('/api/actualizar_ubicacion', methods=['POST', 'OPTIONS'])
def api_actualizar_ubicacion_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'ubicacion' in api_funciones:
        return api_funciones['ubicacion']['actualizar']()
    return jsonify({"ok": False})

@app.route('/api/actualizar_estado_vehiculo', methods=['POST', 'OPTIONS'])
def api_actualizar_estado_vehiculo_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'ubicacion' in api_funciones:
        return api_funciones['ubicacion']['actualizar_estado']()
    return jsonify({"ok": False})

@app.route('/api/vehiculo/<vehiculo_id>', methods=['GET', 'OPTIONS'])
def api_vehiculo_route(vehiculo_id):
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'ubicacion' in api_funciones:
        return api_funciones['ubicacion']['obtener'](vehiculo_id)
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/sincronizar_flota', methods=['POST', 'OPTIONS'])
def api_sincronizar_flota_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'ubicacion' in api_funciones:
        return api_funciones['ubicacion']['sincronizar']()
    return jsonify({"ok": False})

@app.route('/api/ciudades_nicaragua', methods=['GET', 'OPTIONS'])
def api_ciudades_nicaragua_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'ubicacion' in api_funciones:
        return api_funciones['ubicacion']['ciudades']()
    return jsonify({"ok": False, "ciudades": []})

@app.route('/api/vehiculos_cercanos', methods=['GET', 'OPTIONS'])
def api_vehiculos_cercanos_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'ubicacion' in api_funciones:
        return api_funciones['ubicacion']['cercanos']()
    return jsonify({"ok": False, "vehiculos": []})

# ==================== RUTAS API - CONDUCTORES CHAT (UBICACION) ====================
@app.route('/api/ubicacion/conductores_chat', methods=['GET', 'OPTIONS'])
def api_ubicacion_conductores_chat_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'ubicacion' in api_funciones and 'conductores_chat' in api_funciones['ubicacion']:
        return api_funciones['ubicacion']['conductores_chat']()
    return jsonify({"ok": False, "error": "No disponible", "conductores": []})

@app.route('/api/ubicacion/mensajes_conductor', methods=['GET', 'OPTIONS'])
def api_ubicacion_mensajes_conductor_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'ubicacion' in api_funciones and 'mensajes_conductor' in api_funciones['ubicacion']:
        return api_funciones['ubicacion']['mensajes_conductor']()
    return jsonify({"ok": False, "error": "No disponible", "mensajes": []})

@app.route('/api/ubicacion/limpiar_mensajes_conductor', methods=['POST', 'OPTIONS'])
def api_ubicacion_limpiar_mensajes_conductor_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'ubicacion' in api_funciones and 'limpiar_mensajes_conductor' in api_funciones['ubicacion']:
        return api_funciones['ubicacion']['limpiar_mensajes_conductor']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/ubicacion/limpiar_todos_mensajes', methods=['POST', 'OPTIONS'])
def api_ubicacion_limpiar_todos_mensajes_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'ubicacion' in api_funciones and 'limpiar_todos_mensajes' in api_funciones['ubicacion']:
        return api_funciones['ubicacion']['limpiar_todos_mensajes']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/ubicacion/eliminar_mensaje', methods=['POST', 'OPTIONS'])
def api_ubicacion_eliminar_mensaje_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'ubicacion' in api_funciones and 'eliminar_mensaje' in api_funciones['ubicacion']:
        return api_funciones['ubicacion']['eliminar_mensaje']()
    return jsonify({"ok": False, "error": "No disponible"})

@app.route('/api/ubicacion/descargar_archivo', methods=['GET', 'OPTIONS'])
def api_ubicacion_descargar_archivo():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    if 'ubicacion' in api_funciones and 'descargar_archivo' in api_funciones['ubicacion']:
        return api_funciones['ubicacion']['descargar_archivo']()
    return jsonify({"ok": False, "error": "No disponible"})

# ==================== RUTAS API - EMPRESAS ACTIVAS ====================
@app.route('/api/empresas_activas', methods=['GET', 'OPTIONS'])
def api_empresas_activas_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        clientes_data = cargar_json(ARCHIVO_CLIENTES, {"clientes": []})
        clientes = clientes_data.get("clientes", [])
        activos = []
        for c in clientes:
            if c.get("activo", True):
                activos.append({
                    "id": c.get("id"),
                    "nombre": c.get("nombre"),
                    "contacto": c.get("contacto", ""),
                    "telefono": c.get("telefono", ""),
                    "email": c.get("email", ""),
                    "credito": c.get("credito", 0),
                    "limite_credito": c.get("limite_credito", 0)
                })
        return jsonify({"empresas": activos})
    except Exception as e:
        print(f"[ERROR] api_empresas_activas: {e}")
        return jsonify({"empresas": []})

# ==================== RUTAS API - GENERAR ENLACE PRIMOGÉNITO ====================
@app.route('/api/primogenito/generar_enlace', methods=['POST', 'OPTIONS'])
def api_generar_enlace_primogenito():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        data = request.get_json()
        cliente_id = data.get('cliente_id')
        
        if not cliente_id:
            return jsonify({"ok": False, "error": "Se requiere cliente_id"})
        
        clientes_data = cargar_json(ARCHIVO_CLIENTES, {"clientes": []})
        cliente_encontrado = None
        for c in clientes_data.get("clientes", []):
            if c.get("id") == cliente_id:
                cliente_encontrado = c
                break
        
        if not cliente_encontrado:
            empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
            for e in empresas_data.get("empresas", []):
                if e.get("id") == cliente_id:
                    cliente_encontrado = e
                    break
        
        if not cliente_encontrado:
            return jsonify({"ok": False, "error": "Cliente no encontrado"})
        
        nombre_cliente = cliente_encontrado.get("nombre", "Cliente")
        
        url_id_base = re.sub(r'[^a-z0-9-]', '', f"pri-{nombre_cliente.lower().replace(' ', '-')}")
        if not url_id_base:
            url_id_base = f"pri-{cliente_id.lower()}"
        
        url_id = url_id_base
        counter = 1
        paginas = cargar_json(ARCHIVO_PAGINAS, {"paginas": []})
        while any(p.get("url_id") == url_id for p in paginas.get("paginas", [])):
            url_id = f"{url_id_base}-{counter}"
            counter += 1
        
        url_publica = obtener_url_publica_paginas() or URL_CLOUDFLARE or obtener_url_publica() or "http://127.0.0.1:5000"
        
        from paginas_hijo import crear_pagina
        
        estilos = {
            "color_primario": "#3b82f6",
            "color_secundario": "#2563eb", 
            "color_fondo": "#0f0f1a",
            "titulo": f"📱 {nombre_cliente}",
            "subtitulo": "App de Pedidos Móvil - Grupo GSN",
            "logo": "fa-mobile-alt"
        }
        
        nueva_pagina = crear_pagina(f"PRIMOGENITO: {nombre_cliente}", estilos)
        
        paginas = cargar_json(ARCHIVO_PAGINAS, {"paginas": []})
        for i, p in enumerate(paginas.get("paginas", [])):
            if p.get("id") == nueva_pagina["id"]:
                paginas["paginas"][i]["cliente_info"] = {
                    "id": cliente_id,
                    "nombre": nombre_cliente,
                    "tipo": "primogenito"
                }
                paginas["paginas"][i]["tipo_enlace"] = "primogenito"
                paginas["paginas"][i]["ruta"] = f"/primogenito/{url_id}"
                break
        guardar_json(ARCHIVO_PAGINAS, paginas)
        
        url_completa = f"{url_publica}/primogenito/{url_id}"
        
        return jsonify({
            "ok": True,
            "url": url_completa,
            "url_id": url_id,
            "pagina_id": nueva_pagina["id"],
            "cliente": {
                "id": cliente_id,
                "nombre": nombre_cliente
            },
            "mensaje": f"Enlace primogénito generado para {nombre_cliente}"
        })
    except Exception as e:
        print(f"[ERROR] api_generar_enlace_primogenito: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})

# ==================== RUTAS API - TEMAS POR USUARIO ====================
@app.route('/api/obtener_tema_usuario', methods=['GET', 'OPTIONS'])
def api_obtener_tema_usuario_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        usuario_data = request.headers.get('X-User-Data')
        usuario_id = None
        email = None
        if usuario_data:
            try:
                usuario = json.loads(usuario_data)
                usuario_id = usuario.get('id')
                email = usuario.get('email')
            except:
                pass
        
        tema_data = obtener_tema_usuario(usuario_id, email)
        return jsonify({
            "ok": True,
            "tema": tema_data.get("tema", "default"),
            "imagen_url": tema_data.get("imagen_url"),
            "color_primario": tema_data.get("color_primario", "#f59e0b"),
            "color_secundario": tema_data.get("color_secundario", "#d97706"),
            "colores": tema_data.get("colores", {}),
            "logo": tema_data.get("logo", {}),
            "fecha_actualizacion": tema_data.get("fecha_actualizacion")
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route('/api/guardar_tema_usuario', methods=['POST', 'OPTIONS'])
def api_guardar_tema_usuario_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        data = request.get_json()
        tema = data.get('tema', 'default')
        imagen_url = data.get('imagen_url')
        
        usuario_data = request.headers.get('X-User-Data')
        usuario_id = None
        email = None
        if usuario_data:
            try:
                usuario = json.loads(usuario_data)
                usuario_id = usuario.get('id')
                email = usuario.get('email')
            except:
                pass
        
        resultado = guardar_tema_usuario(usuario_id, tema, imagen_url, email)
        if resultado:
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Error al guardar"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route('/api/temas_disponibles', methods=['GET', 'OPTIONS'])
def api_temas_disponibles_route():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        temas_lista = []
        for key, value in TEMAS_DISPONIBLES.items():
            temas_lista.append({
                "id": key,
                "nombre": value["nombre"],
                "descripcion": value["descripcion"],
                "color_primario": value["color_primario"],
                "color_secundario": value["color_secundario"]
            })
        return jsonify({"ok": True, "temas": temas_lista})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==================== RUTAS DEBUG ====================
@app.route('/api/debug/modulos', methods=['GET', 'OPTIONS'])
def debug_modulos():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    return jsonify({
        "modulos_cargados": list(api_funciones.keys()),
        "sistema": {"plataforma": sys.platform, "es_windows": IS_WINDOWS}
    })

@app.route('/api/debug/pedidos_facturacion_directo', methods=['GET', 'OPTIONS'])
def debug_pedidos_facturacion_directo():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        pedidos = cargar_json(ARCHIVO_PEDIDOS_FACTURACION, [])
        return jsonify({
            "ok": True,
            "cantidad": len(pedidos),
            "pedidos": pedidos,
            "ruta": ARCHIVO_PEDIDOS_FACTURACION
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==================== RUTAS PARA SERVIDOR DE IMÁGENES ====================
@app.route('/templates/modulos/Imagenes/<path:filename>')
def servir_imagen_template(filename):
    ruta_imagen = os.path.join(BASE_PATH, 'templates', 'modulos', 'Imagenes', filename)
    if os.path.exists(ruta_imagen):
        return send_from_directory(os.path.join(BASE_PATH, 'templates', 'modulos', 'Imagenes'), filename)
    return jsonify({"error": "Imagen no encontrada"}), 404

@app.route('/modulos/Imagenes/<path:filename>')
def servir_imagen_modulos(filename):
    ruta_imagen = os.path.join(BASE_PATH, 'templates', 'modulos', 'Imagenes', filename)
    if os.path.exists(ruta_imagen):
        return send_from_directory(os.path.join(BASE_PATH, 'templates', 'modulos', 'Imagenes'), filename)
    return jsonify({"error": "Imagen no encontrada"}), 404

@app.route('/static/Imagenes/<path:filename>')
def servir_imagen_static(filename):
    ruta_imagen = os.path.join(BASE_PATH, 'static', 'Imagenes', filename)
    if os.path.exists(ruta_imagen):
        return send_from_directory(os.path.join(BASE_PATH, 'static', 'Imagenes'), filename)
    return jsonify({"error": "Imagen no encontrada"}), 404

# ==================== INICIO DEL SISTEMA ====================
def iniciar_servidor():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)

def main():
    if IS_WINDOWS:
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
    
    print("\n" + "="*60)
    print("   GRUPO GSN - SISTEMA DE GESTION DE COMBUSTIBLE")
    print(f"   Plataforma: {sys.platform}")
    print("="*60 + "\n")
    
    inicializar_datos_demo()
    
    url_publica = None
    url_con_id = None
    id_fijo = None
    
    if SERVIDOR_PUBLICO_DISPONIBLE:
        try:
            info = iniciar_servidor_publico()
            id_fijo = info.get("id")
            url_publica = obtener_url_publica()
            url_con_id = obtener_url_con_id()
            
            if url_publica:
                print(f"\n[OK] URL PUBLICA: {url_publica}")
                print(f"[OK] URL CON ID: {url_con_id}")
                set_public_url(url_publica)
                try:
                    set_public_url_paginas(url_publica)
                    print(f"[OK] URL pública registrada en páginas hijo")
                except Exception as e:
                    print(f"[WARN] Error en set_public_url_paginas: {e}")
            else:
                print("\n[WARN] No se pudo obtener IP pública")
        except Exception as e:
            print(f"\n[ERROR] Iniciando Servidor Público: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n[WARN] Servidor Público no disponible")
    
    print("\n[INFO] Iniciando Cloudflared...")
    iniciar_cloudflared()
    
    if URL_CLOUDFLARE:
        set_public_url_paginas(URL_CLOUDFLARE)
    
    hilo = threading.Thread(target=iniciar_servidor, daemon=True)
    hilo.start()
    time.sleep(3)
    
    print("\n[INFO] ACCESO LOCAL:")
    print("   http://127.0.0.1:5000")
    
    if id_fijo:
        print(f"\n📌 TU ID FIJO: {id_fijo}")
        if url_publica:
            print(f"🌐 URL PUBLICA: {url_publica}")
            print(f"🔗 URL CON ID: {url_con_id}")
    
    if URL_CLOUDFLARE:
        print(f"\n🌐 TUNEL CLOUDFLARE: {URL_CLOUDFLARE}")
        set_public_url_paginas(URL_CLOUDFLARE)
    
    print("\n[INFO] CREDENCIALES:")
    print("   Admin: admin@gruposn.com / admin123")
    print("="*60 + "\n")
    
    try:
        gui = 'edgechromium' if IS_WINDOWS else ('webkit' if IS_LINUX else 'cef')
        webview.create_window(
            "Grupo GSN - Sistema de Gestión de Combustible",
            "http://127.0.0.1:5000/",
            width=1400, height=900, resizable=True,
            min_size=(1024, 768), confirm_close=True
        )
        webview.start(gui=gui, debug=False)
    except Exception as e:
        print(f"Error con {gui}: {e}")
        webview.create_window(
            "Grupo GSN - Sistema de Gestión de Combustible",
            "http://127.0.0.1:5000/",
            width=1400, height=900, resizable=True
        )
        webview.start(debug=False)

if __name__ == '__main__':
    main()