# ==================== MODULO PAGINAS HIJO ====================
import uuid
import random
import string
import os
import re
import json
from datetime import datetime
from flask import jsonify, request

COLOR_PRIMARIO = "#f59e0b"
COLOR_SECUNDARIO = "#d97706"
COLOR_FONDO = "#0f0f1a"

ARCHIVO_PAGINAS = None
CARPETA_PAGINAS = None
_public_url_global = None
_main_module = None
_cargar_json = None
_guardar_json = None
_obtener_url_publica = None
_obtener_id_fijo = None

# ==================== INICIALIZACIÓN ====================
def inicializar_modulo(archivo_paginas, carpeta_paginas, main_module=None, main_funciones=None):
    global ARCHIVO_PAGINAS, CARPETA_PAGINAS, _main_module
    global _cargar_json, _guardar_json, _obtener_url_publica, _obtener_id_fijo
    
    ARCHIVO_PAGINAS = archivo_paginas
    CARPETA_PAGINAS = carpeta_paginas
    _main_module = main_module
    
    if main_funciones:
        _cargar_json = main_funciones.get('cargar_json')
        _guardar_json = main_funciones.get('guardar_json')
        _obtener_url_publica = main_funciones.get('obtener_url_publica')
        _obtener_id_fijo = main_funciones.get('obtener_id_fijo')
    
    print("[OK] Módulo Paginas Hijo inicializado")
    return True

# ==================== FUNCIONES JSON ====================
def cargar_json(ruta, default=None):
    if _cargar_json:
        return _cargar_json(ruta, default)
    if os.path.exists(ruta):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read().strip()
                if not contenido:
                    return default if default is not None else []
                return json.loads(contenido)
        except Exception as e:
            print(f"Error cargando {ruta}: {e}")
            return default if default is not None else []
    return default if default is not None else []

def guardar_json(ruta, data):
    if _guardar_json:
        return _guardar_json(ruta, data)
    try:
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error guardando {ruta}: {e}")
        return False

# ==================== FUNCIONES DE NEGOCIO ====================
def obtener_url_publica():
    """Obtiene la URL pública usando SOLO el Servidor Público"""
    global _public_url_global, _main_module
    
    # Si ya tenemos URL en memoria
    if _public_url_global:
        return _public_url_global
    
    # Intentar con la función pasada desde main
    if _obtener_url_publica:
        try:
            url = _obtener_url_publica()
            if url:
                _public_url_global = url
                return url
        except Exception as e:
            print(f"[WARN] Error en _obtener_url_publica: {e}")
    
    # Intentar desde el módulo principal - SOLO SERVIDOR PÚBLICO
    if _main_module:
        # Intentar con URL_RENDER (Servidor Público en Render)
        if hasattr(_main_module, 'URL_RENDER'):
            try:
                url = _main_module.URL_RENDER
                if url:
                    _public_url_global = url
                    print(f"[INFO] URL pública desde URL_RENDER: {url}")
                    return url
            except Exception as e:
                print(f"[WARN] Error accediendo a URL_RENDER: {e}")
        
        # Intentar con obtener_url_publica del módulo
        if hasattr(_main_module, 'obtener_url_publica'):
            try:
                url = _main_module.obtener_url_publica()
                if url:
                    _public_url_global = url
                    print(f"[INFO] URL pública desde main.obtener_url_publica: {url}")
                    return url
            except Exception as e:
                print(f"[WARN] Error en _main_module.obtener_url_publica: {e}")
        
        # Intentar con public_url_global
        if hasattr(_main_module, 'public_url_global'):
            try:
                url = _main_module.public_url_global
                if url:
                    _public_url_global = url
                    return url
            except Exception as e:
                print(f"[WARN] Error accediendo a public_url_global: {e}")
        
        # Intentar con ID_FIJO para construir URL
        if hasattr(_main_module, 'ID_FIJO') and hasattr(_main_module, 'URL_RENDER'):
            try:
                id_fijo = _main_module.ID_FIJO
                if id_fijo:
                    url = _main_module.URL_RENDER
                    _public_url_global = url
                    return url
            except:
                pass
    
    # Fallback a localhost
    print("[WARN] No se pudo obtener URL pública, usando localhost")
    return "http://127.0.0.1:5000"

