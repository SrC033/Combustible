# ==================== MÓDULO CONFIGURACIÓN ====================
import smtplib
import os
import json
import hashlib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from flask import jsonify, request
import requests

# ==================== CONFIGURACIÓN ====================
ARCHIVO_CONFIG_IA = None
ARCHIVO_CONFIG_CORREO = None
ARCHIVO_CONFIG_SISTEMA = None
ARCHIVO_PEDIDOS = None
ARCHIVO_EMPRESAS = None
ARCHIVO_USUARIOS = None
REQUESTS_DISPONIBLE = False

_cargar_json = None
_guardar_json = None
_registrar_bitacora = None

CONFIG_IA_DEFAULT = {
    "webhook_url": "",
    "api_key": "",
    "enabled": False,
    "auto_send": False
}

CONFIG_CORREO_DEFAULT = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email_remitente": "",
    "email_password": "",
    "email_empresa": "gruposn@example.com",
    "enabled": False
}

MODULOS_SISTEMA = [
    {"id": "dashboard", "nombre": "Dashboard", "icono": "fa-chart-line"},
    {"id": "operaciones", "nombre": "Operaciones", "icono": "fa-clipboard-list"},
    {"id": "empresas", "nombre": "Clientes", "icono": "fa-building"},
    {"id": "facturacion", "nombre": "Facturación", "icono": "fa-file-invoice-dollar"},
    {"id": "flota", "nombre": "Flota", "icono": "fa-truck-moving"},
    {"id": "costos", "nombre": "Costos", "icono": "fa-coins"},
    {"id": "reportes", "nombre": "Reportes", "icono": "fa-chart-bar"},
    {"id": "paginas_hijo", "nombre": "Enlaces", "icono": "fa-copy"},
    {"id": "tablas_editables", "nombre": "Bitácora", "icono": "fa-table"},
    {"id": "configuracion", "nombre": "Configuración", "icono": "fa-cog"}
]

# ==================== INICIALIZACIÓN ====================
def inicializar_configuracion(main_funciones=None, rutas=None):
    global _cargar_json, _guardar_json, _registrar_bitacora
    global ARCHIVO_CONFIG_IA, ARCHIVO_CONFIG_CORREO, ARCHIVO_CONFIG_SISTEMA
    global ARCHIVO_PEDIDOS, ARCHIVO_EMPRESAS, ARCHIVO_USUARIOS, REQUESTS_DISPONIBLE
    
    if main_funciones:
        _cargar_json = main_funciones.get('cargar_json')
        _guardar_json = main_funciones.get('guardar_json')
        _registrar_bitacora = main_funciones.get('registrar_bitacora')
    
    if rutas:
        ARCHIVO_CONFIG_IA = rutas.get('config_ia')
        ARCHIVO_CONFIG_CORREO = rutas.get('config_correo')
        ARCHIVO_CONFIG_SISTEMA = rutas.get('config_sistema')
        ARCHIVO_PEDIDOS = rutas.get('pedidos')
        ARCHIVO_EMPRESAS = rutas.get('empresas')
        # ARCHIVO_USUARIOS no está en rutas_config, se pasa desde main_funciones o se define aquí
        if main_funciones and 'archivo_usuarios' in main_funciones:
            ARCHIVO_USUARIOS = main_funciones.get('archivo_usuarios')
    
    # Si no se pasó ARCHIVO_USUARIOS, usar el de main
    if not ARCHIVO_USUARIOS and rutas:
        base_dir = os.path.dirname(rutas.get('config_sistema', 'datos'))
        ARCHIVO_USUARIOS = os.path.join(base_dir, "usuarios.json")
    
    try:
        import requests
        REQUESTS_DISPONIBLE = True
    except:
        REQUESTS_DISPONIBLE = False
    
    print(f"[INFO] Módulo Configuración inicializado")
    print(f"[INFO] ARCHIVO_USUARIOS: {ARCHIVO_USUARIOS}")

# ==================== FUNCIONES DE PERSISTENCIA ====================
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
        except:
            return default if default is not None else []
    return default if default is not None else []

def guardar_json(ruta, data):
    if _guardar_json:
        return _guardar_json(ruta, data)
    try:
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

def registrar_bitacora(usuario, accion, detalles="", modulo=""):
    if _registrar_bitacora:
        return _registrar_bitacora(usuario, accion, detalles, modulo)

