# ==================== MÓDULO FLOTA - BACKEND COMPLETO ====================
import os
import json
from datetime import datetime
from flask import jsonify, request

# Variables globales
ARCHIVO_CONDUCTORES = None
ARCHIVO_CAMIONES = None
ARCHIVO_MANTENIMIENTO = None
_cargar_json = None
_guardar_json = None

def inicializar_flota(archivo_conductores, archivo_camiones, archivo_mantenimiento, cargar_json_func, guardar_json_func):
    global ARCHIVO_CONDUCTORES, ARCHIVO_CAMIONES, ARCHIVO_MANTENIMIENTO
    global _cargar_json, _guardar_json
    
    ARCHIVO_CONDUCTORES = archivo_conductores
    ARCHIVO_CAMIONES = archivo_camiones
    ARCHIVO_MANTENIMIENTO = archivo_mantenimiento
    _cargar_json = cargar_json_func
    _guardar_json = guardar_json_func
    
    # Crear estructura inicial si no existe
    if ARCHIVO_CONDUCTORES and not os.path.exists(ARCHIVO_CONDUCTORES):
        data_inicial = {"conductores": [], "ultimo_id": 0}
        _guardar_json(ARCHIVO_CONDUCTORES, data_inicial)
    
    if ARCHIVO_CAMIONES and not os.path.exists(ARCHIVO_CAMIONES):
        data_inicial = {"camiones": [], "ultimo_id": 0}
        _guardar_json(ARCHIVO_CAMIONES, data_inicial)
    
    if ARCHIVO_MANTENIMIENTO and not os.path.exists(ARCHIVO_MANTENIMIENTO):
        data_inicial = {"registros": [], "ultimo_id": 0}
        _guardar_json(ARCHIVO_MANTENIMIENTO, data_inicial)
    
    print(f"[INFO] Módulo Flota inicializado")

def cargar_json(ruta, default=None):
    if _cargar_json:
        return _cargar_json(ruta, default)
    if os.path.exists(ruta):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default if default is not None else {}
    return default if default is not None else {}

def guardar_json(ruta, data):
    if _guardar_json:
        return _guardar_json(ruta, data)
    try:
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

# ==================== CONDUCTORES ====================
def cargar_conductores():
    data = cargar_json(ARCHIVO_CONDUCTORES, {"conductores": [], "ultimo_id": 0})
    return data.get("conductores", [])

def guardar_conductores(conductores):
    data = cargar_json(ARCHIVO_CONDUCTORES, {"conductores": [], "ultimo_id": 0})
    data["conductores"] = conductores
    return guardar_json(ARCHIVO_CONDUCTORES, data)

def api_obtener_conductores():
    try:
        conductores = cargar_conductores()
        return jsonify({"ok": True, "conductores": conductores})
    except Exception as e:
        print(f"[ERROR] api_obtener_conductores: {e}")
        return jsonify({"ok": False, "error": str(e), "conductores": []})