def obtener_id_fijo():
    """Obtiene el ID Fijo del servidor público"""
    global _main_module
    
    # Primero intentar con la función pasada desde main
    if _obtener_id_fijo:
        try:
            id_fijo = _obtener_id_fijo()
            if id_fijo and id_fijo != 'NO-DISPONIBLE':
                print(f"[INFO] ID Fijo desde _obtener_id_fijo: {id_fijo}")
                return id_fijo
        except Exception as e:
            print(f"[WARN] Error en _obtener_id_fijo: {e}")
    
    # Intentar desde el módulo principal
    if _main_module:
        # ID_FIJO directo
        if hasattr(_main_module, 'ID_FIJO'):
            try:
                id_fijo = _main_module.ID_FIJO
                if id_fijo and id_fijo != 'NO-DISPONIBLE':
                    print(f"[INFO] ID Fijo desde _main_module.ID_FIJO: {id_fijo}")
                    return id_fijo
            except Exception as e:
                print(f"[WARN] Error accediendo a ID_FIJO: {e}")
        
        # Intentar obtener desde servidor_publico
        if hasattr(_main_module, 'servidor_publico'):
            try:
                if hasattr(_main_module.servidor_publico, 'ID_FIJO'):
                    id_fijo = _main_module.servidor_publico.ID_FIJO
                    if id_fijo and id_fijo != 'NO-DISPONIBLE':
                        print(f"[INFO] ID Fijo desde servidor_publico.ID_FIJO: {id_fijo}")
                        return id_fijo
            except Exception as e:
                print(f"[WARN] Error accediendo a servidor_publico.ID_FIJO: {e}")
    
    # Intentar cargar desde archivo de dispositivos
    try:
        import os
        import json
        from pathlib import Path
        
        # Buscar el archivo de dispositivos
        posibles_rutas = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'datos', 'dispositivos.json'),
            os.path.join(os.getcwd(), 'datos', 'dispositivos.json'),
            os.path.join(os.path.dirname(os.getcwd()), 'datos', 'dispositivos.json')
        ]
        
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                with open(ruta, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('id_fijo'):
                        id_fijo = data.get('id_fijo')
                        print(f"[INFO] ID Fijo desde archivo: {id_fijo}")
                        return id_fijo
    except Exception as e:
        print(f"[WARN] Error cargando ID Fijo desde archivo: {e}")
    
    print("[WARN] No se pudo obtener ID Fijo")
    return "NO-DISPONIBLE"

def set_public_url(url):
    global _public_url_global
    _public_url_global = url
    print(f"[INFO] URL pública establecida: {_public_url_global}")
    regenerar_todas_paginas()

def regenerar_todas_paginas():
    global _public_url_global
    if not _public_url_global:
        return
    paginas = cargar_paginas()
    for pagina in paginas.get("paginas", []):
        generar_html_pagina(pagina, _public_url_global)

def cargar_paginas():
    data = cargar_json(ARCHIVO_PAGINAS, {"paginas": []})
    if not isinstance(data, dict):
        return {"paginas": []}
    if "paginas" not in data:
        data["paginas"] = []
    return data

def guardar_paginas(data):
    return guardar_json(ARCHIVO_PAGINAS, data)

def obtener_pagina_por_url(url_id):
    for pagina in cargar_paginas().get("paginas", []):
        if pagina.get("url_id") == url_id:
            return pagina
    return None

def obtener_pagina_por_id(id_pagina):
    for pagina in cargar_paginas().get("paginas", []):
        if pagina.get("id") == id_pagina:
            return pagina
    return None

def crear_pagina(nombre, estilos=None):
    if estilos is None:
        estilos = {}
    
    paginas = cargar_paginas()
    
    url_id = re.sub(r'[^a-z0-9-]', '', nombre.lower().replace(" ", "-"))
    if not url_id:
        url_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    original = url_id
    counter = 1
    while any(p.get("url_id") == url_id for p in paginas["paginas"]):
        url_id = f"{original}-{counter}"
        counter += 1
    
    nueva_pagina = {
        "id": str(uuid.uuid4()),
        "nombre": nombre,
        "url_id": url_id,
        "estilos": {
            "color_primario": estilos.get("color_primario", COLOR_PRIMARIO),
            "color_secundario": estilos.get("color_secundario", COLOR_SECUNDARIO),
            "color_fondo": estilos.get("color_fondo", COLOR_FONDO),
            "titulo": estilos.get("titulo", nombre),
            "subtitulo": estilos.get("subtitulo", "Complete el formulario para solicitar combustible"),
            "logo": estilos.get("logo", "fa-gas-pump")
        },
        "elementos": estilos.get("elementos", []),
        "fecha": datetime.now().isoformat(),
        "activa": True
    }
    paginas["paginas"].append(nueva_pagina)
    guardar_paginas(paginas)
    
    url_publica = obtener_url_publica()
    generar_html_pagina(nueva_pagina, url_publica or "")
    
    return nueva_pagina

def eliminar_pagina(id_pagina):
    paginas = cargar_paginas()
    for pagina in paginas["paginas"]:
        if pagina.get("id") == id_pagina:
            ruta_html = os.path.join(CARPETA_PAGINAS, f"{pagina.get('id')}.html")
            if os.path.exists(ruta_html):
                os.remove(ruta_html)
            break
    paginas["paginas"] = [p for p in paginas["paginas"] if p.get("id") != id_pagina]
    return guardar_paginas(paginas)

def actualizar_pagina(id_pagina, estilos=None, elementos=None):
    if estilos is None:
        estilos = {}
    
    paginas = cargar_paginas()
    for i, p in enumerate(paginas["paginas"]):
        if p.get("id") == id_pagina:
            if estilos:
                if "estilos" not in paginas["paginas"][i]:
                    paginas["paginas"][i]["estilos"] = {}
                for key, value in estilos.items():
                    paginas["paginas"][i]["estilos"][key] = value
            
            if elementos is not None:
                paginas["paginas"][i]["elementos"] = elementos
            
            paginas["paginas"][i]["fecha_actualizacion"] = datetime.now().isoformat()
            guardar_paginas(paginas)
            
            url_publica = obtener_url_publica()
            generar_html_pagina(paginas["paginas"][i], url_publica or "")
            return True
    return False

def generar_html_pagina(pagina, url_publica=None):
    global CARPETA_PAGINAS, _public_url_global
    
    estilos = pagina.get("estilos", {})
    color_primario = estilos.get("color_primario", COLOR_PRIMARIO)
    color_secundario = estilos.get("color_secundario", COLOR_SECUNDARIO)
    color_fondo = estilos.get("color_fondo", COLOR_FONDO)
    titulo = estilos.get("titulo", pagina.get("nombre", "Solicitud de Combustible"))
    subtitulo = estilos.get("subtitulo", "Complete el formulario")
    logo = estilos.get("logo", "fa-gas-pump")
    elementos = pagina.get("elementos", [])
    
    if url_publica and url_publica != "":
        base_url = url_publica
    elif _public_url_global:
        base_url = _public_url_global
    else:
        base_url = "http://127.0.0.1:5000"
    
    # Obtener el HTML desde hijo_html.py
    try:
        from modulos_py.hijo_html import obtener_html_pagina
        html = obtener_html_pagina(base_url, color_primario, color_secundario, color_fondo, titulo, subtitulo, logo)
    except ImportError:
        # HTML de respaldo si no existe hijo_html.py
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>{titulo}</title></head>
        <body style="background:{color_fondo};color:white;font-family:Arial;">
            <h1 style="color:{color_primario};">{titulo}</h1>
            <p>{subtitulo}</p>
            <p>URL base: {base_url}</p>
            <p>🔒 ID Fijo: {obtener_id_fijo()}</p>
        </body>
        </html>
        """
    
    ruta_html = os.path.join(CARPETA_PAGINAS, f"{pagina['id']}.html")
    with open(ruta_html, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"[OK] HTML generado: {ruta_html}")
    return ruta_html

# ==================== FUNCIÓN PARA OBTENER ENLACES PREDEFINIDOS ====================
def obtener_enlaces_predefinidos():
    """Obtiene los enlaces predefinidos para primogénito y conductor usando el servidor público"""
    url_publica = obtener_url_publica()
    id_fijo = obtener_id_fijo()
    
    # Si no hay URL pública, usar localhost
    if not url_publica:
        url_publica = "http://127.0.0.1:5000"
    
    print(f"[INFO] Generando enlaces con URL: {url_publica}")
    print(f"[INFO] ID Fijo: {id_fijo}")
    
    enlaces = {
        "primogenito": {
            "url": f"{url_publica}/primogenito",
            "nombre": "📱 Primogénito (App de Pedidos Móvil)",
            "descripcion": "URL para la APK de Primogénito - Envía pedidos prioritarios",
            "icono": "fa-mobile-alt",
            "color": "#3b82f6",
            "activo": True,
            "id_fijo": id_fijo
        },
        "conductor": {
            "url": f"{url_publica}/conductor",
            "nombre": "🚛 Conductor (App de Ubicación GPS)",
            "descripcion": "URL para la APK de Conductor - Rastreo GPS en tiempo real",
            "icono": "fa-map-marked-alt",
            "color": "#10b981",
            "activo": True,
            "id_fijo": id_fijo
        },
        "servidor": {
            "url": f"{url_publica}/fijo",
            "nombre": "🌐 Servidor Público",
            "descripcion": f"ID Fijo: {id_fijo} - Comparte este enlace con otros dispositivos",
            "icono": "fa-globe",
            "color": "#f59e0b",
            "activo": True,
            "id_fijo": id_fijo
        },
        "servidor_id": {
            "url": f"{url_publica}/?id={id_fijo}",
            "nombre": "🔗 Enlace con ID Fijo",
            "descripcion": f"URL con ID Fijo: {id_fijo} - Conéctate desde cualquier red",
            "icono": "fa-link",
            "color": "#8b5cf6",
            "activo": True,
            "id_fijo": id_fijo
        }
    }
    
    return enlaces

# ==================== API ENDPOINTS (FUNCIONES, SIN DECORADORES) ====================
def api_paginas():
    return jsonify(cargar_paginas())

def api_crear_pagina():
    try:
        d = request.get_json()
        nombre = d.get('nombre', 'Nueva Pagina')
        estilos = d.get('estilos', {})
        pagina = crear_pagina(nombre, estilos)
        url_publica = obtener_url_publica()
        url_completa = f"{url_publica}/p/{pagina['url_id']}" if url_publica else f"/p/{pagina['url_id']}"
        return jsonify({"ok": True, "pagina": pagina, "url": url_completa})
    except Exception as e:
        print(f"[ERROR] api_crear_pagina: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_eliminar_pagina():
    try:
        d = request.get_json()
        id_pagina = d.get('id')
        if not id_pagina:
            return jsonify({"ok": False, "error": "ID no proporcionado"})
        return jsonify({"ok": eliminar_pagina(id_pagina)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_obtener_pagina(id_pagina):
    try:
        pagina = obtener_pagina_por_id(id_pagina)
        if pagina:
            return jsonify({"ok": True, "pagina": pagina})
        return jsonify({"ok": False, "error": "Pagina no encontrada"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_actualizar_pagina():
    try:
        d = request.get_json()
        id_pagina = d.get('id')
        if not id_pagina:
            return jsonify({"ok": False, "error": "ID no proporcionado"})
        
        estilos = d.get('estilos', {})
        elementos = d.get('elementos')
        
        resultado = actualizar_pagina(id_pagina, estilos, elementos)
        if resultado:
            return jsonify({"ok": True, "mensaje": "Página actualizada"})
        return jsonify({"ok": False, "error": "Página no encontrada"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_obtener_enlaces():
    """Retorna los enlaces predefinidos para copiar (primogénito, conductor, servidor y ID fijo)"""
    try:
        enlaces = obtener_enlaces_predefinidos()
        print(f"[INFO] Enlaces generados: {list(enlaces.keys())}")
        return jsonify({"ok": True, "enlaces": enlaces})
    except Exception as e:
        print(f"[ERROR] api_obtener_enlaces: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e), "enlaces": {}})

def api_obtener_info_servidor():
    """Retorna información del servidor público (URL e ID Fijo)"""
    try:
        url_publica = obtener_url_publica()
        id_fijo = obtener_id_fijo()
        return jsonify({
            "ok": True,
            "url": url_publica,
            "id": id_fijo,
            "url_con_id": f"{url_publica}/?id={id_fijo}" if url_publica and id_fijo else None
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})