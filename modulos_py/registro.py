# ==================== REGISTRO.PY - BACKEND DEL MÓDULO DE REGISTRO ====================

import json
import uuid
import hashlib
from datetime import datetime
from pathlib import Path

# Archivos de datos
ARCHIVO_USUARIOS = os.path.join(CARPETA_DATOS, "usuarios.json")

def inicializar_archivo_usuarios():
    """Inicializa el archivo de usuarios si no existe"""
    if not os.path.exists(ARCHIVO_USUARIOS):
        usuarios_default = {
            "usuarios": [
                {
                    "id": "USR-001",
                    "nombre": "Administrador",
                    "email": "admin@gruposn.com",
                    "cedula": "",
                    "telefono": "",
                    "empresa_id": None,
                    "empresa_nombre": None,
                    "rol": "admin",
                    "password": hashlib.sha256("admin123".encode()).hexdigest(),
                    "estado": "activo",
                    "fecha_registro": datetime.now().isoformat(),
                    "ultimo_acceso": None
                }
            ],
            "ultimo_id": 1
        }
        guardar_json(ARCHIVO_USUARIOS, usuarios_default)
        print("[OK] Archivo de usuarios inicializado")

def cargar_usuarios():
    """Carga todos los usuarios"""
    data = cargar_json(ARCHIVO_USUARIOS, {"usuarios": [], "ultimo_id": 0})
    return data

def obtener_usuario_por_id(user_id):
    """Obtiene un usuario por su ID"""
    data = cargar_usuarios()
    for usuario in data.get("usuarios", []):
        if usuario.get("id") == user_id:
            # No enviar la contraseña
            usuario_copia = usuario.copy()
            usuario_copia.pop("password", None)
            return usuario_copia
    return None

def obtener_usuario_por_email(email):
    """Obtiene un usuario por su email (para login)"""
    data = cargar_usuarios()
    for usuario in data.get("usuarios", []):
        if usuario.get("email", "").lower() == email.lower():
            return usuario
    return None

def crear_usuario(datos):
    """Crea un nuevo usuario"""
    data = cargar_usuarios()
    
    # Verificar si el email ya existe
    for usuario in data.get("usuarios", []):
        if usuario.get("email", "").lower() == datos.get("email", "").lower():
            return {"ok": False, "error": "El correo electrónico ya está registrado"}
    
    # Verificar si la cédula ya existe
    if datos.get("cedula"):
        for usuario in data.get("usuarios", []):
            if usuario.get("cedula") == datos.get("cedula"):
                return {"ok": False, "error": "La cédula ya está registrada"}
    
    # Generar nuevo ID
    nuevo_id_num = data.get("ultimo_id", 0) + 1
    nuevo_id = f"USR-{nuevo_id_num:03d}"
    
    # Obtener nombre de la empresa si se seleccionó
    empresa_nombre = None
    if datos.get("empresa_id"):
        empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
        for emp in empresas_data.get("empresas", []):
            if emp.get("id") == datos.get("empresa_id"):
                empresa_nombre = emp.get("nombre")
                break
    
    nuevo_usuario = {
        "id": nuevo_id,
        "nombre": datos.get("nombre", ""),
        "email": datos.get("email", ""),
        "cedula": datos.get("cedula", ""),
        "telefono": datos.get("telefono", ""),
        "empresa_id": datos.get("empresa_id"),
        "empresa_nombre": empresa_nombre,
        "rol": datos.get("rol", "usuario"),
        "password": hashlib.sha256(datos.get("password", "").encode()).hexdigest(),
        "estado": "activo",
        "fecha_registro": datetime.now().isoformat(),
        "ultimo_acceso": None
    }
    
    data["usuarios"].append(nuevo_usuario)
    data["ultimo_id"] = nuevo_id_num
    guardar_json(ARCHIVO_USUARIOS, data)
    
    # No devolver la contraseña
    usuario_retorno = nuevo_usuario.copy()
    usuario_retorno.pop("password", None)
    
    return {"ok": True, "usuario": usuario_retorno}