# ==================== FUNCIONES DE USUARIOS ====================
def cargar_usuarios():
    if not ARCHIVO_USUARIOS:
        return {"usuarios": [], "ultimo_id": 0}
    data = cargar_json(ARCHIVO_USUARIOS, {"usuarios": [], "ultimo_id": 0})
    if not isinstance(data, dict):
        return {"usuarios": [], "ultimo_id": 0}
    if "usuarios" not in data:
        data["usuarios"] = []
    if "ultimo_id" not in data:
        data["ultimo_id"] = 0
    return data

def guardar_usuarios(data):
    if not ARCHIVO_USUARIOS:
        return False
    return guardar_json(ARCHIVO_USUARIOS, data)

def generar_id_usuario():
    data = cargar_usuarios()
    data["ultimo_id"] = data.get("ultimo_id", 0) + 1
    return f"USR-{data['ultimo_id']:04d}"

def crear_usuario(datos):
    data = cargar_usuarios()
    
    # Verificar si el email ya existe
    email = datos.get('email', '')
    for u in data["usuarios"]:
        if u.get('email', '').lower() == email.lower():
            return None, "El email ya está registrado"
    
    # Generar ID
    nuevo_id = generar_id_usuario()
    
    # Encriptar contraseña
    password_plain = datos.get('password_plain', '')
    if password_plain:
        password_hash = hashlib.sha256(password_plain.encode()).hexdigest()
    else:
        password_hash = hashlib.sha256("123456".encode()).hexdigest()
        password_plain = "123456"
    
    nuevo_usuario = {
        "id": nuevo_id,
        "nombre": datos.get('nombre', ''),
        "email": email,
        "cedula": datos.get('cedula', ''),
        "telefono": datos.get('telefono', ''),
        "empresa_id": datos.get('empresa_id'),
        "empresa_nombre": datos.get('empresa_nombre', ''),
        "rol": datos.get('rol', 'usuario'),
        "estado": datos.get('estado', 'activo'),
        "password": password_hash,
        "password_plain": password_plain,
        "modulos_permitidos": datos.get('modulos_permitidos', ["dashboard"]),
        "fecha_creacion": datetime.now().isoformat()
    }
    
    data["usuarios"].append(nuevo_usuario)
    guardar_usuarios(data)
    return nuevo_usuario, None

def actualizar_usuario(datos):
    data = cargar_usuarios()
    usuario_id = datos.get('id')
    
    for i, u in enumerate(data["usuarios"]):
        if u.get('id') == usuario_id:
            # Actualizar campos
            if 'nombre' in datos:
                data["usuarios"][i]['nombre'] = datos['nombre']
            if 'email' in datos:
                data["usuarios"][i]['email'] = datos['email']
            if 'cedula' in datos:
                data["usuarios"][i]['cedula'] = datos.get('cedula', '')
            if 'telefono' in datos:
                data["usuarios"][i]['telefono'] = datos.get('telefono', '')
            if 'empresa_id' in datos:
                data["usuarios"][i]['empresa_id'] = datos.get('empresa_id')
            if 'empresa_nombre' in datos:
                data["usuarios"][i]['empresa_nombre'] = datos.get('empresa_nombre', '')
            if 'rol' in datos:
                data["usuarios"][i]['rol'] = datos['rol']
            if 'estado' in datos:
                data["usuarios"][i]['estado'] = datos['estado']
            if 'modulos_permitidos' in datos:
                data["usuarios"][i]['modulos_permitidos'] = datos['modulos_permitidos']
            
            # Actualizar contraseña si se proporciona
            if 'password' in datos and datos['password']:
                password_hash = hashlib.sha256(datos['password'].encode()).hexdigest()
                data["usuarios"][i]['password'] = password_hash
                data["usuarios"][i]['password_plain'] = datos['password']
            
            data["usuarios"][i]['fecha_actualizacion'] = datetime.now().isoformat()
            guardar_usuarios(data)
            return data["usuarios"][i], None
    
    return None, "Usuario no encontrado"

def eliminar_usuario(usuario_id):
    data = cargar_usuarios()
    original_count = len(data["usuarios"])
    data["usuarios"] = [u for u in data["usuarios"] if u.get('id') != usuario_id]
    
    if len(data["usuarios"]) < original_count:
        guardar_usuarios(data)
        return True
    return False

