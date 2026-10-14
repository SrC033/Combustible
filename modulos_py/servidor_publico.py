#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servidor Público - Grupo GSN
Cliente Socket.io para túnel con Render
"""

import os
import sys
import json
import socket
import random
import hashlib
import uuid
import requests
import threading
import time
from datetime import datetime
from pathlib import Path

# ==================== CONFIGURACIÓN ====================
def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.abspath(".")

def get_data_path():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, 'data')
    return os.path.abspath(".")

BASE_PATH = get_base_path()
DATA_PATH = get_data_path()
CARPETA_DATOS = os.path.join(DATA_PATH, "datos")
ARCHIVO_DISPOSITIVOS = os.path.join(CARPETA_DATOS, "dispositivos.json")
ARCHIVO_URL_PUBLICA = os.path.join(CARPETA_DATOS, "url_publica.json")

Path(CARPETA_DATOS).mkdir(parents=True, exist_ok=True)

# ==================== URL DE RENDER ====================
URL_RENDER = "https://madre-gsn-combustible-datos.onrender.com"
URL_LOCAL = "http://localhost:5000"

# ==================== ID FIJO ====================
ID_FIJO = None

def generar_id_fijo():
    global ID_FIJO
    if os.path.exists(ARCHIVO_DISPOSITIVOS):
        try:
            with open(ARCHIVO_DISPOSITIVOS, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('id_fijo'):
                    ID_FIJO = data['id_fijo']
                    return ID_FIJO
        except Exception as e:
            print(f"[WARN] Error cargando ID: {e}")
    
    try:
        mac = uuid.getnode()
        hostname = socket.gethostname()
        base = f"{mac}-{hostname}-{datetime.now().isoformat()}"
        id_hash = hashlib.md5(base.encode()).hexdigest()[:8].upper()
        ID_FIJO = f"GSN-{id_hash}"
        
        with open(ARCHIVO_DISPOSITIVOS, 'w', encoding='utf-8') as f:
            json.dump({
                "id_fijo": ID_FIJO,
                "fecha_creacion": datetime.now().isoformat(),
                "hostname": hostname,
                "mac": str(mac),
                "entorno": "render"
            }, f, indent=2, ensure_ascii=False)
        
        return ID_FIJO
    except Exception as e:
        print(f"[ERROR] Generando ID: {e}")
        ID_FIJO = f"GSN-{random.randint(10000, 99999)}"
        return ID_FIJO

# ==================== OBTENER IP ====================
def obtener_ip_publica():
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        if response.status_code == 200:
            return response.json().get('ip')
    except:
        pass
    return None

def obtener_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "127.0.0.1"

# ==================== URLS ====================
def obtener_url_publica():
    """Retorna la URL de Render (siempre la misma)"""
    return URL_RENDER

def obtener_url_con_id():
    """Retorna la URL de Render con el ID fijo"""
    if ID_FIJO:
        return f"{URL_RENDER}/?id={ID_FIJO}"
    return URL_RENDER

def guardar_url_publica(url):
    """Guarda la URL pública (solo para compatibilidad)"""
    try:
        with open(ARCHIVO_URL_PUBLICA, 'w', encoding='utf-8') as f:
            json.dump({
                "url": url,
                "fecha_actualizacion": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Guardando URL: {e}")
        return False

# ==================== CLIENTE SOCKET.IO ====================
_cliente_socket = None
_tunel_activo = False
_hilo_socket = None

def iniciar_cliente_socket():
    """Inicia el cliente Socket.io para conectar con Render"""
    global _cliente_socket, _tunel_activo, _hilo_socket
    
    try:
        import socketio
        
        # Crear cliente Socket.io
        sio = socketio.Client()
        _cliente_socket = sio
        
        @sio.event
        def connect():
            global _tunel_activo
            print(f"[SOCKET] ✅ Conectado a Render")
            print(f"[SOCKET] 📡 Registrando ID: {ID_FIJO}")
            
            # Registrar el dispositivo
            sio.emit('registro', {
                'id_fijo': ID_FIJO,
                'nombre': socket.gethostname(),
                'ip_local': obtener_ip_local(),
                'version': '2.0.0'
            })
        
        @sio.event
        def connect_error(data):
            print(f"[SOCKET] ❌ Error de conexión: {data}")
        
        @sio.event
        def disconnect():
            global _tunel_activo
            _tunel_activo = False
            print(f"[SOCKET] 🔌 Desconectado de Render")
        
        @sio.event
        def registro_confirmado(data):
            global _tunel_activo
            _tunel_activo = True
            print(f"[SOCKET] ✅ Túnel establecido correctamente")
            print(f"[SOCKET]    ID: {data.get('id_fijo')}")
            print(f"[SOCKET]    URL: {data.get('url_publica')}")
        
        @sio.event
        def registro_error(data):
            print(f"[SOCKET] ❌ Error de registro: {data.get('error')}")
            print(f"[SOCKET]    Esperado: {data.get('esperado')}")
            print(f"[SOCKET]    Recibido: {data.get('recibido')}")
        
        @sio.event
        def heartbeat_confirmado(data):
            print(f"[SOCKET] 💓 Heartbeat confirmado: {data.get('timestamp')}")
        
        @sio.event
        def tunel_estado(data):
            print(f"[SOCKET] 📊 Estado del túnel:")
            print(f"    Activo: {data.get('activo')}")
            print(f"    ID: {data.get('id_fijo')}")
            print(f"    Clientes: {data.get('clientes')}")
        
        # Conectar a Render
        print(f"[SOCKET] 🔌 Conectando a {URL_RENDER}...")
        sio.connect(URL_RENDER, wait_timeout=10)
        
        # Iniciar hilo para enviar heartbeat
        def enviar_heartbeat():
            while True:
                try:
                    if sio.connected:
                        sio.emit('heartbeat', {'timestamp': datetime.now().isoformat()})
                except Exception as e:
                    print(f"[SOCKET] Error enviando heartbeat: {e}")
                time.sleep(30)
        
        _hilo_socket = threading.Thread(target=enviar_heartbeat, daemon=True)
        _hilo_socket.start()
        
        return True
        
    except ImportError:
        print("[ERROR] Socket.io no instalado. Ejecuta: pip install python-socketio[client]")
        return False
    except Exception as e:
        print(f"[ERROR] Error en cliente Socket.io: {e}")
        return False

def obtener_tunel_activo():
    """Retorna si el túnel está activo"""
    return _tunel_activo

def obtener_cliente_socket():
    """Retorna el cliente Socket.io para uso interno"""
    return _cliente_socket

# ==================== DISPOSITIVOS ====================
def cargar_dispositivos():
    if os.path.exists(ARCHIVO_DISPOSITIVOS):
        try:
            with open(ARCHIVO_DISPOSITIVOS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Error cargando dispositivos: {e}")
    return {"id_fijo": ID_FIJO, "dispositivos": []}

def guardar_dispositivos(data):
    try:
        Path(CARPETA_DATOS).mkdir(parents=True, exist_ok=True)
        with open(ARCHIVO_DISPOSITIVOS, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Guardando dispositivos: {e}")
        return False

def registrar_dispositivo(nombre, ip_publica, ip_local):
    data = cargar_dispositivos()
    for d in data.get("dispositivos", []):
        if d.get("nombre") == nombre:
            d["ip_publica"] = ip_publica
            d["ip_local"] = ip_local
            d["ultima_actualizacion"] = datetime.now().isoformat()
            d["activo"] = True
            d["url"] = obtener_url_publica()
            guardar_dispositivos(data)
            return d
    
    nuevo = {
        "id": f"DEV-{random.randint(1000, 9999)}",
        "nombre": nombre,
        "ip_publica": ip_publica,
        "ip_local": ip_local,
        "url": obtener_url_publica(),
        "fecha_registro": datetime.now().isoformat(),
        "ultima_actualizacion": datetime.now().isoformat(),
        "activo": True
    }
    
    if "dispositivos" not in data:
        data["dispositivos"] = []
    data["dispositivos"].append(nuevo)
    guardar_dispositivos(data)
    return nuevo

def validar_dispositivo(id_buscar):
    data = cargar_dispositivos()
    for d in data.get("dispositivos", []):
        if d.get("id") == id_buscar or d.get("nombre") == id_buscar:
            if d.get("activo", True):
                return d
    return None

def obtener_info_servidor():
    global ID_FIJO
    ip_publica = obtener_ip_publica()
    ip_local = obtener_ip_local()
    nombre = socket.gethostname()
    
    registrar_dispositivo(nombre, ip_publica, ip_local)
    
    return {
        "id": ID_FIJO,
        "nombre": nombre,
        "ip_publica": ip_publica,
        "ip_local": ip_local,
        "ultima_actualizacion": datetime.now().isoformat(),
        "url": obtener_url_publica(),
        "url_con_id": obtener_url_con_id(),
        "tunel": {
            "activo": obtener_tunel_activo(),
            "modo": "socketio",
            "servidor": URL_RENDER
        }
    }

# ==================== INICIAR SERVIDOR PÚBLICO ====================
def iniciar_servidor_publico():
    global ID_FIJO
    ID_FIJO = generar_id_fijo()
    
    ip_publica = obtener_ip_publica()
    ip_local = obtener_ip_local()
    nombre = socket.gethostname()
    url_publica = obtener_url_publica()
    
    registrar_dispositivo(nombre, ip_publica, ip_local)
    guardar_url_publica(url_publica)
    
    # Iniciar túnel Socket.io
    print(f"\n[INFO] Iniciando túnel Socket.io...")
    iniciar_cliente_socket()
    
    info = {
        "id": ID_FIJO,
        "nombre": nombre,
        "ip_publica": ip_publica,
        "ip_local": ip_local,
        "url": url_publica,
        "url_con_id": f"{url_publica}/?id={ID_FIJO}" if url_publica else None,
        "ultima_actualizacion": datetime.now().isoformat(),
        "tunel": {
            "activo": obtener_tunel_activo(),
            "modo": "socketio",
            "servidor": URL_RENDER
        }
    }
    
    print(f"\n{'='*60}")
    print(f"🔒 SERVIDOR PÚBLICO - GRUPO GSN")
    print(f"{'='*60}")
    print(f"   ID FIJO: {ID_FIJO}")
    print(f"   URL Pública: {url_publica}")
    print(f"   URL con ID: {info['url_con_id']}")
    print(f"   IP Local: {ip_local}")
    print(f"   Túnel: {'✅ Activo' if obtener_tunel_activo() else '⏳ Conectando...'}")
    print(f"{'='*60}")
    
    return info

# ==================== LIMPIAR DISPOSITIVOS ====================
def limpiar_dispositivos_inactivos():
    data = cargar_dispositivos()
    ahora = datetime.now()
    activos = []
    for d in data.get("dispositivos", []):
        ultima = d.get("ultima_actualizacion")
        if ultima:
            try:
                dt = datetime.fromisoformat(ultima)
                if (ahora - dt).total_seconds() < 86400:
                    activos.append(d)
            except:
                activos.append(d)
    data["dispositivos"] = activos
    guardar_dispositivos(data)
    return len(activos)

# ==================== INICIALIZAR ====================
ID_FIJO = generar_id_fijo()

print(f"[INFO] Servidor Público inicializado")
print(f"[INFO] ID FIJO: {ID_FIJO}")
print(f"[INFO] URL Pública: {obtener_url_publica()}")