def actualizar_usuario(user_id, datos):
    """Actualiza un usuario existente"""
    data = cargar_usuarios()
    
    for i, usuario in enumerate(data.get("usuarios", [])):
        if usuario.get("id") == user_id:
            # Actualizar campos básicos
            if "nombre" in datos:
                usuario["nombre"] = datos["nombre"]
            if "email" in datos:
                # Verificar que el nuevo email no esté en uso por otro usuario
                for otro in data["usuarios"]:
                    if otro.get("id") != user_id and otro.get("email", "").lower() == datos["email"].lower():
                        return {"ok": False, "error": "El correo ya está en uso"}
                usuario["email"] = datos["email"]
            if "telefono" in datos:
                usuario["telefono"] = datos["telefono"]
            if "rol" in datos:
                usuario["rol"] = datos["rol"]
            if "estado" in datos:
                usuario["estado"] = datos["estado"]
            if "empresa_id" in datos:
                usuario["empresa_id"] = datos["empresa_id"]
                # Actualizar nombre de empresa
                empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
                for emp in empresas_data.get("empresas", []):
                    if emp.get("id") == datos["empresa_id"]:
                        usuario["empresa_nombre"] = emp.get("nombre")
                        break
            if "password" in datos and datos["password"]:
                usuario["password"] = hashlib.sha256(datos["password"].encode()).hexdigest()
            
            guardar_json(ARCHIVO_USUARIOS, data)
            
            usuario_retorno = usuario.copy()
            usuario_retorno.pop("password", None)
            return {"ok": True, "usuario": usuario_retorno}
    
    return {"ok": False, "error": "Usuario no encontrado"}

def eliminar_usuario(user_id):
    """Elimina un usuario (no permite eliminar al admin principal)"""
    data = cargar_usuarios()
    
    for i, usuario in enumerate(data.get("usuarios", [])):
        if usuario.get("id") == user_id:
            # No permitir eliminar al administrador principal
            if usuario.get("email") == "admin@gruposn.com":
                return {"ok": False, "error": "No se puede eliminar el administrador principal"}
            
            data["usuarios"].pop(i)
            guardar_json(ARCHIVO_USUARIOS, data)
            return {"ok": True}
    
    return {"ok": False, "error": "Usuario no encontrado"}

def autenticar_usuario(email, password):
    """Autentica un usuario para login"""
    usuario = obtener_usuario_por_email(email)
    if not usuario:
        return {"ok": False, "error": "Usuario no encontrado"}
    
    if usuario.get("estado") != "activo":
        return {"ok": False, "error": "Usuario inactivo o bloqueado"}
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if usuario.get("password") == password_hash:
        # Actualizar último acceso
        data = cargar_usuarios()
        for u in data["usuarios"]:
            if u.get("id") == usuario["id"]:
                u["ultimo_acceso"] = datetime.now().isoformat()
                break
        guardar_json(ARCHIVO_USUARIOS, data)
        
        usuario_retorno = usuario.copy()
        usuario_retorno.pop("password", None)
        return {"ok": True, "usuario": usuario_retorno}
    
    return {"ok": False, "error": "Contraseña incorrecta"}

# ==================== RUTAS API PARA REGISTRO ====================

@app.route('/api/usuarios', methods=['GET'])
def api_usuarios():
    """Obtener todos los usuarios"""
    data = cargar_usuarios()
    # Ocultar contraseñas
    usuarios_sin_password = []
    for u in data.get("usuarios", []):
        u_copy = u.copy()
        u_copy.pop("password", None)
        usuarios_sin_password.append(u_copy)
    return jsonify({"ok": True, "usuarios": usuarios_sin_password})

@app.route('/api/usuario/<user_id>', methods=['GET'])
def api_usuario(user_id):
    """Obtener un usuario específico"""
    usuario = obtener_usuario_por_id(user_id)
    if usuario:
        return jsonify({"ok": True, "usuario": usuario})
    return jsonify({"ok": False, "error": "Usuario no encontrado"})

@app.route('/api/registrar_usuario', methods=['POST'])
def api_registrar_usuario():
    """Registrar un nuevo usuario"""
    try:
        datos = request.get_json()
        resultado = crear_usuario(datos)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route('/api/actualizar_usuario', methods=['POST'])
def api_actualizar_usuario():
    """Actualizar un usuario existente"""
    try:
        datos = request.get_json()
        user_id = datos.get("id")
        if not user_id:
            return jsonify({"ok": False, "error": "ID de usuario requerido"})
        resultado = actualizar_usuario(user_id, datos)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route('/api/eliminar_usuario', methods=['POST'])
def api_eliminar_usuario():
    """Eliminar un usuario"""
    try:
        datos = request.get_json()
        user_id = datos.get("id")
        if not user_id:
            return jsonify({"ok": False, "error": "ID de usuario requerido"})
        resultado = eliminar_usuario(user_id)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route('/api/login', methods=['POST'])
def api_login():
    """Autenticar usuario"""
    try:
        datos = request.get_json()
        email = datos.get("email")
        password = datos.get("password")
        resultado = autenticar_usuario(email, password)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# Inicializar archivo de usuarios al iniciar
inicializar_archivo_usuarios()