def obtener_usuario_por_id(usuario_id):
    data = cargar_usuarios()
    for u in data["usuarios"]:
        if u.get('id') == usuario_id:
            return u
    return None

def obtener_usuario_por_email(email):
    data = cargar_usuarios()
    for u in data["usuarios"]:
        if u.get('email', '').lower() == email.lower():
            return u
    return None

# ==================== FUNCIONES DE CONFIGURACIÓN ====================
def cargar_config_ia():
    return cargar_json(ARCHIVO_CONFIG_IA, CONFIG_IA_DEFAULT)

def guardar_config_ia(config):
    return guardar_json(ARCHIVO_CONFIG_IA, config)

def cargar_config_correo():
    return cargar_json(ARCHIVO_CONFIG_CORREO, CONFIG_CORREO_DEFAULT)

def guardar_config_correo(config):
    return guardar_json(ARCHIVO_CONFIG_CORREO, config)

def cargar_config_sistema():
    return cargar_json(ARCHIVO_CONFIG_SISTEMA, {})

def guardar_config_sistema(config):
    return guardar_json(ARCHIVO_CONFIG_SISTEMA, config)

# ==================== FUNCIONES DE NEGOCIO ====================
def enviar_factura_correo(destinatario, nombre_cliente, factura_pdf_path, factura_data):
    config = cargar_config_correo()
    if not config.get('enabled', False):
        return False
    if not config.get('email_remitente') or not config.get('email_password'):
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = config.get('email_remitente')
        msg['To'] = destinatario
        msg['Subject'] = f"Factura Combustible - Grupo GSN - {factura_data.get('id', 'FAC')}"
        
        cuerpo = f"""
        <html>
        <body>
            <div style="max-width:600px; margin:0 auto;">
                <div style="background:linear-gradient(135deg,#f59e0b,#d97706);padding:20px;text-align:center;">
                    <h2 style="color:white;">GRUPO GSN</h2>
                    <p style="color:white;">Sistema de Gestión de Combustible</p>
                </div>
                <div style="padding:20px;">
                    <p>Estimado(a) <strong>{nombre_cliente}</strong>,</p>
                    <p>Adjunto encontrará la factura correspondiente.</p>
                    <p><strong>Factura No.:</strong> {factura_data.get('id', 'N/A')}<br>
                    <strong>Total:</strong> C${factura_data.get('total', 0):,.2f}</p>
                    <p>Gracias por su preferencia.</p>
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(cuerpo, 'html'))
        with open(factura_pdf_path, 'rb') as f:
            adjunto = MIMEApplication(f.read(), _subtype="pdf")
            adjunto.add_header('Content-Disposition', 'attachment', filename=os.path.basename(factura_pdf_path))
            msg.attach(adjunto)
        
        server = smtplib.SMTP(config.get('smtp_server'), config.get('smtp_port'))
        server.starttls()
        server.login(config.get('email_remitente'), config.get('email_password'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False

def enviar_a_ia():
    config = cargar_config_ia()
    if not config.get('enabled', False):
        return False
    webhook_url = config.get('webhook_url', '')
    if not webhook_url:
        return False
    
    pedidos = cargar_json(ARCHIVO_PEDIDOS, [])
    empresas = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "total_pedidos": len(pedidos),
        "total_ventas": sum(p.get('costo_total', 0) for p in pedidos),
        "total_galones": sum(p.get('galones', 0) for p in pedidos),
        "empresas_activas": len(empresas.get('empresas', []))
    }
    
    headers = {}
    if config.get('api_key'):
        headers['Authorization'] = f"Bearer {config['api_key']}"
    
    try:
        if REQUESTS_DISPONIBLE:
            response = requests.post(webhook_url, json=data, headers=headers, timeout=10)
            return response.status_code == 200
        return False
    except:
        return False

# ==================== API ENDPOINTS ====================

# ---- USUARIOS ----
def api_obtener_usuarios():
    try:
        data = cargar_usuarios()
        usuarios = data.get("usuarios", [])
        # No enviar contraseñas hasheadas, solo las planas si existen
        for u in usuarios:
            u.pop('password', None)
        return jsonify({"ok": True, "usuarios": usuarios})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "usuarios": []})

def api_registrar_usuario():
    try:
        data = request.get_json()
        nuevo_usuario, error = crear_usuario(data)
        
        if error:
            return jsonify({"ok": False, "error": error})
        
        # No enviar contraseña hasheada
        nuevo_usuario.pop('password', None)
        registrar_bitacora(
            data.get('usuario', 'sistema'),
            "Crear Usuario",
            f"ID: {nuevo_usuario.get('id')} - {nuevo_usuario.get('nombre')}",
            "Configuración"
        )
        return jsonify({"ok": True, "usuario": nuevo_usuario})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_actualizar_usuario():
    try:
        data = request.get_json()
        usuario_actualizado, error = actualizar_usuario(data)
        
        if error:
            return jsonify({"ok": False, "error": error})
        
        usuario_actualizado.pop('password', None)
        registrar_bitacora(
            data.get('usuario', 'sistema'),
            "Actualizar Usuario",
            f"ID: {usuario_actualizado.get('id')} - {usuario_actualizado.get('nombre')}",
            "Configuración"
        )
        return jsonify({"ok": True, "usuario": usuario_actualizado})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_eliminar_usuario():
    try:
        data = request.get_json()
        usuario_id = data.get('id')
        
        if not usuario_id:
            return jsonify({"ok": False, "error": "Se requiere ID"})
        
        # No permitir eliminar al admin principal
        usuario = obtener_usuario_por_id(usuario_id)
        if usuario and usuario.get('email') == 'admin@gruposn.com':
            return jsonify({"ok": False, "error": "No se puede eliminar al administrador principal"})
        
        if eliminar_usuario(usuario_id):
            registrar_bitacora(
                data.get('usuario', 'sistema'),
                "Eliminar Usuario",
                f"ID: {usuario_id}",
                "Configuración"
            )
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Usuario no encontrado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ---- IA ----
def api_config_ia():
    if request.method == 'GET':
        config = cargar_config_ia()
        return jsonify({"ok": True, "config": config})
    else:
        try:
            config = request.get_json()
            guardar_config_ia(config)
            registrar_bitacora(config.get('usuario', 'sistema'), "Configurar IA", "", "Configuración")
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)})

# ---- CORREO ----
def api_config_correo():
    if request.method == 'GET':
        config = cargar_config_correo()
        return jsonify({"ok": True, "config": config})
    else:
        try:
            config = request.get_json()
            guardar_config_correo(config)
            registrar_bitacora(config.get('usuario', 'sistema'), "Configurar Correo", "", "Configuración")
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)})

# ---- SISTEMA ----
def api_config_sistema():
    if request.method == 'GET':
        config = cargar_config_sistema()
        return jsonify({"ok": True, "config": config})
    else:
        try:
            config = request.get_json()
            guardar_config_sistema(config)
            registrar_bitacora(config.get('usuario', 'sistema'), "Configurar Sistema", "", "Configuración")
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)})

# ---- CORREO PRUEBA ----
def api_probar_correo():
    try:
        data = request.get_json()
        email_destino = data.get('email', '')
        config = cargar_config_correo()
        
        if not email_destino:
            return jsonify({"ok": False, "error": "Email destino requerido"})
        if not config.get('enabled', False):
            return jsonify({"ok": False, "error": "Correo no habilitado"})
        
        msg = MIMEMultipart()
        msg['From'] = config.get('email_remitente')
        msg['To'] = email_destino
        msg['Subject'] = "Prueba de correo - Grupo GSN"
        cuerpo = "<h2>Prueba de configuración</h2><p>Si recibe esto, la configuración es correcta.</p>"
        msg.attach(MIMEText(cuerpo, 'html'))
        
        server = smtplib.SMTP(config.get('smtp_server'), config.get('smtp_port'))
        server.starttls()
        server.login(config.get('email_remitente'), config.get('email_password'))
        server.send_message(msg)
        server.quit()
        
        registrar_bitacora(data.get('usuario', 'sistema'), "Probar Correo", f"Prueba enviada a {email_destino}", "Configuración")
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ---- IA ENVIO ----
def api_enviar_ia_ahora():
    try:
        resultado = enviar_a_ia()
        if resultado:
            registrar_bitacora(request.get_json().get('usuario', 'sistema'), "Enviar IA", "Datos enviados", "Configuración")
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Error enviando datos"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})