def api_crear_conductor():
    try:
        data = request.get_json()
        conductores = cargar_conductores()
        ultimo_id = cargar_json(ARCHIVO_CONDUCTORES, {"ultimo_id": 0}).get("ultimo_id", 0)
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
        conductores.append(nuevo_conductor)
        
        data_file = cargar_json(ARCHIVO_CONDUCTORES, {"conductores": [], "ultimo_id": 0})
        data_file["conductores"] = conductores
        data_file["ultimo_id"] = ultimo_id + 1
        guardar_json(ARCHIVO_CONDUCTORES, data_file)
        
        return jsonify({"ok": True, "conductor": nuevo_conductor})
    except Exception as e:
        print(f"[ERROR] api_crear_conductor: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_actualizar_conductor():
    try:
        data = request.get_json()
        conductor_id = data.get("id")
        campo = data.get("campo")
        valor = data.get("valor")
        
        conductores = cargar_conductores()
        for c in conductores:
            if c.get("id") == conductor_id:
                c[campo] = valor
                guardar_conductores(conductores)
                return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Conductor no encontrado"})
    except Exception as e:
        print(f"[ERROR] api_actualizar_conductor: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_eliminar_conductor():
    try:
        data = request.get_json()
        conductor_id = data.get("id")
        
        conductores = cargar_conductores()
        conductores = [c for c in conductores if c.get("id") != conductor_id]
        guardar_conductores(conductores)
        
        return jsonify({"ok": True})
    except Exception as e:
        print(f"[ERROR] api_eliminar_conductor: {e}")
        return jsonify({"ok": False, "error": str(e)})

# ==================== CAMIONES ====================
def cargar_camiones():
    data = cargar_json(ARCHIVO_CAMIONES, {"camiones": [], "ultimo_id": 0})
    return data.get("camiones", [])

def guardar_camiones(camiones):
    data = cargar_json(ARCHIVO_CAMIONES, {"camiones": [], "ultimo_id": 0})
    data["camiones"] = camiones
    return guardar_json(ARCHIVO_CAMIONES, data)

def api_obtener_camiones():
    try:
        camiones = cargar_camiones()
        return jsonify({"ok": True, "camiones": camiones})
    except Exception as e:
        print(f"[ERROR] api_obtener_camiones: {e}")
        return jsonify({"ok": False, "error": str(e), "camiones": []})

def api_crear_camion():
    try:
        data = request.get_json()
        camiones = cargar_camiones()
        ultimo_id = cargar_json(ARCHIVO_CAMIONES, {"ultimo_id": 0}).get("ultimo_id", 0)
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
        camiones.append(nuevo_camion)
        
        data_file = cargar_json(ARCHIVO_CAMIONES, {"camiones": [], "ultimo_id": 0})
        data_file["camiones"] = camiones
        data_file["ultimo_id"] = ultimo_id + 1
        guardar_json(ARCHIVO_CAMIONES, data_file)
        
        return jsonify({"ok": True, "camion": nuevo_camion})
    except Exception as e:
        print(f"[ERROR] api_crear_camion: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_actualizar_camion():
    try:
        data = request.get_json()
        camion_id = data.get("id")
        campo = data.get("campo")
        valor = data.get("valor")
        
        camiones = cargar_camiones()
        for c in camiones:
            if c.get("id") == camion_id:
                c[campo] = valor
                guardar_camiones(camiones)
                return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Camión no encontrado"})
    except Exception as e:
        print(f"[ERROR] api_actualizar_camion: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_eliminar_camion():
    try:
        data = request.get_json()
        camion_id = data.get("id")
        
        camiones = cargar_camiones()
        camiones = [c for c in camiones if c.get("id") != camion_id]
        guardar_camiones(camiones)
        
        return jsonify({"ok": True})
    except Exception as e:
        print(f"[ERROR] api_eliminar_camion: {e}")
        return jsonify({"ok": False, "error": str(e)})

# ==================== MANTENIMIENTO ====================
def cargar_mantenimiento():
    if ARCHIVO_MANTENIMIENTO:
        data = cargar_json(ARCHIVO_MANTENIMIENTO, {"registros": [], "ultimo_id": 0})
        return data.get("registros", [])
    return []

def guardar_mantenimiento(registros):
    if ARCHIVO_MANTENIMIENTO:
        data = {"registros": registros, "ultimo_id": len(registros)}
        return guardar_json(ARCHIVO_MANTENIMIENTO, data)
    return False

def api_obtener_mantenimiento():
    try:
        registros = cargar_mantenimiento()
        return jsonify({"ok": True, "registros": registros})
    except Exception as e:
        print(f"[ERROR] api_obtener_mantenimiento: {e}")
        return jsonify({"ok": False, "error": str(e), "registros": []})

def api_crear_mantenimiento():
    try:
        data = request.get_json()
        registros = cargar_mantenimiento()
        
        nuevo_id = str(int(datetime.now().timestamp() * 1000))
        
        nuevo_registro = {
            "id": nuevo_id,
            "camion_id": data.get("camion_id", ""),
            "camion_placa": data.get("camion_placa", ""),
            "fecha": data.get("fecha", datetime.now().strftime("%Y-%m-%d")),
            "tipo_mantenimiento": data.get("tipo_mantenimiento", ""),
            "descripcion": data.get("descripcion", ""),
            "costo": float(data.get("costo", 0)),
            "kilometraje": int(data.get("kilometraje", 0)),
            "proximo_mantenimiento": data.get("proximo_mantenimiento", ""),
            "estado": data.get("estado", "Pendiente"),
            "fecha_registro": datetime.now().isoformat()
        }
        registros.append(nuevo_registro)
        guardar_mantenimiento(registros)
        
        return jsonify({"ok": True, "registro": nuevo_registro})
    except Exception as e:
        print(f"[ERROR] api_crear_mantenimiento: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_actualizar_mantenimiento():
    try:
        data = request.get_json()
        registro_id = data.get("id")
        campo = data.get("campo")
        valor = data.get("valor")
        
        registros = cargar_mantenimiento()
        for r in registros:
            if r.get("id") == registro_id:
                # Convertir tipos según el campo
                if campo in ["costo", "kilometraje"]:
                    try:
                        valor = float(valor) if campo == "costo" else int(valor)
                    except:
                        pass
                r[campo] = valor
                guardar_mantenimiento(registros)
                return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Registro no encontrado"})
    except Exception as e:
        print(f"[ERROR] api_actualizar_mantenimiento: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_eliminar_mantenimiento():
    try:
        data = request.get_json()
        registro_id = data.get("id")
        
        registros = cargar_mantenimiento()
        registros = [r for r in registros if r.get("id") != registro_id]
        guardar_mantenimiento(registros)
        
        return jsonify({"ok": True})
    except Exception as e:
        print(f"[ERROR] api_eliminar_mantenimiento: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_exportar_mantenimiento_excel():
    try:
        registros = cargar_mantenimiento()
        return jsonify({"ok": True, "registros": registros})
    except Exception as e:
        print(f"[ERROR] api_exportar_mantenimiento_excel: {e}")
        return jsonify({"ok": False, "error": str(e)})