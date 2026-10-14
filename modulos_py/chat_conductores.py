# ==================== MODULO CHAT CONDUCTORES ====================
import os
import json
import random
import shutil
from datetime import datetime, timedelta
from flask import jsonify, request, send_file
from werkzeug.utils import secure_filename
from io import BytesIO
from werkzeug.datastructures import FileStorage

# ==================== CONFIGURACIÓN ====================
ARCHIVO_CHAT = None
CARPETA_CHAT_ARCHIVOS = None
_cargar_json = None
_guardar_json = None
_registrar_bitacora = None

# Estructura en memoria
mensajes_por_conductor = {}  # {conductor_id: [mensajes]}
ubicacion_conductores = {}   # {conductor_id: {lat, lng, nombre, ultima_actualizacion}}
conductores_registrados = {}  # {conductor_id: {nombre, conectado, ultima_actividad, chat_id}}
chats_activos = {}           # {chat_id: {conductor_id, nombre, ultima_actividad}}

# Extensiones de archivo permitidas
EXTENSIONES_PERMITIDAS = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico'],
    'document': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.ods'],
    'spreadsheet': ['.csv', '.xls', '.xlsx'],
    'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac'],
    'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'],
    'code': ['.py', '.js', '.html', '.css', '.json', '.xml', '.sql', '.php', '.java', '.c', '.cpp']
}

TAMANO_MAXIMO_ARCHIVO = 50 * 1024 * 1024  # 50 MB

def inicializar_chat(main_funciones=None, rutas=None):
    global ARCHIVO_CHAT, CARPETA_CHAT_ARCHIVOS, _cargar_json, _guardar_json, _registrar_bitacora
    global mensajes_por_conductor, ubicacion_conductores, conductores_registrados, chats_activos
    
    if main_funciones:
        _cargar_json = main_funciones.get('cargar_json')
        _guardar_json = main_funciones.get('guardar_json')
        _registrar_bitacora = main_funciones.get('registrar_bitacora')
    
    if rutas:
        ARCHIVO_CHAT = rutas.get('chat')
        # Crear carpeta de archivos del chat
        data_path = os.path.dirname(ARCHIVO_CHAT) if ARCHIVO_CHAT else "./datos"
        CARPETA_CHAT_ARCHIVOS = os.path.join(data_path, "chat_archivos")
    
    # Crear carpeta de archivos si no existe
    if CARPETA_CHAT_ARCHIVOS and not os.path.exists(CARPETA_CHAT_ARCHIVOS):
        os.makedirs(CARPETA_CHAT_ARCHIVOS, exist_ok=True)
        print(f"[INFO] Carpeta de archivos del chat creada: {CARPETA_CHAT_ARCHIVOS}")
    
    # Crear archivo si no existe
    if ARCHIVO_CHAT and not os.path.exists(ARCHIVO_CHAT):
        guardar_datos_chat({
            "mensajes_por_conductor": {},
            "ubicaciones": {},
            "conductores": {},
            "chats_activos": {}
        })
    
    cargar_datos_chat()
    print(f"[INFO] Módulo Chat Conductores inicializado")
    print(f"[INFO] Archivo chat: {ARCHIVO_CHAT}")
    print(f"[INFO] Carpeta archivos: {CARPETA_CHAT_ARCHIVOS}")

def cargar_datos_chat():
    global mensajes_por_conductor, ubicacion_conductores, conductores_registrados, chats_activos
    
    if ARCHIVO_CHAT and os.path.exists(ARCHIVO_CHAT):
        try:
            with open(ARCHIVO_CHAT, 'r', encoding='utf-8') as f:
                data = json.load(f)
                mensajes_por_conductor = data.get('mensajes_por_conductor', {})
                ubicacion_conductores = data.get('ubicaciones', {})
                conductores_registrados = data.get('conductores', {})
                chats_activos = data.get('chats_activos', {})
                return
        except Exception as e:
            print(f"[ERROR] cargar_datos_chat: {e}")
    
    mensajes_por_conductor = {}
    ubicacion_conductores = {}
    conductores_registrados = {}
    chats_activos = {}

def guardar_datos_chat(data=None):
    if ARCHIVO_CHAT:
        try:
            if data is None:
                data = {
                    'mensajes_por_conductor': mensajes_por_conductor,
                    'ubicaciones': ubicacion_conductores,
                    'conductores': conductores_registrados,
                    'chats_activos': chats_activos,
                    'ultima_actualizacion': datetime.now().isoformat()
                }
            with open(ARCHIVO_CHAT, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERROR] guardar_datos_chat: {e}")
    return False

