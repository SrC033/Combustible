# ==================== API.PY - TODOS LOS ENDPOINTS ====================
import os
import json
import hashlib
import random
from datetime import datetime
from flask import jsonify, request

# Variables globales para archivos (se inicializan desde main)
ARCHIVO_EMPRESAS = None
ARCHIVO_PEDIDOS = None
ARCHIVO_PEDIDOS_FACTURACION = None
ARCHIVO_FACTURAS = None
ARCHIVO_CONDUCTORES = None
ARCHIVO_CAMIONES = None
ARCHIVO_COSTOS_TRASLADO = None
ARCHIVO_USUARIOS = None
ARCHIVO_BITACORA = None
ARCHIVO_TABLAS_EDITABLES = None
ARCHIVO_MANTENIMIENTO = None
ARCHIVO_PAGINAS = None
ARCHIVO_URL_PUBLICA = None
ARCHIVO_OPERACIONES = None
ARCHIVO_CONFIG_FACTURA = None

_cargar_json = None
_guardar_json = None

def configurar_api(cargar_json_func, guardar_json_func, archivos):
    """Configura el módulo API con las funciones y archivos"""
    global _cargar_json, _guardar_json
    global ARCHIVO_EMPRESAS, ARCHIVO_PEDIDOS, ARCHIVO_PEDIDOS_FACTURACION
    global ARCHIVO_FACTURAS, ARCHIVO_CONDUCTORES, ARCHIVO_CAMIONES
    global ARCHIVO_COSTOS_TRASLADO, ARCHIVO_USUARIOS, ARCHIVO_BITACORA
    global ARCHIVO_TABLAS_EDITABLES, ARCHIVO_MANTENIMIENTO, ARCHIVO_PAGINAS
    global ARCHIVO_URL_PUBLICA, ARCHIVO_OPERACIONES, ARCHIVO_CONFIG_FACTURA
    
    _cargar_json = cargar_json_func
    _guardar_json = guardar_json_func
    
    ARCHIVO_EMPRESAS = archivos.get('empresas')
    ARCHIVO_PEDIDOS = archivos.get('pedidos')
    ARCHIVO_PEDIDOS_FACTURACION = archivos.get('pedidos_facturacion')
    ARCHIVO_FACTURAS = archivos.get('facturas')
    ARCHIVO_CONDUCTORES = archivos.get('conductores')
    ARCHIVO_CAMIONES = archivos.get('camiones')
    ARCHIVO_COSTOS_TRASLADO = archivos.get('costos_traslado')
    ARCHIVO_USUARIOS = archivos.get('usuarios')
    ARCHIVO_BITACORA = archivos.get('bitacora')
    ARCHIVO_TABLAS_EDITABLES = archivos.get('tablas_editables')
    ARCHIVO_MANTENIMIENTO = archivos.get('mantenimiento')
    ARCHIVO_PAGINAS = archivos.get('paginas')
    ARCHIVO_URL_PUBLICA = archivos.get('url_publica')
    ARCHIVO_OPERACIONES = archivos.get('operaciones')
    ARCHIVO_CONFIG_FACTURA = archivos.get('config_factura')
    
    print("[INFO] ✅ API configurada correctamente")

def cargar_json(ruta, default=None):
    if _cargar_json:
        return _cargar_json(ruta, default)
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
    if _guardar_json:
        return _guardar_json(ruta, data)
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

# ==================== API - EMPRESAS ====================
def api_empresas():
    data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
    return jsonify({"empresas": data.get("empresas", [])})

def api_empresas_activas():
    data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
    empresas = [e for e in data.get("empresas", []) if e.get("activo", True)]
    return jsonify({"empresas": empresas})

