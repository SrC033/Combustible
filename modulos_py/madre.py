#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MADRE.PY - Gestión de Temas y Estilos por Usuario
Este módulo maneja la persistencia de temas seleccionados por cada usuario.
Los temas se guardan en un archivo JSON y se cargan al iniciar sesión.
"""

import os
import sys
import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

# ==================== CONFIGURACIÓN ====================
def get_data_path():
    """Obtiene la ruta de datos según el entorno"""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, 'data')
    return os.path.abspath(".")

# Ruta del archivo de temas
ARCHIVO_TEMAS_USUARIOS = os.path.join(get_data_path(), "datos", "temas_usuarios.json")
CARPETA_IMAGENES_FONDO = os.path.join(get_data_path(), "datos", "imagenes_fondo")

# Crear carpeta de imágenes de fondo
Path(CARPETA_IMAGENES_FONDO).mkdir(parents=True, exist_ok=True)

# ==================== TEMAS DISPONIBLES ====================
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

# ==================== COLORES POR DEFECTO ====================
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
    "fondo": 0.75,
    "tarjetas": 0.85,
    "bordes": 0.20,
    "blur": 10
}

MODULOS_POR_DEFECTO = [
    "dashboard", "operaciones", "empresas", "facturacion",
    "flota", "costos", "reportes", "paginas_hijo",
    "tablas_editables", "configuracion"
]

# ==================== FUNCIONES ====================

def cargar_json(ruta, default=None):
    """Carga un archivo JSON de forma segura"""
    if os.path.exists(ruta):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read().strip()
                if not contenido:
                    return default if default is not None else {}
                return json.loads(contenido)
        except Exception as e:
            print(f"[ERROR] Error cargando {ruta}: {e}")
            return default if default is not None else {}
    return default if default is not None else {}

def guardar_json(ruta, data):
    """Guarda un archivo JSON de forma segura"""
    try:
        Path(os.path.dirname(ruta)).mkdir(parents=True, exist_ok=True)
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Error guardando {ruta}: {e}")
        return False

def obtener_clave_usuario(usuario_id, email=None):
    """Obtiene una clave única para el usuario"""
    if usuario_id:
        return f"usuario_{usuario_id}"
    elif email:
        return f"usuario_{hashlib.md5(email.lower().encode()).hexdigest()[:8]}"
    return "usuario_default"

def obtener_carpeta_usuario(email):
    """Obtiene la carpeta de imágenes para un usuario específico"""
    if email:
        hash_email = hashlib.md5(email.lower().encode()).hexdigest()[:16]
        carpeta = os.path.join(CARPETA_IMAGENES_FONDO, hash_email)
        Path(carpeta).mkdir(parents=True, exist_ok=True)
        return carpeta
    return CARPETA_IMAGENES_FONDO

# ==================== FUNCIONES PRINCIPALES DE TEMAS ====================

def obtener_tema_completo_usuario(usuario_id, email=None):
    """
    Obtiene la configuración completa del tema para un usuario
    
    Args:
        usuario_id (str): ID del usuario
        email (str): Email del usuario (fallback)
    
    Returns:
        dict: Configuración completa del tema
    """
    temas = cargar_json(ARCHIVO_TEMAS_USUARIOS, {})
    clave = obtener_clave_usuario(usuario_id, email)
    
    if clave in temas:
        tema_data = temas[clave]
        # Asegurar que todos los campos existan
        colores = tema_data.get("colores", {})
        colores_completos = {**COLORES_POR_DEFECTO, **colores}
        
        logo = tema_data.get("logo", {})
        logo_completo = {**LOGO_POR_DEFECTO, **logo}
        
        transparencia = tema_data.get("transparencia", {})
        transparencia_completa = {**TRANSPARENCIA_POR_DEFECTO, **transparencia}
        
        modulos = tema_data.get("modulos", MODULOS_POR_DEFECTO)
        
        return {
            "tema": tema_data.get("tema", "default"),
            "imagen_url": tema_data.get("imagen_url"),
            "colores": colores_completos,
            "logo": logo_completo,
            "transparencia": transparencia_completa,
            "modulos": modulos,
            "fecha_actualizacion": tema_data.get("fecha_actualizacion", datetime.now().isoformat()),
            "color_primario": colores_completos["primario"],
            "color_secundario": colores_completos["secundario"]
        }
    
    # Si no hay tema guardado, retornar valores por defecto
    return {
        "tema": "default",
        "imagen_url": None,
        "colores": COLORES_POR_DEFECTO.copy(),
        "logo": LOGO_POR_DEFECTO.copy(),
        "transparencia": TRANSPARENCIA_POR_DEFECTO.copy(),
        "modulos": MODULOS_POR_DEFECTO.copy(),
        "fecha_actualizacion": datetime.now().isoformat(),
        "color_primario": COLORES_POR_DEFECTO["primario"],
        "color_secundario": COLORES_POR_DEFECTO["secundario"]
    }

def guardar_tema_completo_usuario(usuario_id, tema, imagen_url, colores, logo, transparencia, modulos, email=None):
    """
    Guarda la configuración completa del tema para un usuario
    
    Args:
        usuario_id (str): ID del usuario
        tema (str): Nombre del tema
        imagen_url (str): URL de la imagen
        colores (dict): Colores personalizados
        logo (dict): Datos del logo
        transparencia (dict): Configuración de transparencia
        modulos (list): Lista de módulos seleccionados
        email (str): Email del usuario (fallback)
    
    Returns:
        bool: True si se guardó correctamente
    """
    temas = cargar_json(ARCHIVO_TEMAS_USUARIOS, {})
    clave = obtener_clave_usuario(usuario_id, email)
    
    if tema not in TEMAS_DISPONIBLES and tema != "image":
        tema = "default"
    
    # Asegurar que todos los campos de colores estén presentes
    colores_completos = {**COLORES_POR_DEFECTO, **(colores or {})}
    
    # Asegurar que todos los campos del logo estén presentes
    logo_completo = {**LOGO_POR_DEFECTO, **(logo or {})}
    
    # Asegurar que todos los campos de transparencia estén presentes
    transparencia_completa = {**TRANSPARENCIA_POR_DEFECTO, **(transparencia or {})}
    
    # Asegurar que modulos sea una lista
    modulos_completos = modulos or MODULOS_POR_DEFECTO
    
    temas[clave] = {
        "tema": tema,
        "imagen_url": imagen_url,
        "colores": colores_completos,
        "logo": logo_completo,
        "transparencia": transparencia_completa,
        "modulos": modulos_completos,
        "fecha_actualizacion": datetime.now().isoformat(),
        "color_primario": colores_completos["primario"],
        "color_secundario": colores_completos["secundario"]
    }
    
    resultado = guardar_json(ARCHIVO_TEMAS_USUARIOS, temas)
    print(f"[INFO] Tema completo guardado para usuario {email or usuario_id}: {tema}")
    print(f"[INFO] Colores guardados: {colores_completos}")
    print(f"[INFO] Módulos guardados: {modulos_completos}")
    return resultado

def obtener_colores_usuario(usuario_id, email=None):
    """Obtiene solo los colores del tema de un usuario"""
    tema = obtener_tema_completo_usuario(usuario_id, email)
    return tema.get("colores", COLORES_POR_DEFECTO.copy())

def obtener_logo_usuario(usuario_id, email=None):
    """Obtiene solo el logo del tema de un usuario"""
    tema = obtener_tema_completo_usuario(usuario_id, email)
    return tema.get("logo", LOGO_POR_DEFECTO.copy())

def obtener_transparencia_usuario(usuario_id, email=None):
    """Obtiene solo la transparencia del tema de un usuario"""
    tema = obtener_tema_completo_usuario(usuario_id, email)
    return tema.get("transparencia", TRANSPARENCIA_POR_DEFECTO.copy())

def obtener_modulos_usuario(usuario_id, email=None):
    """Obtiene solo los módulos seleccionados de un usuario"""
    tema = obtener_tema_completo_usuario(usuario_id, email)
    return tema.get("modulos", MODULOS_POR_DEFECTO.copy())

def obtener_tema_por_email(email):
    """Obtiene el tema completo usando solo el email (para login)"""
    return obtener_tema_completo_usuario(None, email)

def guardar_tema_por_email(email, tema, imagen_url=None, colores=None, logo=None, transparencia=None, modulos=None):
    """Guarda el tema usando solo el email (para login)"""
    if not email:
        return False
    
    # Usar valores por defecto si no se proporcionan
    colores = colores or COLORES_POR_DEFECTO.copy()
    logo = logo or LOGO_POR_DEFECTO.copy()
    transparencia = transparencia or TRANSPARENCIA_POR_DEFECTO.copy()
    modulos = modulos or MODULOS_POR_DEFECTO.copy()
    
    return guardar_tema_completo_usuario(None, tema, imagen_url, colores, logo, transparencia, modulos, email)

def eliminar_tema_usuario(usuario_id, email=None):
    """Elimina el tema guardado de un usuario (vuelve a default)"""
    temas = cargar_json(ARCHIVO_TEMAS_USUARIOS, {})
    clave = obtener_clave_usuario(usuario_id, email)
    
    if clave in temas:
        del temas[clave]
        return guardar_json(ARCHIVO_TEMAS_USUARIOS, temas)
    return True

def obtener_todos_temas_usuarios():
    """Obtiene todos los temas guardados de todos los usuarios"""
    return cargar_json(ARCHIVO_TEMAS_USUARIOS, {})

def get_css_para_tema(tema_nombre, imagen_url=None, colores=None):
    """
    Genera el CSS para un tema específico con colores personalizados
    
    Args:
        tema_nombre (str): Nombre del tema
        imagen_url (str): URL de la imagen (para tema image)
        colores (dict): Colores personalizados
    
    Returns:
        str: CSS del tema
    """
    colores = colores or COLORES_POR_DEFECTO
    
    if tema_nombre == "image" and imagen_url:
        return f"""
        body.image-theme {{
            background: url('{imagen_url}') center/cover no-repeat fixed;
            position: relative;
        }}
        body.image-theme::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0);
            z-index: -1;
        }}
        """
    
    tema = TEMAS_DISPONIBLES.get(tema_nombre, TEMAS_DISPONIBLES["default"])
    
    if tema_nombre == "default":
        return f"""
        body.default-theme {{
            background: {tema['fondo']};
            color: {colores.get('texto', tema['color_texto'])};
        }}
        """
    elif tema_nombre == "dark":
        return f"""
        body.dark-theme {{
            background: {tema['fondo']};
            color: {colores.get('texto', tema['color_texto'])};
        }}
        """
    elif tema_nombre == "light":
        return f"""
        body.light-theme {{
            background: {tema['fondo']};
            color: {colores.get('texto', tema['color_texto'])};
        }}
        """
    elif tema_nombre == "navy":
        return f"""
        body.navy-theme {{
            background: {tema['fondo']};
            color: {colores.get('texto', tema['color_texto'])};
        }}
        """
    elif tema_nombre == "nature":
        return f"""
        body.nature-theme {{
            background: {tema['fondo']};
            color: {colores.get('texto', tema['color_texto'])};
        }}
        """
    
    return ""

def inicializar_modulo_temas():
    """Inicializa el módulo de temas creando el archivo si no existe"""
    if not os.path.exists(ARCHIVO_TEMAS_USUARIOS):
        guardar_json(ARCHIVO_TEMAS_USUARIOS, {})
        print("[INFO] Archivo de temas de usuarios creado")
    
    Path(CARPETA_IMAGENES_FONDO).mkdir(parents=True, exist_ok=True)
    
    print(f"[INFO] Módulo de temas inicializado")
    print(f"[INFO] Archivo: {ARCHIVO_TEMAS_USUARIOS}")
    print(f"[INFO] Carpeta de imágenes: {CARPETA_IMAGENES_FONDO}")

# ==================== API PARA FLASK ====================
def registrar_rutas_temas(app):
    """Registra las rutas API para temas en la aplicación Flask"""
    
    @app.route('/api/obtener_tema_completo', methods=['GET'])
    def api_obtener_tema_completo():
        """Obtiene el tema completo del usuario actual"""
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
            
            tema_data = obtener_tema_completo_usuario(usuario_id, email)
            
            return jsonify({
                "ok": True,
                "tema": tema_data
            })
        except Exception as e:
            print(f"[ERROR] api_obtener_tema_completo: {e}")
            return jsonify({"ok": False, "error": str(e)})
    
    @app.route('/api/guardar_tema_completo', methods=['POST'])
    def api_guardar_tema_completo():
        """Guarda la configuración completa del tema"""
        try:
            data = request.get_json()
            print(f"[DEBUG] Datos recibidos en guardar_tema_completo: {data}")
            
            tema = data.get('tema', 'default')
            imagen_url = data.get('imagen_url')
            colores = data.get('colores', {})
            logo = data.get('logo', {})
            transparencia = data.get('transparencia', {})
            modulos = data.get('modulos', [])
            
            usuario_data = request.headers.get('X-User-Data')
            usuario_id = None
            email = None
            
            if usuario_data:
                try:
                    usuario = json.loads(usuario_data)
                    usuario_id = usuario.get('id')
                    email = usuario.get('email')
                    print(f"[DEBUG] Usuario: {email} (ID: {usuario_id})")
                except Exception as e:
                    print(f"[ERROR] Error parseando usuario: {e}")
            
            if not email and not usuario_id:
                return jsonify({"ok": False, "error": "Usuario no autenticado"})
            
            resultado = guardar_tema_completo_usuario(usuario_id, tema, imagen_url, colores, logo, transparencia, modulos, email)
            
            if resultado:
                return jsonify({"ok": True})
            return jsonify({"ok": False, "error": "Error al guardar"})
        except Exception as e:
            print(f"[ERROR] api_guardar_tema_completo: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"ok": False, "error": str(e)})
    
    @app.route('/api/obtener_tema_por_email/<email>', methods=['GET'])
    def api_obtener_tema_por_email(email):
        """Obtiene el tema completo usando solo el email (para login)"""
        try:
            if not email:
                return jsonify({"ok": False, "error": "Email requerido"})
            
            tema_data = obtener_tema_por_email(email)
            
            if tema_data:
                return jsonify({
                    "ok": True,
                    "tema": tema_data
                })
            
            return jsonify({
                "ok": True,
                "tema": {
                    "tema": "default",
                    "imagen_url": None,
                    "colores": COLORES_POR_DEFECTO.copy(),
                    "logo": LOGO_POR_DEFECTO.copy(),
                    "transparencia": TRANSPARENCIA_POR_DEFECTO.copy(),
                    "modulos": MODULOS_POR_DEFECTO.copy(),
                    "fecha_actualizacion": datetime.now().isoformat(),
                    "color_primario": COLORES_POR_DEFECTO["primario"],
                    "color_secundario": COLORES_POR_DEFECTO["secundario"]
                }
            })
        except Exception as e:
            print(f"[ERROR] api_obtener_tema_por_email: {e}")
            return jsonify({"ok": False, "error": str(e)})
    
    @app.route('/api/guardar_tema_por_email', methods=['POST'])
    def api_guardar_tema_por_email():
        """Guarda el tema usando solo el email (para login)"""
        try:
            data = request.get_json()
            email = data.get('email')
            tema = data.get('tema', 'default')
            imagen_url = data.get('imagen_url')
            colores = data.get('colores', {})
            logo = data.get('logo', {})
            transparencia = data.get('transparencia', {})
            modulos = data.get('modulos', [])
            
            if not email:
                return jsonify({"ok": False, "error": "Email requerido"})
            
            resultado = guardar_tema_por_email(email, tema, imagen_url, colores, logo, transparencia, modulos)
            
            if resultado:
                return jsonify({"ok": True})
            return jsonify({"ok": False, "error": "Error al guardar"})
        except Exception as e:
            print(f"[ERROR] api_guardar_tema_por_email: {e}")
            return jsonify({"ok": False, "error": str(e)})
    
    @app.route('/api/obtener_colores_usuario', methods=['GET'])
    def api_obtener_colores_usuario():
        """Obtiene solo los colores del usuario actual"""
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
            
            colores = obtener_colores_usuario(usuario_id, email)
            
            return jsonify({
                "ok": True,
                "colores": colores
            })
        except Exception as e:
            print(f"[ERROR] api_obtener_colores_usuario: {e}")
            return jsonify({"ok": False, "error": str(e)})
    
    @app.route('/api/obtener_logo_usuario', methods=['GET'])
    def api_obtener_logo_usuario():
        """Obtiene solo el logo del usuario actual"""
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
            
            logo = obtener_logo_usuario(usuario_id, email)
            
            return jsonify({
                "ok": True,
                "logo": logo
            })
        except Exception as e:
            print(f"[ERROR] api_obtener_logo_usuario: {e}")
            return jsonify({"ok": False, "error": str(e)})
    
    @app.route('/api/obtener_transparencia_usuario', methods=['GET'])
    def api_obtener_transparencia_usuario():
        """Obtiene solo la transparencia del usuario actual"""
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
            
            transparencia = obtener_transparencia_usuario(usuario_id, email)
            
            return jsonify({
                "ok": True,
                "transparencia": transparencia
            })
        except Exception as e:
            print(f"[ERROR] api_obtener_transparencia_usuario: {e}")
            return jsonify({"ok": False, "error": str(e)})
    
    @app.route('/api/obtener_modulos_usuario', methods=['GET'])
    def api_obtener_modulos_usuario():
        """Obtiene solo los módulos seleccionados del usuario actual"""
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
            
            modulos = obtener_modulos_usuario(usuario_id, email)
            
            return jsonify({
                "ok": True,
                "modulos": modulos
            })
        except Exception as e:
            print(f"[ERROR] api_obtener_modulos_usuario: {e}")
            return jsonify({"ok": False, "error": str(e)})
    
    @app.route('/api/temas_disponibles', methods=['GET'])
    def api_temas_disponibles():
        """Obtiene la lista de temas disponibles"""
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
            print(f"[ERROR] api_temas_disponibles: {e}")
            return jsonify({"ok": False, "error": str(e)})
    
    @app.route('/api/eliminar_tema_usuario', methods=['POST'])
    def api_eliminar_tema_usuario():
        """Elimina el tema guardado del usuario (vuelve a default)"""
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
            
            resultado = eliminar_tema_usuario(usuario_id, email)
            
            if resultado:
                return jsonify({"ok": True})
            return jsonify({"ok": False, "error": "Error al eliminar"})
        except Exception as e:
            print(f"[ERROR] api_eliminar_tema_usuario: {e}")
            return jsonify({"ok": False, "error": str(e)})
    
    # ==================== RUTAS PARA IMÁGENES DE FONDO ====================
    
    @app.route('/api/subir_imagen_fondo', methods=['POST'])
    def api_subir_imagen_fondo():
        """Sube una imagen de fondo personalizada para el usuario"""
        try:
            if 'imagen' not in request.files:
                return jsonify({"ok": False, "error": "No se envió ninguna imagen"})
            
            file = request.files['imagen']
            if file.filename == '':
                return jsonify({"ok": False, "error": "Nombre de archivo vacío"})
            
            usuario_data = request.headers.get('X-User-Data')
            email = None
            if usuario_data:
                try:
                    usuario = json.loads(usuario_data)
                    email = usuario.get('email')
                except:
                    pass
            
            if not email:
                return jsonify({"ok": False, "error": "Usuario no autenticado"})
            
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if ext not in allowed_extensions:
                return jsonify({"ok": False, "error": f"Formato no permitido. Use: {', '.join(allowed_extensions)}"})
            
            carpeta_usuario = obtener_carpeta_usuario(email)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"fondo_{timestamp}.{ext}"
            ruta_archivo = os.path.join(carpeta_usuario, nombre_archivo)
            
            file.save(ruta_archivo)
            print(f"[DEBUG] Imagen guardada: {ruta_archivo}")
            
            hash_email = hashlib.md5(email.lower().encode()).hexdigest()[:16]
            url = f"/api/imagen_fondo/{hash_email}/{nombre_archivo}"
            
            return jsonify({"ok": True, "url": url, "filename": nombre_archivo})
        except Exception as e:
            print(f"[ERROR] api_subir_imagen_fondo: {e}")
            return jsonify({"ok": False, "error": str(e)})
    
    @app.route('/api/imagen_fondo/<carpeta_usuario>/<filename>', methods=['GET'])
    def api_servir_imagen_fondo(carpeta_usuario, filename):
        """Sirve una imagen de fondo de la carpeta del usuario"""
        try:
            ruta_carpeta = os.path.join(CARPETA_IMAGENES_FONDO, carpeta_usuario)
            if not os.path.exists(ruta_carpeta):
                return jsonify({"error": "Carpeta no encontrada"}), 404
            return send_from_directory(ruta_carpeta, filename)
        except Exception as e:
            print(f"[ERROR] api_servir_imagen_fondo: {e}")
            return jsonify({"error": "Imagen no encontrada"}), 404
    
    @app.route('/api/eliminar_imagen_fondo', methods=['POST'])
    def api_eliminar_imagen_fondo():
        """Elimina la imagen de fondo del usuario"""
        try:
            usuario_data = request.headers.get('X-User-Data')
            email = None
            if usuario_data:
                try:
                    usuario = json.loads(usuario_data)
                    email = usuario.get('email')
                except:
                    pass
            
            if not email:
                return jsonify({"ok": False, "error": "Usuario no autenticado"})
            
            clave = f"usuario_{hashlib.md5(email.lower().encode()).hexdigest()[:8]}"
            temas = cargar_json(ARCHIVO_TEMAS_USUARIOS, {})
            
            if clave in temas and 'imagen_url' in temas[clave]:
                imagen_url = temas[clave].get('imagen_url')
                if imagen_url:
                    partes = imagen_url.split('/')
                    if len(partes) >= 2:
                        filename = partes[-1]
                        carpeta_usuario = partes[-2]
                        ruta_archivo = os.path.join(CARPETA_IMAGENES_FONDO, carpeta_usuario, filename)
                        if os.path.exists(ruta_archivo):
                            try:
                                os.remove(ruta_archivo)
                                print(f"[DEBUG] Imagen eliminada: {ruta_archivo}")
                            except Exception as e:
                                print(f"[WARN] No se pudo eliminar imagen: {e}")
                
                temas[clave]['imagen_url'] = None
                temas[clave]['tema'] = 'default'
                temas[clave]['fecha_actualizacion'] = datetime.now().isoformat()
                guardar_json(ARCHIVO_TEMAS_USUARIOS, temas)
            
            return jsonify({"ok": True})
        except Exception as e:
            print(f"[ERROR] api_eliminar_imagen_fondo: {e}")
            return jsonify({"ok": False, "error": str(e)})
    
    print("[INFO] Rutas de temas registradas en Flask")
    return app

# ==================== EJECUCIÓN DIRECTA ====================
if __name__ == '__main__':
    print("="*60)
    print("   MADRE.PY - Gestión de Temas por Usuario")
    print("="*60)
    
    inicializar_modulo_temas()
    
    temas = obtener_todos_temas_usuarios()
    if temas:
        print(f"\n[INFO] Temas guardados:")
        for usuario, data in temas.items():
            tema = data.get('tema', 'default')
            modulos = data.get('modulos', [])
            print(f"   - {usuario}: {tema} - {len(modulos)} módulos")
    else:
        print("\n[INFO] No hay temas guardados todavía")
    
    print("\n[INFO] Ruta del archivo de temas:")
    print(f"   {ARCHIVO_TEMAS_USUARIOS}")
    print("\n[INFO] Carpeta de imágenes de fondo:")
    print(f"   {CARPETA_IMAGENES_FONDO}")
    print("\n[INFO] Temas disponibles:")
    for key, value in TEMAS_DISPONIBLES.items():
        print(f"   - {key}: {value['nombre']} - {value['descripcion']}")
    print("\n[INFO] Campos guardados por usuario:")
    print("   - tema (default, dark, light, navy, nature, image)")
    print("   - imagen_url (URL de la imagen de fondo)")
    print("   - colores (18 colores personalizados)")
    print("   - logo (icono, color, título, subtítulo)")
    print("   - transparencia (fondo, tarjetas, bordes, blur)")
    print("   - modulos (lista de módulos seleccionados)")
    print("="*60)