def obtener_carpeta_conductor(conductor_id):
    """Obtiene la carpeta de archivos para un conductor específico"""
    if not conductor_id or not CARPETA_CHAT_ARCHIVOS:
        return None
    
    carpeta = os.path.join(CARPETA_CHAT_ARCHIVOS, conductor_id)
    if not os.path.exists(carpeta):
        os.makedirs(carpeta, exist_ok=True)
    return carpeta

def obtener_tipo_archivo(filename):
    """Determina el tipo de archivo basado en su extensión"""
    ext = os.path.splitext(filename)[1].lower()
    for tipo, extensiones in EXTENSIONES_PERMITIDAS.items():
        if ext in extensiones:
            return tipo
    return 'desconocido'

def obtener_icono_archivo(filename):
    """Obtiene el ícono de FontAwesome para el tipo de archivo"""
    tipo = obtener_tipo_archivo(filename)
    iconos = {
        'image': 'fa-image',
        'document': 'fa-file-pdf',
        'spreadsheet': 'fa-file-excel',
        'archive': 'fa-file-archive',
        'audio': 'fa-file-audio',
        'video': 'fa-file-video',
        'code': 'fa-file-code',
        'desconocido': 'fa-file'
    }
    return iconos.get(tipo, 'fa-file')

def obtener_color_archivo(filename):
    """Obtiene el color para el tipo de archivo"""
    tipo = obtener_tipo_archivo(filename)
    colores = {
        'image': '#fbbf24',
        'document': '#f87171',
        'spreadsheet': '#34d399',
        'archive': '#60a5fa',
        'audio': '#a78bfa',
        'video': '#f472b6',
        'code': '#f59e0b',
        'desconocido': '#94a3b8'
    }
    return colores.get(tipo, '#94a3b8')

def detectar_tipo_archivo_por_bytes(raw_data):
    """Detecta el tipo de archivo por sus bytes iniciales"""
    if len(raw_data) < 4:
        return None, 'bin'
    
    # PNG: 89 50 4E 47
    if raw_data[:4] == b'\x89PNG':
        return '.png', 'image'
    # JPEG: FF D8 FF
    elif raw_data[:3] == b'\xff\xd8\xff':
        return '.jpg', 'image'
    # PDF: 25 50 44 46
    elif raw_data[:4] == b'%PDF':
        return '.pdf', 'document'
    # ZIP/Office: 50 4B 03 04
    elif raw_data[:4] == b'PK\x03\x04':
        return '.zip', 'archive'
    # GIF: 47 49 46 38
    elif raw_data[:4] == b'GIF8':
        return '.gif', 'image'
    # BMP: 42 4D
    elif raw_data[:2] == b'BM':
        return '.bmp', 'image'
    # WEBP: 52 49 46 46
    elif raw_data[:4] == b'RIFF':
        return '.webp', 'image'
    # MP3: 49 44 33
    elif raw_data[:3] == b'ID3':
        return '.mp3', 'audio'
    # MP4: 00 00 00 18 66 74 79 70
    elif raw_data[:8] == b'\x00\x00\x00\x18ftyp':
        return '.mp4', 'video'
    else:
        return None, 'desconocido'

# ==================== API ENDPOINTS ====================