def api_crear_empresa():
    try:
        data = request.get_json()
        empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": [], "ultimo_id": 0})
        ultimo_id = empresas_data.get("ultimo_id", 0)
        nuevo_id = f"CLI-{str(ultimo_id+1).zfill(3)}"
        
        nueva_empresa = {
            "id": data.get("id") or nuevo_id,
            "nombre": data.get("nombre", ""),
            "contacto": data.get("contacto", ""),
            "cedula": data.get("cedula", ""),
            "telefono": data.get("telefono", ""),
            "email": data.get("email", ""),
            "direccion": data.get("direccion", ""),
            "destino": data.get("destino", ""),
            "conductor": data.get("conductor", ""),
            "tipo": data.get("tipo", "Cliente"),
            "placa": data.get("placa", ""),
            "fecha_registro": datetime.now().isoformat(),
            "pedidos": 0,
            "activo": True,
            "credito": data.get("credito", 0),
            "limite_credito": data.get("limite_credito", 0)
        }
        empresas_data["empresas"].append(nueva_empresa)
        empresas_data["ultimo_id"] = ultimo_id + 1
        guardar_json(ARCHIVO_EMPRESAS, empresas_data)
        return jsonify({"ok": True, "empresa": nueva_empresa})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_eliminar_empresa():
    try:
        data = request.get_json()
        empresa_id = data.get("id")
        empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
        empresas_data["empresas"] = [e for e in empresas_data.get("empresas", []) if e.get("id") != empresa_id]
        guardar_json(ARCHIVO_EMPRESAS, empresas_data)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_actualizar_empresa():
    try:
        data = request.get_json()
        empresa_id = data.get("id")
        nuevos_datos = data.get("datos", {})
        empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
        for e in empresas_data.get("empresas", []):
            if e.get("id") == empresa_id:
                for k, v in nuevos_datos.items():
                    e[k] = v
                guardar_json(ARCHIVO_EMPRESAS, empresas_data)
                return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Empresa no encontrada"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_actualizar_credito():
    try:
        data = request.get_json()
        empresa_id = data.get("empresa_id")
        monto = data.get("monto", 0)
        es_abono = data.get("es_abono", False)
        
        empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
        for e in empresas_data.get("empresas", []):
            if e.get("id") == empresa_id:
                if es_abono:
                    e["credito"] = max(0, e.get("credito", 0) - monto)
                else:
                    e["credito"] = e.get("credito", 0) + monto
                e["pedidos"] = e.get("pedidos", 0) + 1
                guardar_json(ARCHIVO_EMPRESAS, empresas_data)
                return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Empresa no encontrada"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_estado_credito(empresa_id):
    try:
        empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
        for e in empresas_data.get("empresas", []):
            if e.get("id") == empresa_id:
                credito = e.get("credito", 0)
                limite = e.get("limite_credito", 0)
                disponible = max(0, limite - credito)
                estado = "bloqueado" if credito >= limite and limite > 0 else "disponible"
                return jsonify({
                    "ok": True,
                    "estado": {
                        "credito": credito,
                        "limite": limite,
                        "disponible": disponible,
                        "estado": estado
                    }
                })
        return jsonify({"ok": False, "error": "Empresa no encontrada"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_extender_limite():
    try:
        data = request.get_json()
        empresa_id = data.get("empresa_id")
        nuevo_limite = data.get("nuevo_limite", 0)
        
        empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
        for e in empresas_data.get("empresas", []):
            if e.get("id") == empresa_id:
                e["limite_credito"] = nuevo_limite
                guardar_json(ARCHIVO_EMPRESAS, empresas_data)
                return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Empresa no encontrada"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_validar():
    try:
        data = request.get_json()
        empresa_id = data.get("id")
        empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
        for e in empresas_data.get("empresas", []):
            if e.get("id") == empresa_id or e.get("nombre") == empresa_id:
                return jsonify({
                    "valido": True,
                    "nombre": e.get("nombre", ""),
                    "ruc": e.get("cedula", ""),
                    "telefono": e.get("telefono", ""),
                    "email": e.get("email", ""),
                    "direccion": e.get("direccion", ""),
                    "placa": e.get("placa", ""),
                    "destino": e.get("destino", ""),
                    "contacto": e.get("contacto", ""),
                    "conductor": e.get("conductor", ""),
                    "credito": e.get("credito", 0),
                    "limite_credito": e.get("limite_credito", 0)
                })
        return jsonify({"valido": False})
    except Exception as e:
        return jsonify({"valido": False, "error": str(e)})

def api_alertas_credito():
    try:
        empresas_data = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
        alertas = []
        for e in empresas_data.get("empresas", []):
            credito = e.get("credito", 0)
            limite = e.get("limite_credito", 0)
            if limite > 0 and credito >= limite:
                alertas.append({
                    "id": e.get("id"),
                    "nombre": e.get("nombre"),
                    "credito": credito,
                    "limite": limite
                })
        return jsonify({"alertas": alertas})
    except Exception as e:
        return jsonify({"alertas": []})

# ==================== API - USUARIOS ====================
def api_login():
    try:
        data = request.get_json()
        email = data.get('email', '')
        password = data.get('password', '')
        
        print(f"[DEBUG] Intento de login: {email}")
        
        # Cargar usuarios directamente
        if os.path.exists(ARCHIVO_USUARIOS):
            try:
                with open(ARCHIVO_USUARIOS, 'r', encoding='utf-8') as f:
                    usuarios = json.load(f)
            except Exception as e:
                print(f"[ERROR] Leyendo usuarios.json: {e}")
                usuarios = {"usuarios": []}
        else:
            # Crear usuario por defecto
            admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
            usuarios = {
                "usuarios": [
                    {
                        "id": "USR-001",
                        "nombre": "Administrador",
                        "email": "admin@gruposn.com",
                        "rol": "admin",
                        "password": admin_hash,
                        "estado": "activo"
                    }
                ],
                "ultimo_id": 1
            }
            guardar_json(ARCHIVO_USUARIOS, usuarios)
        
        print(f"[DEBUG] Usuarios cargados: {len(usuarios.get('usuarios', []))}")
        
        # Buscar usuario
        for u in usuarios.get("usuarios", []):
            if u.get('email', '').lower() == email.lower():
                # Hash de la contraseña ingresada
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                print(f"[DEBUG] Hash esperado: {u.get('password')}")
                print(f"[DEBUG] Hash ingresado: {password_hash}")
                
                if u.get('password') == password_hash:
                    u_copy = u.copy()
                    u_copy.pop('password', None)
                    print(f"[DEBUG] ✅ Login exitoso: {email}")
                    return jsonify({"ok": True, "usuario": u_copy})
                else:
                    print(f"[DEBUG] ❌ Contraseña incorrecta para: {email}")
                return jsonify({"ok": False, "error": "Contraseña incorrecta"})
        
        print(f"[DEBUG] ❌ Usuario no encontrado: {email}")
        return jsonify({"ok": False, "error": "Usuario no encontrado"})
    except Exception as e:
        print(f"[ERROR] api_login: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})

# ==================== API - COSTOS TRASLADO ====================
def api_costos_traslado():
    costos = cargar_json(ARCHIVO_COSTOS_TRASLADO, {"costos": []})
    return jsonify({"costos": costos.get("costos", [])})

def api_costo_empresa(empresa_id):
    costos = cargar_json(ARCHIVO_COSTOS_TRASLADO, {"costos": []})
    for c in costos.get("costos", []):
        if c.get("empresa_id") == empresa_id:
            return jsonify({"ok": True, "costo": c})
    return jsonify({"ok": False, "costo": None})

def api_guardar_costo_empresa():
    try:
        data = request.get_json()
        costos = cargar_json(ARCHIVO_COSTOS_TRASLADO, {"costos": []})
        empresa_id = data.get("empresa_id")
        
        encontrado = False
        for c in costos.get("costos", []):
            if c.get("empresa_id") == empresa_id:
                c.update(data)
                encontrado = True
                break
        
        if not encontrado:
            costos["costos"].append(data)
        
        guardar_json(ARCHIVO_COSTOS_TRASLADO, costos)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_eliminar_costo_empresa():
    try:
        data = request.get_json()
        empresa_id = data.get("empresa_id")
        costos = cargar_json(ARCHIVO_COSTOS_TRASLADO, {"costos": []})
        costos["costos"] = [c for c in costos.get("costos", []) if c.get("empresa_id") != empresa_id]
        guardar_json(ARCHIVO_COSTOS_TRASLADO, costos)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==================== API - FLOTA (CONDUCTORES) ====================
def api_obtener_conductores():
    data = cargar_json(ARCHIVO_CONDUCTORES, {"conductores": []})
    return jsonify({"ok": True, "conductores": data.get("conductores", [])})

def api_crear_conductor():
    try:
        data = request.get_json()
        conductores_data = cargar_json(ARCHIVO_CONDUCTORES, {"conductores": [], "ultimo_id": 0})
        ultimo_id = conductores_data.get("ultimo_id", 0)
        nuevo_id = f"CON-{str(ultimo_id+1).zfill(3)}"
        
        nuevo_conductor = {
            "id": nuevo_id,
            "nombre": data.get("nombre", ""),
            "cedula": data.get("cedula", ""),
            "licencia": data.get("licencia", ""),
            "telefono": data.get("telefono", ""),
            "direccion": data.get("direccion", ""),
            "activo": True,
            "fecha_registro": datetime.now().isoformat()
        }
        conductores_data["conductores"].append(nuevo_conductor)
        conductores_data["ultimo_id"] = ultimo_id + 1
        guardar_json(ARCHIVO_CONDUCTORES, conductores_data)
        return jsonify({"ok": True, "conductor": nuevo_conductor})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_actualizar_conductor():
    try:
        data = request.get_json()
        conductor_id = data.get("id")
        campo = data.get("campo")
        valor = data.get("valor")
        
        conductores_data = cargar_json(ARCHIVO_CONDUCTORES, {"conductores": []})
        for c in conductores_data.get("conductores", []):
            if c.get("id") == conductor_id:
                c[campo] = valor
                guardar_json(ARCHIVO_CONDUCTORES, conductores_data)
                return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Conductor no encontrado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_eliminar_conductor():
    try:
        data = request.get_json()
        conductor_id = data.get("id")
        conductores_data = cargar_json(ARCHIVO_CONDUCTORES, {"conductores": []})
        conductores_data["conductores"] = [c for c in conductores_data.get("conductores", []) if c.get("id") != conductor_id]
        guardar_json(ARCHIVO_CONDUCTORES, conductores_data)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==================== API - FLOTA (CAMIONES) ====================
def api_obtener_camiones():
    data = cargar_json(ARCHIVO_CAMIONES, {"camiones": []})
    return jsonify({"ok": True, "camiones": data.get("camiones", [])})

def api_crear_camion():
    try:
        data = request.get_json()
        camiones_data = cargar_json(ARCHIVO_CAMIONES, {"camiones": [], "ultimo_id": 0})
        ultimo_id = camiones_data.get("ultimo_id", 0)
        nuevo_id = f"CAM-{str(ultimo_id+1).zfill(3)}"
        
        nuevo_camion = {
            "id": nuevo_id,
            "placa": data.get("placa", ""),
            "marca": data.get("marca", ""),
            "modelo": data.get("modelo", ""),
            "anio": data.get("anio", ""),
            "capacidad_galones": data.get("capacidad_galones", 0),
            "tipo": "Cisterna",
            "conductor_asignado": data.get("conductor_asignado", ""),
            "estado": data.get("estado", "Disponible"),
            "activo": True,
            "fecha_registro": datetime.now().isoformat()
        }
        camiones_data["camiones"].append(nuevo_camion)
        camiones_data["ultimo_id"] = ultimo_id + 1
        guardar_json(ARCHIVO_CAMIONES, camiones_data)
        return jsonify({"ok": True, "camion": nuevo_camion})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_actualizar_camion():
    try:
        data = request.get_json()
        camion_id = data.get("id")
        campo = data.get("campo")
        valor = data.get("valor")
        
        camiones_data = cargar_json(ARCHIVO_CAMIONES, {"camiones": []})
        for c in camiones_data.get("camiones", []):
            if c.get("id") == camion_id:
                c[campo] = valor
                guardar_json(ARCHIVO_CAMIONES, camiones_data)
                return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Camión no encontrado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_eliminar_camion():
    try:
        data = request.get_json()
        camion_id = data.get("id")
        camiones_data = cargar_json(ARCHIVO_CAMIONES, {"camiones": []})
        camiones_data["camiones"] = [c for c in camiones_data.get("camiones", []) if c.get("id") != camion_id]
        guardar_json(ARCHIVO_CAMIONES, camiones_data)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==================== API - FLOTA (MANTENIMIENTO) ====================
def api_obtener_mantenimiento():
    data = cargar_json(ARCHIVO_MANTENIMIENTO, {"registros": []})
    return jsonify({"ok": True, "registros": data.get("registros", [])})

def api_crear_mantenimiento():
    try:
        data = request.get_json()
        mantenimiento_data = cargar_json(ARCHIVO_MANTENIMIENTO, {"registros": [], "ultimo_id": 0})
        
        nuevo_registro = {
            "id": str(datetime.now().timestamp()),
            "camion_id": data.get("camion_id", ""),
            "camion_placa": data.get("camion_placa", ""),
            "fecha": data.get("fecha", datetime.now().strftime("%Y-%m-%d")),
            "tipo_mantenimiento": data.get("tipo_mantenimiento", ""),
            "descripcion": data.get("descripcion", ""),
            "costo": data.get("costo", 0),
            "kilometraje": data.get("kilometraje", 0),
            "proximo_mantenimiento": data.get("proximo_mantenimiento", ""),
            "estado": data.get("estado", "Pendiente"),
            "fecha_registro": datetime.now().isoformat()
        }
        mantenimiento_data["registros"].append(nuevo_registro)
        guardar_json(ARCHIVO_MANTENIMIENTO, mantenimiento_data)
        return jsonify({"ok": True, "registro": nuevo_registro})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_actualizar_mantenimiento():
    try:
        data = request.get_json()
        registro_id = data.get("id")
        campo = data.get("campo")
        valor = data.get("valor")
        
        mantenimiento_data = cargar_json(ARCHIVO_MANTENIMIENTO, {"registros": []})
        for r in mantenimiento_data.get("registros", []):
            if r.get("id") == registro_id:
                r[campo] = valor
                guardar_json(ARCHIVO_MANTENIMIENTO, mantenimiento_data)
                return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Registro no encontrado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_eliminar_mantenimiento():
    try:
        data = request.get_json()
        registro_id = data.get("id")
        mantenimiento_data = cargar_json(ARCHIVO_MANTENIMIENTO, {"registros": []})
        mantenimiento_data["registros"] = [r for r in mantenimiento_data.get("registros", []) if r.get("id") != registro_id]
        guardar_json(ARCHIVO_MANTENIMIENTO, mantenimiento_data)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==================== API - TABLAS EDITABLES ====================
def api_guardar_tabla_empresas():
    try:
        data = request.get_json()
        guardar_json(ARCHIVO_TABLAS_EDITABLES, data)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_cargar_tabla_empresas():
    data = cargar_json(ARCHIVO_TABLAS_EDITABLES, [])
    return jsonify({"datos": data})

def api_guardar_tabla_pedidos():
    try:
        data = request.get_json()
        guardar_json(ARCHIVO_TABLAS_EDITABLES, data)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_cargar_tabla_pedidos():
    data = cargar_json(ARCHIVO_TABLAS_EDITABLES, [])
    return jsonify({"datos": data})

def api_guardar_tabla_costos():
    try:
        data = request.get_json()
        guardar_json(ARCHIVO_TABLAS_EDITABLES, data)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_cargar_tabla_costos():
    data = cargar_json(ARCHIVO_TABLAS_EDITABLES, [])
    return jsonify({"datos": data})

# ==================== API - PEDIDOS ====================
def api_pedidos_combustible():
    pedidos = cargar_json(ARCHIVO_PEDIDOS, [])
    pedidos.sort(key=lambda x: x.get('fecha', ''), reverse=True)
    return jsonify({"pedidos": pedidos[:500]})

def api_actualizar_pedido_combustible():
    try:
        data = request.get_json()
        pedido_id = data.get('id')
        nuevos_datos = data.get('datos', {})
        pedidos = cargar_json(ARCHIVO_PEDIDOS, [])
        for p in pedidos:
            if p.get('id') == pedido_id:
                p.update(nuevos_datos)
                guardar_json(ARCHIVO_PEDIDOS, pedidos)
                return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Pedido no encontrado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_crear_pedido():
    try:
        data = request.get_json()
        pedidos = cargar_json(ARCHIVO_PEDIDOS, [])
        nuevo_id = f"PED-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"
        
        galones = float(data.get("galones", 0))
        precio = float(data.get("precio_por_galon", 0))
        costo_traslado = float(data.get("costo_traslado", 0))
        costo_combustible = galones * precio
        costo_total = costo_combustible + costo_traslado
        
        nuevo_pedido = {
            "id": nuevo_id,
            "empresa_id": data.get("empresa_id", ""),
            "nombre": data.get("nombre", "Cliente"),
            "fecha": datetime.now().isoformat(),
            "fecha_str": datetime.now().strftime("%Y-%m-%d"),
            "origen": data.get("origen", "Managua"),
            "destino": data.get("destino", "Leon"),
            "tipo_combustible": data.get("tipo_combustible", "DIESEL"),
            "galones": galones,
            "precio_por_galon": round(precio, 2),
            "costo_combustible": round(costo_combustible, 2),
            "costo_traslado": costo_traslado,
            "costo_total": round(costo_total, 2),
            "iva": round(costo_total * 0.19, 2),
            "importe": round(costo_total * 1.19, 2),
            "facturado": False,
            "estado_operacion": "espera",
            "conductor_asignado": data.get("conductor_asignado", ""),
            "conductor2_asignado": data.get("conductor2_asignado", ""),
            "camion_asignado": data.get("camion_asignado", ""),
            "camion2_asignado": data.get("camion2_asignado", ""),
            "bono1": data.get("bono1", ""),
            "bono2": data.get("bono2", ""),
            "viatico1": data.get("viatico1", 0),
            "viatico2": data.get("viatico2", 0)
        }
        
        pedidos.append(nuevo_pedido)
        guardar_json(ARCHIVO_PEDIDOS, pedidos)
        return jsonify({"ok": True, "pedido": nuevo_pedido})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==================== API - BITÁCORA ====================
def api_bitacora():
    bitacora = cargar_json(ARCHIVO_BITACORA, [])
    bitacora.sort(key=lambda x: x.get('fecha', ''), reverse=True)
    return jsonify({"bitacora": bitacora[:100]})

# ==================== API - PÁGINAS ====================
def api_paginas():
    data = cargar_json(ARCHIVO_PAGINAS, {"paginas": []})
    return jsonify({"paginas": data.get("paginas", [])})

def api_crear_pagina():
    try:
        data = request.get_json()
        paginas_data = cargar_json(ARCHIVO_PAGINAS, {"paginas": []})
        nuevo_id = str(random.randint(10000, 99999))
        
        nueva_pagina = {
            "id": nuevo_id,
            "nombre": data.get("nombre", ""),
            "url_id": data.get("url_id", f"pagina-{nuevo_id}"),
            "contenido": data.get("contenido", ""),
            "fecha_creacion": datetime.now().isoformat(),
            "activa": True
        }
        paginas_data["paginas"].append(nueva_pagina)
        guardar_json(ARCHIVO_PAGINAS, paginas_data)
        return jsonify({"ok": True, "pagina": nueva_pagina})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_eliminar_pagina():
    try:
        data = request.get_json()
        pagina_id = data.get("id")
        paginas_data = cargar_json(ARCHIVO_PAGINAS, {"paginas": []})
        paginas_data["paginas"] = [p for p in paginas_data.get("paginas", []) if p.get("id") != pagina_id]
        guardar_json(ARCHIVO_PAGINAS, paginas_data)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_obtener_pagina(id_pagina):
    paginas_data = cargar_json(ARCHIVO_PAGINAS, {"paginas": []})
    for p in paginas_data.get("paginas", []):
        if p.get("id") == id_pagina or p.get("url_id") == id_pagina:
            return jsonify({"ok": True, "pagina": p})
    return jsonify({"ok": False, "error": "Página no encontrada"})

def api_actualizar_pagina():
    try:
        data = request.get_json()
        pagina_id = data.get("id")
        nuevos_datos = data.get("datos", {})
        paginas_data = cargar_json(ARCHIVO_PAGINAS, {"paginas": []})
        for p in paginas_data.get("paginas", []):
            if p.get("id") == pagina_id:
                for k, v in nuevos_datos.items():
                    p[k] = v
                guardar_json(ARCHIVO_PAGINAS, paginas_data)
                return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Página no encontrada"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==================== API - CLOUDFLARE ====================
def api_cloudflare_url():
    url_data = cargar_json(ARCHIVO_URL_PUBLICA, {})
    return jsonify({"url": url_data.get("url", ""), "activo": bool(url_data.get("url"))})

def api_guardar_url_publica(url):
    guardar_json(ARCHIVO_URL_PUBLICA, {"url": url, "fecha_actualizacion": datetime.now().isoformat()})