def api_registrar_conductor():
    """Registra un conductor en el chat"""
    global conductores_registrados, chats_activos, ubicacion_conductores
    
    try:
        data = request.get_json()
        conductor_id = data.get('conductor_id')
        nombre = data.get('nombre', 'Conductor')
        ubicacion = data.get('ubicacion')
        chat_id = data.get('chat_id')
        
        if not conductor_id:
            return jsonify({"ok": False, "error": "conductor_id requerido"})
        
        # Crear carpeta para el conductor
        obtener_carpeta_conductor(conductor_id)
        
        # Registrar conductor
        conductores_registrados[conductor_id] = {
            'id': conductor_id,
            'nombre': nombre,
            'conectado': True,
            'chat_id': chat_id,
            'ultima_actividad': datetime.now().isoformat(),
            'fecha_registro': datetime.now().isoformat()
        }
        
        if chat_id:
            chats_activos[chat_id] = {
                'conductor_id': conductor_id,
                'nombre': nombre,
                'ultima_actividad': datetime.now().isoformat()
            }
        
        if ubicacion and 'lat' in ubicacion and 'lng' in ubicacion:
            ubicacion_conductores[conductor_id] = {
                'nombre': nombre,
                'lat': ubicacion.get('lat'),
                'lng': ubicacion.get('lng'),
                'ultima_actualizacion': datetime.now().isoformat()
            }
        
        guardar_datos_chat()
        
        if _registrar_bitacora:
            _registrar_bitacora(
                nombre,
                "Registrar Conductor Chat",
                f"Conductor ID: {conductor_id}",
                "Chat"
            )
        
        return jsonify({"ok": True, "mensaje": "Conductor registrado"})
    except Exception as e:
        print(f"[ERROR] api_registrar_conductor: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_enviar_mensaje_conductor():
    """Envía un mensaje al chat de un conductor específico (con soporte de archivos)"""
    global mensajes_por_conductor, chats_activos, ubicacion_conductores
    
    try:
        # ===== DETECCIÓN INTELIGENTE: VERIFICAR SI HAY ARCHIVOS =====
        raw_data = request.get_data()
        tiene_archivo = False
        
        # Verificar si hay archivos en request.files
        if request.files:
            for key in request.files:
                if request.files[key] and request.files[key].filename:
                    tiene_archivo = True
                    break
        
        # Si no hay archivos en request.files, verificar si el body parece binario
        if not tiene_archivo and raw_data and len(raw_data) > 0:
            # Detectar por bytes iniciales
            ext, tipo = detectar_tipo_archivo_por_bytes(raw_data)
            if ext:
                tiene_archivo = True
                print(f"[DEBUG] Detectado archivo tipo: {tipo} con extensión {ext}")
        
        # Obtener Content-Type
        content_type = request.headers.get('Content-Type', '').lower()
        is_multipart = 'multipart/form-data' in content_type
        
        print(f"[DEBUG] ===== NUEVA SOLICITUD =====")
        print(f"[DEBUG] Content-Type: {content_type}")
        print(f"[DEBUG] is_multipart: {is_multipart}")
        print(f"[DEBUG] tiene_archivo: {tiene_archivo}")
        print(f"[DEBUG] Files keys: {list(request.files.keys()) if request.files else 'None'}")
        print(f"[DEBUG] Form keys: {list(request.form.keys()) if request.form else 'None'}")
        print(f"[DEBUG] Raw data length: {len(raw_data) if raw_data else 0}")
        
        # ===== PROCESAR COMO MULTIPART SI TIENE ARCHIVO =====
        if tiene_archivo or is_multipart:
            print("[DEBUG] Procesando como multipart/form-data")
            
            # Obtener datos del formulario
            conductor_id = request.form.get('conductor_id')
            remitente = request.form.get('remitente', 'Conductor')
            mensaje = request.form.get('mensaje', '')
            fecha = request.form.get('fecha', datetime.now().isoformat())
            
            # Si no vienen en form, intentar obtener del JSON (caso de fallback)
            if not conductor_id:
                try:
                    if raw_data:
                        # Intentar parsear como JSON solo si parece texto
                        try:
                            data = json.loads(raw_data.decode('utf-8'))
                            if data:
                                conductor_id = data.get('conductor_id')
                                remitente = data.get('remitente', 'Conductor')
                                mensaje = data.get('mensaje', '')
                                fecha = data.get('fecha', datetime.now().isoformat())
                                # Si hay archivo en base64 en el JSON
                                archivo_base64 = data.get('archivo_base64')
                                if archivo_base64 and not tiene_archivo:
                                    import base64
                                    try:
                                        datos_binarios = base64.b64decode(archivo_base64)
                                        ext, tipo = detectar_tipo_archivo_por_bytes(datos_binarios)
                                        if ext:
                                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                                            nombre_original = f"archivo_{timestamp}{ext}"
                                            file_obj = FileStorage(
                                                stream=BytesIO(datos_binarios),
                                                filename=nombre_original,
                                                content_type='application/octet-stream'
                                            )
                                            request.files = request.files or {}
                                            request.files['archivo'] = file_obj
                                            tiene_archivo = True
                                            print(f"[DEBUG] Archivo base64 procesado: {nombre_original}")
                                    except Exception as e:
                                        print(f"[ERROR] Procesando base64: {e}")
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            pass
                except:
                    pass
            
            if not conductor_id:
                return jsonify({"ok": False, "error": "conductor_id requerido"})
            
            # Obtener archivos
            archivos_validos = []
            
            # Primero de request.files
            for f in request.files.getlist('archivo'):
                if f and f.filename and f.filename != '':
                    archivos_validos.append(f)
            
            # Si hay archivos en request.files pero con otro nombre
            if not archivos_validos and request.files:
                for key in request.files:
                    f = request.files[key]
                    if f and f.filename and f.filename != '':
                        archivos_validos.append(f)
                        break
            
            # Si no hay archivos en request.files pero el body es binario, crear uno
            if not archivos_validos and tiene_archivo and raw_data and len(raw_data) > 0:
                try:
                    ext, tipo = detectar_tipo_archivo_por_bytes(raw_data)
                    if not ext:
                        ext = '.bin'
                    
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                    nombre_original = f"archivo_{timestamp}{ext}"
                    
                    file_obj = FileStorage(
                        stream=BytesIO(raw_data),
                        filename=nombre_original,
                        content_type='application/octet-stream'
                    )
                    archivos_validos.append(file_obj)
                    print(f"[DEBUG] Archivo creado desde body: {nombre_original}")
                except Exception as e:
                    print(f"[ERROR] Creando archivo desde body: {e}")
            
            if not archivos_validos:
                return jsonify({"ok": False, "error": "No se encontraron archivos válidos"})
            
            # ===== PROCESAR ARCHIVOS =====
            archivos_procesados = []
            for archivo in archivos_validos:
                try:
                    # Validar tamaño
                    archivo.seek(0, os.SEEK_END)
                    tamanio = archivo.tell()
                    archivo.seek(0)
                    
                    print(f"[DEBUG] Archivo: {archivo.filename}, Tamaño: {tamanio} bytes")
                    
                    if tamanio > TAMANO_MAXIMO_ARCHIVO:
                        return jsonify({"ok": False, "error": f"El archivo {archivo.filename} excede el tamaño máximo de {TAMANO_MAXIMO_ARCHIVO // (1024*1024)} MB"})
                    
                    # Guardar archivo en la carpeta del conductor
                    carpeta_conductor = obtener_carpeta_conductor(conductor_id)
                    if not carpeta_conductor:
                        return jsonify({"ok": False, "error": "No se pudo crear la carpeta del conductor"})
                    
                    nombre_original = secure_filename(archivo.filename)
                    if not nombre_original:
                        nombre_original = f"archivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                    nombre_guardado = f"{timestamp}_{nombre_original}"
                    ruta_archivo = os.path.join(carpeta_conductor, nombre_guardado)
                    
                    archivo.save(ruta_archivo)
                    print(f"[DEBUG] Archivo guardado: {ruta_archivo}")
                    
                    archivos_procesados.append({
                        'nombre': nombre_original,
                        'nombre_guardado': nombre_guardado,
                        'tamanio': tamanio,
                        'tipo': obtener_tipo_archivo(nombre_original),
                        'ruta': ruta_archivo,
                        'icono': obtener_icono_archivo(nombre_original),
                        'color': obtener_color_archivo(nombre_original)
                    })
                except Exception as e:
                    print(f"[ERROR] Procesando archivo: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            if not archivos_procesados:
                return jsonify({"ok": False, "error": "No se pudieron procesar los archivos"})
            
            # Crear mensaje con archivos
            msg_id = f"msg_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(100, 999)}"
            
            nuevo_mensaje = {
                'id': msg_id,
                'conductor_id': conductor_id,
                'remitente': remitente,
                'mensaje': mensaje if mensaje else '',
                'fecha': fecha,
                'fecha_iso': datetime.now().isoformat(),
                'archivo': archivos_procesados[0] if archivos_procesados else None
            }
            
            # Guardar mensaje
            if conductor_id not in mensajes_por_conductor:
                mensajes_por_conductor[conductor_id] = []
            mensajes_por_conductor[conductor_id].append(nuevo_mensaje)
            
            # Mantener solo los últimos 500 mensajes por conductor
            if len(mensajes_por_conductor[conductor_id]) > 500:
                mensajes_por_conductor[conductor_id] = mensajes_por_conductor[conductor_id][-500:]
            
            if conductor_id in conductores_registrados:
                conductores_registrados[conductor_id]['ultima_actividad'] = datetime.now().isoformat()
            
            guardar_datos_chat()
            
            if _registrar_bitacora:
                _registrar_bitacora(
                    remitente,
                    "Enviar Mensaje Chat Conductor",
                    f"Conductor: {conductor_id} - Archivo: {archivos_procesados[0]['nombre']} - Tamaño: {archivos_procesados[0]['tamanio']} bytes",
                    "Chat"
                )
            
            return jsonify({"ok": True, "mensaje": "Mensaje enviado", "msg_id": msg_id})
        
        # ===== PROCESAR JSON NORMAL (solo texto) =====
        else:
            print("[DEBUG] Procesando como JSON (solo texto)")
            
            try:
                data = request.get_json()
                if data is None:
                    return jsonify({"ok": False, "error": "Content-Type debe ser application/json para mensajes de texto"})
            except Exception as e:
                return jsonify({"ok": False, "error": f"Error parsing JSON: {str(e)}"})
            
            conductor_id = data.get('conductor_id')
            remitente = data.get('remitente', 'Conductor')
            mensaje = data.get('mensaje')
            ubicacion = data.get('ubicacion')
            fecha = data.get('fecha', datetime.now().isoformat())
            
            if not conductor_id:
                return jsonify({"ok": False, "error": "conductor_id requerido"})
            
            if not mensaje:
                return jsonify({"ok": False, "error": "mensaje requerido"})
            
            msg_id = f"msg_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(100, 999)}"
            
            nuevo_mensaje = {
                'id': msg_id,
                'conductor_id': conductor_id,
                'remitente': remitente,
                'mensaje': mensaje,
                'ubicacion': ubicacion,
                'fecha': fecha,
                'fecha_iso': datetime.now().isoformat()
            }
            
            # Guardar mensaje
            if conductor_id not in mensajes_por_conductor:
                mensajes_por_conductor[conductor_id] = []
            mensajes_por_conductor[conductor_id].append(nuevo_mensaje)
            
            # Mantener solo los últimos 500 mensajes por conductor
            if len(mensajes_por_conductor[conductor_id]) > 500:
                mensajes_por_conductor[conductor_id] = mensajes_por_conductor[conductor_id][-500:]
            
            # Actualizar ubicación si se incluye
            if ubicacion and 'lat' in ubicacion and 'lng' in ubicacion:
                ubicacion_conductores[conductor_id] = {
                    'nombre': remitente,
                    'lat': ubicacion.get('lat'),
                    'lng': ubicacion.get('lng'),
                    'ultima_actualizacion': datetime.now().isoformat()
                }
            
            if conductor_id in conductores_registrados:
                conductores_registrados[conductor_id]['ultima_actividad'] = datetime.now().isoformat()
            
            guardar_datos_chat()
            
            if _registrar_bitacora:
                _registrar_bitacora(
                    remitente,
                    "Enviar Mensaje Chat Conductor",
                    f"Conductor: {conductor_id} - {mensaje[:50] + '...' if len(mensaje) > 50 else mensaje}",
                    "Chat"
                )
            
            return jsonify({"ok": True, "mensaje": "Mensaje enviado", "msg_id": msg_id})
            
    except Exception as e:
        print(f"[ERROR] api_enviar_mensaje_conductor: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})

def api_obtener_mensajes_conductor():
    """Obtiene mensajes de un conductor específico"""
    global mensajes_por_conductor
    
    try:
        conductor_id = request.args.get('conductor_id')
        limite = int(request.args.get('limite', 100))
        
        if not conductor_id:
            return jsonify({"ok": False, "error": "conductor_id requerido", "mensajes": []})
        
        mensajes = mensajes_por_conductor.get(conductor_id, [])
        mensajes.sort(key=lambda x: x.get('fecha', ''), reverse=True)
        mensajes = mensajes[:limite]
        
        return jsonify({
            "ok": True,
            "mensajes": mensajes,
            "conductor_id": conductor_id,
            "total": len(mensajes)
        })
    except Exception as e:
        print(f"[ERROR] api_obtener_mensajes_conductor: {e}")
        return jsonify({"ok": False, "error": str(e), "mensajes": []})

def api_descargar_archivo():
    """Descarga un archivo enviado en el chat"""
    try:
        conductor_id = request.args.get('conductor_id')
        nombre_guardado = request.args.get('nombre_guardado')
        
        if not conductor_id or not nombre_guardado:
            return jsonify({"ok": False, "error": "Faltan parámetros"})
        
        carpeta_conductor = obtener_carpeta_conductor(conductor_id)
        if not carpeta_conductor:
            return jsonify({"ok": False, "error": "Carpeta del conductor no encontrada"})
        
        ruta_archivo = os.path.join(carpeta_conductor, nombre_guardado)
        if not os.path.exists(ruta_archivo):
            return jsonify({"ok": False, "error": "Archivo no encontrado"})
        
        # Buscar el nombre original en los mensajes
        mensajes = mensajes_por_conductor.get(conductor_id, [])
        nombre_original = nombre_guardado
        for msg in mensajes:
            if msg.get('archivo', {}).get('nombre_guardado') == nombre_guardado:
                nombre_original = msg.get('archivo', {}).get('nombre', nombre_guardado)
                break
        
        return send_file(
            ruta_archivo,
            as_attachment=True,
            download_name=nombre_original
        )
    except Exception as e:
        print(f"[ERROR] api_descargar_archivo: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_actualizar_ubicacion_conductor():
    """Actualiza la ubicación de un conductor"""
    global ubicacion_conductores, conductores_registrados
    
    try:
        data = request.get_json()
        conductor_id = data.get('conductor_id')
        lat = data.get('lat')
        lng = data.get('lng')
        
        if not conductor_id:
            return jsonify({"ok": False, "error": "conductor_id requerido"})
        
        if lat is None or lng is None:
            return jsonify({"ok": False, "error": "lat y lng requeridos"})
        
        nombre = 'Conductor'
        if conductor_id in conductores_registrados:
            nombre = conductores_registrados[conductor_id].get('nombre', 'Conductor')
        
        ubicacion_conductores[conductor_id] = {
            'nombre': nombre,
            'lat': lat,
            'lng': lng,
            'ultima_actualizacion': datetime.now().isoformat()
        }
        
        if conductor_id in conductores_registrados:
            conductores_registrados[conductor_id]['ultima_actividad'] = datetime.now().isoformat()
        
        guardar_datos_chat()
        return jsonify({"ok": True, "mensaje": "Ubicación actualizada"})
    except Exception as e:
        print(f"[ERROR] api_actualizar_ubicacion_conductor: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_obtener_conductores_conectados():
    """Obtiene lista de conductores conectados con sus ubicaciones"""
    global conductores_registrados, ubicacion_conductores, mensajes_por_conductor
    
    try:
        # Limpiar conductores inactivos (más de 2 minutos sin actividad)
        limite_tiempo = datetime.now() - timedelta(minutes=2)
        conductores_activos = {}
        
        for conductor_id, info in conductores_registrados.items():
            ultima_act = info.get('ultima_actividad')
            if ultima_act:
                try:
                    fecha_ultima = datetime.fromisoformat(ultima_act)
                    if fecha_ultima > limite_tiempo:
                        conductores_activos[conductor_id] = info
                except:
                    conductores_activos[conductor_id] = info
        
        # Actualizar estado en memoria
        for cid in conductores_registrados:
            conductores_registrados[cid]['conectado'] = cid in conductores_activos
        
        conductores_lista = []
        for conductor_id, info in conductores_activos.items():
            ubicacion = ubicacion_conductores.get(conductor_id)
            mensajes_count = len(mensajes_por_conductor.get(conductor_id, []))
            
            conductores_lista.append({
                'id': conductor_id,
                'nombre': info.get('nombre', 'Conductor'),
                'ubicacion': ubicacion,
                'ultima_actividad': info.get('ultima_actividad'),
                'mensajes_count': mensajes_count,
                'conectado': True
            })
        
        # Ordenar por nombre
        conductores_lista.sort(key=lambda x: x.get('nombre', ''))
        
        guardar_datos_chat()
        return jsonify({"ok": True, "conductores": conductores_lista, "total": len(conductores_lista)})
    except Exception as e:
        print(f"[ERROR] api_obtener_conductores_conectados: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e), "conductores": []})

def api_obtener_conductores_con_mensajes():
    """Obtiene lista de conductores que tienen mensajes"""
    global mensajes_por_conductor, conductores_registrados
    
    try:
        conductores = []
        for conductor_id, mensajes in mensajes_por_conductor.items():
            if mensajes:
                info = conductores_registrados.get(conductor_id, {})
                conductores.append({
                    'id': conductor_id,
                    'nombre': info.get('nombre', 'Conductor'),
                    'mensajes_count': len(mensajes),
                    'ultimo_mensaje': mensajes[-1].get('fecha') if mensajes else None,
                    'conectado': info.get('conectado', False)
                })
        
        conductores.sort(key=lambda x: x.get('ultimo_mensaje', ''), reverse=True)
        return jsonify({"ok": True, "conductores": conductores, "total": len(conductores)})
    except Exception as e:
        print(f"[ERROR] api_obtener_conductores_con_mensajes: {e}")
        return jsonify({"ok": False, "error": str(e), "conductores": []})

def api_limpiar_mensajes_conductor():
    """Elimina permanentemente todos los mensajes de un conductor y sus archivos"""
    global mensajes_por_conductor
    
    try:
        data = request.get_json()
        conductor_id = data.get('conductor_id')
        
        if not conductor_id:
            return jsonify({"ok": False, "error": "conductor_id requerido"})
        
        # Eliminar mensajes del conductor
        if conductor_id in mensajes_por_conductor:
            eliminados = len(mensajes_por_conductor[conductor_id])
            mensajes_por_conductor[conductor_id] = []
            
            # Eliminar archivos del conductor
            carpeta_conductor = obtener_carpeta_conductor(conductor_id)
            if carpeta_conductor and os.path.exists(carpeta_conductor):
                try:
                    shutil.rmtree(carpeta_conductor)
                    os.makedirs(carpeta_conductor, exist_ok=True)
                except Exception as e:
                    print(f"[WARN] Error eliminando carpeta del conductor {conductor_id}: {e}")
            
            guardar_datos_chat()
            
            if _registrar_bitacora:
                _registrar_bitacora(
                    data.get('usuario', 'sistema'),
                    "Limpiar Mensajes Conductor",
                    f"Conductor: {conductor_id} - {eliminados} mensajes eliminados",
                    "Chat"
                )
            
            return jsonify({
                "ok": True,
                "mensaje": f"Se eliminaron {eliminados} mensajes",
                "eliminados": eliminados
            })
        
        return jsonify({"ok": False, "error": "Conductor no encontrado"})
    except Exception as e:
        print(f"[ERROR] api_limpiar_mensajes_conductor: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_limpiar_todos_mensajes():
    """Elimina permanentemente TODOS los mensajes de TODOS los conductores y sus archivos"""
    global mensajes_por_conductor
    
    try:
        data = request.get_json()
        confirmar = data.get('confirmar', False)
        
        if not confirmar:
            return jsonify({"ok": False, "error": "Se requiere confirmación"})
        
        total = sum(len(m) for m in mensajes_por_conductor.values())
        mensajes_por_conductor = {}
        
        # Eliminar todos los archivos del chat
        if CARPETA_CHAT_ARCHIVOS and os.path.exists(CARPETA_CHAT_ARCHIVOS):
            try:
                for item in os.listdir(CARPETA_CHAT_ARCHIVOS):
                    ruta = os.path.join(CARPETA_CHAT_ARCHIVOS, item)
                    if os.path.isdir(ruta):
                        shutil.rmtree(ruta)
                print(f"[INFO] Todos los archivos del chat eliminados")
            except Exception as e:
                print(f"[WARN] Error eliminando archivos del chat: {e}")
        
        guardar_datos_chat()
        
        if _registrar_bitacora:
            _registrar_bitacora(
                data.get('usuario', 'sistema'),
                "Limpiar Todos Mensajes Chat",
                f"{total} mensajes eliminados permanentemente",
                "Chat"
            )
        
        return jsonify({
            "ok": True,
            "mensaje": f"Se eliminaron {total} mensajes de todos los conductores",
            "eliminados": total
        })
    except Exception as e:
        print(f"[ERROR] api_limpiar_todos_mensajes: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_eliminar_mensaje():
    """Elimina un mensaje específico por ID y su archivo asociado"""
    global mensajes_por_conductor
    
    try:
        data = request.get_json()
        msg_id = data.get('msg_id')
        conductor_id = data.get('conductor_id')
        
        if not msg_id:
            return jsonify({"ok": False, "error": "msg_id requerido"})
        
        eliminado = False
        archivo_eliminado = False
        
        if conductor_id and conductor_id in mensajes_por_conductor:
            # Buscar el mensaje y eliminar archivo si existe
            for msg in mensajes_por_conductor[conductor_id]:
                if msg.get('id') == msg_id and msg.get('archivo'):
                    nombre_guardado = msg.get('archivo', {}).get('nombre_guardado')
                    if nombre_guardado:
                        carpeta = obtener_carpeta_conductor(conductor_id)
                        if carpeta:
                            ruta = os.path.join(carpeta, nombre_guardado)
                            if os.path.exists(ruta):
                                try:
                                    os.remove(ruta)
                                    archivo_eliminado = True
                                except:
                                    pass
            
            original_len = len(mensajes_por_conductor[conductor_id])
            mensajes_por_conductor[conductor_id] = [m for m in mensajes_por_conductor[conductor_id] if m.get('id') != msg_id]
            if len(mensajes_por_conductor[conductor_id]) < original_len:
                eliminado = True
        else:
            # Buscar en todos los conductores
            for cid in list(mensajes_por_conductor.keys()):
                # Buscar y eliminar archivo
                for msg in mensajes_por_conductor[cid]:
                    if msg.get('id') == msg_id and msg.get('archivo'):
                        nombre_guardado = msg.get('archivo', {}).get('nombre_guardado')
                        if nombre_guardado:
                            carpeta = obtener_carpeta_conductor(cid)
                            if carpeta:
                                ruta = os.path.join(carpeta, nombre_guardado)
                                if os.path.exists(ruta):
                                    try:
                                        os.remove(ruta)
                                        archivo_eliminado = True
                                    except:
                                        pass
                
                original_len = len(mensajes_por_conductor[cid])
                mensajes_por_conductor[cid] = [m for m in mensajes_por_conductor[cid] if m.get('id') != msg_id]
                if len(mensajes_por_conductor[cid]) < original_len:
                    eliminado = True
                    conductor_id = cid
                    break
        
        if eliminado:
            guardar_datos_chat()
            if _registrar_bitacora:
                _registrar_bitacora(
                    data.get('usuario', 'sistema'),
                    "Eliminar Mensaje Chat",
                    f"Msg ID: {msg_id} - Conductor: {conductor_id} - Archivo: {'Eliminado' if archivo_eliminado else 'No'}",
                    "Chat"
                )
            return jsonify({"ok": True, "mensaje": "Mensaje eliminado", "archivo_eliminado": archivo_eliminado})
        
        return jsonify({"ok": False, "error": "Mensaje no encontrado"})
    except Exception as e:
        print(f"[ERROR] api_eliminar_mensaje: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_obtener_todos_mensajes():
    """Obtiene todos los mensajes de todos los conductores (para admin)"""
    global mensajes_por_conductor
    
    try:
        limite = int(request.args.get('limite', 100))
        todos = []
        for conductor_id, mensajes in mensajes_por_conductor.items():
            for m in mensajes:
                m_copy = m.copy()
                m_copy['conductor_id'] = conductor_id
                todos.append(m_copy)
        
        todos.sort(key=lambda x: x.get('fecha', ''), reverse=True)
        todos = todos[:limite]
        
        return jsonify({"ok": True, "mensajes": todos, "total": len(todos)})
    except Exception as e:
        print(f"[ERROR] api_obtener_todos_mensajes: {e}")
        return jsonify({"ok": False, "error": str(e), "mensajes": []})

# ==================== FUNCIONES LEGACY (COMPATIBILIDAD) ====================

def api_registrar_chat():
    """Registra un chat (legacy)"""
    try:
        data = request.get_json()
        conductor_id = data.get('id_conductor') or data.get('conductor_id') or data.get('chat_id')
        nombre = data.get('nombre', 'Conductor')
        ubicacion = data.get('ubicacion')
        chat_id = data.get('chat_id', f"chat_{conductor_id}")
        
        if not conductor_id:
            return jsonify({"ok": False, "error": "conductor_id requerido"})
        
        # Registrar conductor directamente
        global conductores_registrados, chats_activos, ubicacion_conductores
        
        # Crear carpeta para el conductor
        obtener_carpeta_conductor(conductor_id)
        
        conductores_registrados[conductor_id] = {
            'id': conductor_id,
            'nombre': nombre,
            'conectado': True,
            'chat_id': chat_id,
            'ultima_actividad': datetime.now().isoformat(),
            'fecha_registro': datetime.now().isoformat()
        }
        
        if chat_id:
            chats_activos[chat_id] = {
                'conductor_id': conductor_id,
                'nombre': nombre,
                'ultima_actividad': datetime.now().isoformat()
            }
        
        if ubicacion and 'lat' in ubicacion and 'lng' in ubicacion:
            ubicacion_conductores[conductor_id] = {
                'nombre': nombre,
                'lat': ubicacion.get('lat'),
                'lng': ubicacion.get('lng'),
                'ultima_actualizacion': datetime.now().isoformat()
            }
        
        guardar_datos_chat()
        
        if _registrar_bitacora:
            _registrar_bitacora(
                nombre,
                "Registrar Conductor Chat",
                f"Conductor ID: {conductor_id}",
                "Chat"
            )
        
        return jsonify({"ok": True, "mensaje": "Conductor registrado", "conductor_id": conductor_id})
    except Exception as e:
        print(f"[ERROR] api_registrar_chat: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_enviar_mensaje():
    """Envía un mensaje (legacy) - redirige a la función principal"""
    try:
        return api_enviar_mensaje_conductor()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_obtener_mensajes():
    """Obtiene mensajes (legacy)"""
    try:
        conductor_id = request.args.get('conductor_id') or request.args.get('chat_id')
        return api_obtener_mensajes_conductor()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "mensajes": []})

def api_actualizar_ubicacion():
    """Actualiza ubicación (legacy)"""
    try:
        data = request.get_json()
        conductor_id = data.get('conductor_id') or data.get('chat_id')
        lat = data.get('lat')
        lng = data.get('lng')
        return api_actualizar_ubicacion_conductor()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_obtener_chats_activos():
    """Obtiene chats activos (legacy)"""
    return api_obtener_conductores_conectados()

def api_obtener_mensajes_globales():
    """Obtiene mensajes globales (legacy)"""
    return api_obtener_todos_mensajes()

def api_obtener_ubicacion_conductores():
    """Obtiene ubicación de conductores (legacy)"""
    return api_obtener_conductores_conectados()