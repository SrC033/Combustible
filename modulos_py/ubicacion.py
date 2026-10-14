# ==================== MODULO UBICACION (GPS) - MAPA DE NICARAGUA ====================
import os
import json
import random
import math
from datetime import datetime, timedelta
from flask import jsonify, request, render_template

# ==================== CONFIGURACIÓN ====================
ARCHIVO_UBICACIONES = None
ARCHIVO_VEHICULOS = None
ARCHIVO_PEDIDOS = None
_cargar_json = None
_guardar_json = None
_registrar_bitacora = None

# Coordenadas de ciudades de Nicaragua
CIUDADES_NICARAGUA = {
    "Managua": {"lat": 12.1364, "lng": -86.2514},
    "León": {"lat": 12.4358, "lng": -86.8789},
    "Granada": {"lat": 11.9295, "lng": -85.9535},
    "Masaya": {"lat": 11.9692, "lng": -86.0978},
    "Matagalpa": {"lat": 12.9276, "lng": -85.9206},
    "Estelí": {"lat": 13.0913, "lng": -86.3537},
    "Chinandega": {"lat": 12.6220, "lng": -87.1326},
    "Rivas": {"lat": 11.4360, "lng": -85.8260},
    "Jinotega": {"lat": 13.0925, "lng": -85.9998},
    "Bluefields": {"lat": 12.0134, "lng": -83.7637},
    "Ocotal": {"lat": 13.6325, "lng": -86.4765},
    "Puerto Cabezas": {"lat": 14.0244, "lng": -83.3987},
    "Juigalpa": {"lat": 12.1064, "lng": -85.3666},
    "Boaco": {"lat": 12.4722, "lng": -85.6586},
    "Diriamba": {"lat": 11.8583, "lng": -86.2389},
    "San Carlos": {"lat": 11.1333, "lng": -84.7833},
    "San Juan del Sur": {"lat": 11.2500, "lng": -85.8667}
}

# ==================== INICIALIZACIÓN ====================
def inicializar_ubicacion(rutas=None, main_funciones=None):
    global ARCHIVO_UBICACIONES, ARCHIVO_VEHICULOS, ARCHIVO_PEDIDOS
    global _cargar_json, _guardar_json, _registrar_bitacora
    
    if rutas:
        ARCHIVO_UBICACIONES = rutas.get('ubicaciones')
        ARCHIVO_VEHICULOS = rutas.get('vehiculos')
        ARCHIVO_PEDIDOS = rutas.get('pedidos')
    
    if main_funciones:
        _cargar_json = main_funciones.get('cargar_json')
        _guardar_json = main_funciones.get('guardar_json')
        _registrar_bitacora = main_funciones.get('registrar_bitacora')
    
    # Crear archivos si no existen
    if ARCHIVO_UBICACIONES and not os.path.exists(ARCHIVO_UBICACIONES):
        guardar_ubicaciones({"ultima_actualizacion": datetime.now().isoformat(), "vehiculos": []})
    
    print(f"[INFO] Módulo Ubicación GPS inicializado")
    print(f"[INFO] Archivo ubicaciones: {ARCHIVO_UBICACIONES}")


def cargar_ubicaciones():
    """Carga los datos de ubicación de vehículos"""
    if ARCHIVO_UBICACIONES and os.path.exists(ARCHIVO_UBICACIONES):
        try:
            with open(ARCHIVO_UBICACIONES, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] cargar_ubicaciones: {e}")
    return {"ultima_actualizacion": datetime.now().isoformat(), "vehiculos": []}


def guardar_ubicaciones(data):
    """Guarda los datos de ubicación de vehículos"""
    if ARCHIVO_UBICACIONES:
        try:
            data["ultima_actualizacion"] = datetime.now().isoformat()
            with open(ARCHIVO_UBICACIONES, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERROR] guardar_ubicaciones: {e}")
    return False


def cargar_vehiculos_desde_flota():
    """Carga vehículos desde el archivo de flota (camiones)"""
    if ARCHIVO_VEHICULOS and os.path.exists(ARCHIVO_VEHICULOS):
        try:
            with open(ARCHIVO_VEHICULOS, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("camiones", [])
        except Exception as e:
            print(f"[ERROR] cargar_vehiculos_desde_flota: {e}")
    return []


def generar_ubicacion_aleatoria():
    """Genera una ubicación aleatoria dentro de Nicaragua"""
    ciudad_nombre = random.choice(list(CIUDADES_NICARAGUA.keys()))
    ciudad = CIUDADES_NICARAGUA[ciudad_nombre]
    
    # Añadir pequeña variación aleatoria
    lat_offset = (random.random() - 0.5) * 0.02
    lng_offset = (random.random() - 0.5) * 0.02
    
    return {
        "lat": ciudad["lat"] + lat_offset,
        "lng": ciudad["lng"] + lng_offset,
        "ubicacion": ciudad_nombre,
        "departamento": ciudad_nombre
    }


def calcular_distancia(lat1, lng1, lat2, lng2):
    """Calcula la distancia en kilómetros entre dos puntos usando la fórmula de Haversine"""
    R = 6371  # Radio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def obtener_ciudad_mas_cercana(lat, lng):
    """Determina la ciudad más cercana a una ubicación dada"""
    ciudad_cercana = None
    dist_min = float('inf')
    for ciudad, coord in CIUDADES_NICARAGUA.items():
        dist = calcular_distancia(lat, lng, coord["lat"], coord["lng"])
        if dist < dist_min:
            dist_min = dist
            ciudad_cercana = ciudad
    return ciudad_cercana


# ==================== API ENDPOINTS ====================

def api_obtener_ubicaciones():
    """
    Obtiene todas las ubicaciones de vehículos
    """
    try:
        ubicaciones_data = cargar_ubicaciones()
        vehiculos = ubicaciones_data.get("vehiculos", [])
        
        # Si no hay ubicaciones guardadas, generar desde flota
        if not vehiculos:
            camiones = cargar_vehiculos_desde_flota()
            for camion in camiones:
                if camion.get("activo", True):
                    ubicacion = generar_ubicacion_aleatoria()
                    estados = ["activo", "en_camino", "inactivo"]
                    vehiculo = {
                        "id": camion.get("id", f"VEH-{len(vehiculos)+1:03d}"),
                        "placa": camion.get("placa", f"M{100000+len(vehiculos)}"),
                        "conductor": camion.get("conductor_asignado", "No asignado"),
                        "estado": random.choice(estados),
                        "lat": ubicacion["lat"],
                        "lng": ubicacion["lng"],
                        "ubicacion": ubicacion["ubicacion"],
                        "departamento": ubicacion["departamento"],
                        "ultima_actualizacion": datetime.now().isoformat(),
                        "velocidad": random.randint(20, 80),
                        "direccion": random.randint(0, 360),
                        "combustible": random.randint(60, 100),
                        "odometro": random.randint(10000, 50000)
                    }
                    vehiculos.append(vehiculo)
            
            # Guardar ubicaciones generadas
            ubicaciones_data["vehiculos"] = vehiculos
            guardar_ubicaciones(ubicaciones_data)
        
        return jsonify({
            "ok": True,
            "vehiculos": vehiculos,
            "ultima_actualizacion": ubicaciones_data.get("ultima_actualizacion"),
            "total": len(vehiculos)
        })
    except Exception as e:
        print(f"[ERROR] api_obtener_ubicaciones: {e}")
        return jsonify({"ok": False, "error": str(e), "vehiculos": []})


def api_actualizar_ubicacion():
    """
    Actualiza la ubicación de un vehículo específico
    """
    try:
        data = request.get_json()
        vehiculo_id = data.get("vehiculo_id")
        lat = data.get("lat")
        lng = data.get("lng")
        
        if not vehiculo_id or lat is None or lng is None:
            return jsonify({"ok": False, "error": "Faltan datos requeridos"})
        
        ubicaciones_data = cargar_ubicaciones()
        vehiculos = ubicaciones_data.get("vehiculos", [])
        
        encontrado = False
        for v in vehiculos:
            if v.get("id") == vehiculo_id:
                v["lat"] = lat
                v["lng"] = lng
                v["ultima_actualizacion"] = datetime.now().isoformat()
                # Determinar ciudad más cercana
                ciudad_cercana = obtener_ciudad_mas_cercana(lat, lng)
                if ciudad_cercana:
                    v["ubicacion"] = ciudad_cercana
                    v["departamento"] = ciudad_cercana
                encontrado = True
                break
        
        if not encontrado:
            return jsonify({"ok": False, "error": "Vehículo no encontrado"})
        
        guardar_ubicaciones(ubicaciones_data)
        
        if _registrar_bitacora:
            _registrar_bitacora(
                data.get('usuario', 'sistema'),
                "Actualizar Ubicación",
                f"Vehículo: {vehiculo_id} - Lat: {lat}, Lng: {lng}",
                "GPS"
            )
        
        return jsonify({"ok": True, "mensaje": "Ubicación actualizada"})
    except Exception as e:
        print(f"[ERROR] api_actualizar_ubicacion: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_actualizar_estado_vehiculo():
    """
    Actualiza el estado de un vehículo (activo, en_camino, inactivo)
    """
    try:
        data = request.get_json()
        vehiculo_id = data.get("vehiculo_id")
        estado = data.get("estado")
        
        if not vehiculo_id or not estado:
            return jsonify({"ok": False, "error": "Faltan datos requeridos"})
        
        if estado not in ["activo", "en_camino", "inactivo"]:
            return jsonify({"ok": False, "error": "Estado inválido"})
        
        ubicaciones_data = cargar_ubicaciones()
        vehiculos = ubicaciones_data.get("vehiculos", [])
        
        for v in vehiculos:
            if v.get("id") == vehiculo_id:
                v["estado"] = estado
                v["ultima_actualizacion"] = datetime.now().isoformat()
                break
        
        guardar_ubicaciones(ubicaciones_data)
        
        if _registrar_bitacora:
            _registrar_bitacora(
                data.get('usuario', 'sistema'),
                "Actualizar Estado Vehículo",
                f"Vehículo: {vehiculo_id} - Estado: {estado}",
                "GPS"
            )
        
        return jsonify({"ok": True, "mensaje": "Estado actualizado"})
    except Exception as e:
        print(f"[ERROR] api_actualizar_estado_vehiculo: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_obtener_vehiculo(vehiculo_id):
    """
    Obtiene información de un vehículo específico
    """
    try:
        ubicaciones_data = cargar_ubicaciones()
        for v in ubicaciones_data.get("vehiculos", []):
            if v.get("id") == vehiculo_id:
                return jsonify({"ok": True, "vehiculo": v})
        
        return jsonify({"ok": False, "error": "Vehículo no encontrado"})
    except Exception as e:
        print(f"[ERROR] api_obtener_vehiculo: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_sincronizar_con_flota():
    """
    Sincroniza las ubicaciones con los vehículos de la flota
    """
    try:
        camiones = cargar_vehiculos_desde_flota()
        ubicaciones_data = cargar_ubicaciones()
        vehiculos_actuales = ubicaciones_data.get("vehiculos", [])
        
        # Crear mapa de IDs existentes
        ids_existentes = {v.get("id"): v for v in vehiculos_actuales}
        
        # Agregar nuevos vehículos
        for camion in camiones:
            camion_id = camion.get("id")
            if camion_id not in ids_existentes and camion.get("activo", True):
                ubicacion = generar_ubicacion_aleatoria()
                nuevo = {
                    "id": camion_id,
                    "placa": camion.get("placa", f"M{100000+len(ids_existentes)}"),
                    "conductor": camion.get("conductor_asignado", "No asignado"),
                    "estado": "activo",
                    "lat": ubicacion["lat"],
                    "lng": ubicacion["lng"],
                    "ubicacion": ubicacion["ubicacion"],
                    "departamento": ubicacion["departamento"],
                    "ultima_actualizacion": datetime.now().isoformat(),
                    "velocidad": random.randint(20, 80),
                    "direccion": random.randint(0, 360),
                    "combustible": random.randint(60, 100),
                    "odometro": random.randint(10000, 50000)
                }
                vehiculos_actuales.append(nuevo)
        
        # Actualizar nombres de conductores desde flota
        for camion in camiones:
            for v in vehiculos_actuales:
                if v.get("id") == camion.get("id"):
                    v["conductor"] = camion.get("conductor_asignado", v.get("conductor", "No asignado"))
                    v["placa"] = camion.get("placa", v.get("placa", ""))
                    break
        
        ubicaciones_data["vehiculos"] = vehiculos_actuales
        guardar_ubicaciones(ubicaciones_data)
        
        return jsonify({
            "ok": True,
            "mensaje": f"Sincronizados {len(vehiculos_actuales)} vehículos",
            "total": len(vehiculos_actuales)
        })
    except Exception as e:
        print(f"[ERROR] api_sincronizar_con_flota: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_ciudades_nicaragua():
    """
    Retorna la lista de ciudades de Nicaragua con sus coordenadas
    """
    try:
        ciudades = []
        for nombre, coords in CIUDADES_NICARAGUA.items():
            ciudades.append({
                "nombre": nombre,
                "lat": coords["lat"],
                "lng": coords["lng"]
            })
        return jsonify({"ok": True, "ciudades": ciudades})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "ciudades": []})


def api_vehiculos_cercanos():
    """
    Encuentra vehículos cercanos a una ubicación dada
    """
    try:
        lat = float(request.args.get('lat', 0))
        lng = float(request.args.get('lng', 0))
        radio_km = float(request.args.get('radio', 50))
        
        ubicaciones_data = cargar_ubicaciones()
        vehiculos_cercanos = []
        
        for v in ubicaciones_data.get("vehiculos", []):
            dist = calcular_distancia(lat, lng, v.get("lat", 0), v.get("lng", 0))
            if dist <= radio_km:
                v_copy = v.copy()
                v_copy["distancia_km"] = round(dist, 1)
                vehiculos_cercanos.append(v_copy)
        
        vehiculos_cercanos.sort(key=lambda x: x.get("distancia_km", 999))
        
        return jsonify({
            "ok": True,
            "vehiculos": vehiculos_cercanos,
            "total": len(vehiculos_cercanos),
            "radio_km": radio_km
        })
    except Exception as e:
        print(f"[ERROR] api_vehiculos_cercanos: {e}")
        return jsonify({"ok": False, "error": str(e), "vehiculos": []})


# ==================== FUNCIONES PARA UBICACIÓN DE PEDIDOS ====================

def api_guardar_ubicacion_pedido():
    """
    Guarda la ubicación de un pedido específico
    """
    try:
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        ubicacion = data.get('ubicacion')
        
        if not pedido_id or not ubicacion:
            return jsonify({"ok": False, "error": "Faltan datos requeridos"})
        
        if 'lat' not in ubicacion or 'lng' not in ubicacion:
            return jsonify({"ok": False, "error": "Ubicación incompleta"})
        
        # Cargar pedidos
        if ARCHIVO_PEDIDOS and _cargar_json:
            pedidos = _cargar_json(ARCHIVO_PEDIDOS, [])
        else:
            return jsonify({"ok": False, "error": "Archivo de pedidos no disponible"})
        
        encontrado = False
        for p in pedidos:
            if p.get('id') == pedido_id:
                p['ubicacion_pedido'] = {
                    "lat": ubicacion.get('lat'),
                    "lng": ubicacion.get('lng'),
                    "direccion": ubicacion.get('direccion', ''),
                    "accuracy": ubicacion.get('accuracy', 0),
                    "fecha_captura": datetime.now().isoformat(),
                    "capturada_por": ubicacion.get('capturada_por', 'cliente')
                }
                encontrado = True
                break
        
        if not encontrado:
            return jsonify({"ok": False, "error": "Pedido no encontrado"})
        
        if _guardar_json:
            _guardar_json(ARCHIVO_PEDIDOS, pedidos)
        
        if _registrar_bitacora:
            _registrar_bitacora(
                data.get('usuario', 'sistema'),
                "Guardar Ubicación Pedido",
                f"Pedido: {pedido_id} - Lat: {ubicacion.get('lat')}, Lng: {ubicacion.get('lng')}",
                "GPS"
            )
        
        return jsonify({"ok": True, "mensaje": "Ubicación de pedido guardada"})
    except Exception as e:
        print(f"[ERROR] api_guardar_ubicacion_pedido: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_obtener_ubicacion_pedido(pedido_id):
    """
    Obtiene la ubicación de un pedido específico
    """
    try:
        if ARCHIVO_PEDIDOS and _cargar_json:
            pedidos = _cargar_json(ARCHIVO_PEDIDOS, [])
        else:
            return jsonify({"ok": False, "error": "Archivo de pedidos no disponible"})
        
        for p in pedidos:
            if p.get('id') == pedido_id:
                ubicacion = p.get('ubicacion_pedido')
                if ubicacion:
                    # También obtener información de la empresa
                    empresa_info = {
                        "nombre": p.get('nombre', ''),
                        "empresa_id": p.get('empresa_id', ''),
                        "fecha": p.get('fecha', ''),
                        "fecha_str": p.get('fecha_str', '')
                    }
                    return jsonify({
                        "ok": True,
                        "ubicacion": ubicacion,
                        "empresa": empresa_info
                    })
                return jsonify({
                    "ok": False,
                    "error": "No hay ubicación registrada para este pedido"
                })
        
        return jsonify({"ok": False, "error": "Pedido no encontrado"})
    except Exception as e:
        print(f"[ERROR] api_obtener_ubicacion_pedido: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_actualizar_ubicacion_pedido(pedido_id, lat, lng, direccion=""):
    """
    Actualiza la ubicación de un pedido (función interna para usar desde otros módulos)
    """
    try:
        if ARCHIVO_PEDIDOS and _cargar_json and _guardar_json:
            pedidos = _cargar_json(ARCHIVO_PEDIDOS, [])
        else:
            return False
        
        for p in pedidos:
            if p.get('id') == pedido_id:
                p['ubicacion_pedido'] = {
                    "lat": lat,
                    "lng": lng,
                    "direccion": direccion,
                    "fecha_captura": datetime.now().isoformat(),
                    "capturada_por": "sistema"
                }
                _guardar_json(ARCHIVO_PEDIDOS, pedidos)
                return True
        
        return False
    except Exception as e:
        print(f"[ERROR] api_actualizar_ubicacion_pedido: {e}")
        return False


def api_obtener_pedidos_con_ubicacion():
    """
    Obtiene todos los pedidos que tienen ubicación registrada
    """
    try:
        if ARCHIVO_PEDIDOS and _cargar_json:
            pedidos = _cargar_json(ARCHIVO_PEDIDOS, [])
        else:
            return jsonify({"ok": False, "error": "Archivo de pedidos no disponible"})
        
        pedidos_con_ubicacion = []
        for p in pedidos:
            if p.get('ubicacion_pedido'):
                pedidos_con_ubicacion.append({
                    "id": p.get('id'),
                    "empresa": p.get('nombre', ''),
                    "empresa_id": p.get('empresa_id', ''),
                    "fecha": p.get('fecha', ''),
                    "fecha_str": p.get('fecha_str', ''),
                    "tipo_combustible": p.get('tipo_combustible', ''),
                    "galones": p.get('galones', 0),
                    "costo_total": p.get('costo_total', 0),
                    "ubicacion": p.get('ubicacion_pedido'),
                    "estado_operacion": p.get('estado_operacion', '')
                })
        
        # Ordenar por fecha más reciente
        pedidos_con_ubicacion.sort(key=lambda x: x.get('fecha', ''), reverse=True)
        
        return jsonify({
            "ok": True,
            "pedidos": pedidos_con_ubicacion,
            "total": len(pedidos_con_ubicacion)
        })
    except Exception as e:
        print(f"[ERROR] api_obtener_pedidos_con_ubicacion: {e}")
        return jsonify({"ok": False, "error": str(e), "pedidos": []})


def api_estadisticas_ubicaciones():
    """
    Obtiene estadísticas de ubicaciones de pedidos
    """
    try:
        if ARCHIVO_PEDIDOS and _cargar_json:
            pedidos = _cargar_json(ARCHIVO_PEDIDOS, [])
        else:
            return jsonify({"ok": False, "error": "Archivo de pedidos no disponible"})
        
        total_pedidos = len(pedidos)
        pedidos_con_ubicacion = sum(1 for p in pedidos if p.get('ubicacion_pedido'))
        
        # Contar por estado de operación
        estados = {}
        for p in pedidos:
            estado = p.get('estado_operacion', 'desconocido')
            estados[estado] = estados.get(estado, 0) + 1
        
        # Contar por tipo de combustible
        combustibles = {}
        for p in pedidos:
            tipo = p.get('tipo_combustible', 'desconocido')
            combustibles[tipo] = combustibles.get(tipo, 0) + 1
        
        # Calcular total de galones y costo
        total_galones = sum(p.get('galones', 0) for p in pedidos)
        total_costo = sum(p.get('costo_total', 0) for p in pedidos)
        
        return jsonify({
            "ok": True,
            "estadisticas": {
                "total_pedidos": total_pedidos,
                "pedidos_con_ubicacion": pedidos_con_ubicacion,
                "porcentaje_con_ubicacion": round((pedidos_con_ubicacion / total_pedidos * 100) if total_pedidos > 0 else 0, 1),
                "total_galones": round(total_galones, 2),
                "total_costo": round(total_costo, 2),
                "estados": estados,
                "combustibles": combustibles
            }
        })
    except Exception as e:
        print(f"[ERROR] api_estadisticas_ubicaciones: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_exportar_ubicaciones():
    """
    Exporta todas las ubicaciones de pedidos en formato JSON
    """
    try:
        if ARCHIVO_PEDIDOS and _cargar_json:
            pedidos = _cargar_json(ARCHIVO_PEDIDOS, [])
        else:
            return jsonify({"ok": False, "error": "Archivo de pedidos no disponible"})
        
        datos_exportar = []
        for p in pedidos:
            if p.get('ubicacion_pedido'):
                datos_exportar.append({
                    "pedido_id": p.get('id'),
                    "empresa": p.get('nombre', ''),
                    "empresa_id": p.get('empresa_id', ''),
                    "fecha": p.get('fecha', ''),
                    "fecha_str": p.get('fecha_str', ''),
                    "tipo_combustible": p.get('tipo_combustible', ''),
                    "galones": p.get('galones', 0),
                    "costo_total": p.get('costo_total', 0),
                    "lat": p.get('ubicacion_pedido', {}).get('lat'),
                    "lng": p.get('ubicacion_pedido', {}).get('lng'),
                    "direccion": p.get('ubicacion_pedido', {}).get('direccion', ''),
                    "fecha_captura": p.get('ubicacion_pedido', {}).get('fecha_captura', ''),
                    "capturada_por": p.get('ubicacion_pedido', {}).get('capturada_por', '')
                })
        
        return jsonify({
            "ok": True,
            "datos": datos_exportar,
            "total": len(datos_exportar)
        })
    except Exception as e:
        print(f"[ERROR] api_exportar_ubicaciones: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_limpiar_ubicaciones_antiguas():
    """
    Limpia ubicaciones de pedidos más antiguas que una fecha dada
    """
    try:
        data = request.get_json()
        dias = data.get('dias', 30)
        
        if ARCHIVO_PEDIDOS and _cargar_json and _guardar_json:
            pedidos = _cargar_json(ARCHIVO_PEDIDOS, [])
        else:
            return jsonify({"ok": False, "error": "Archivo de pedidos no disponible"})
        
        fecha_limite = datetime.now() - timedelta(days=dias)
        eliminados = 0
        
        for p in pedidos:
            if p.get('ubicacion_pedido'):
                fecha_captura_str = p.get('ubicacion_pedido', {}).get('fecha_captura')
                if fecha_captura_str:
                    try:
                        fecha_captura = datetime.fromisoformat(fecha_captura_str)
                        if fecha_captura < fecha_limite:
                            # Eliminar la ubicación del pedido
                            p['ubicacion_pedido'] = None
                            eliminados += 1
                    except:
                        pass
        
        if _guardar_json:
            _guardar_json(ARCHIVO_PEDIDOS, pedidos)
        
        return jsonify({
            "ok": True,
            "mensaje": f"Se eliminaron {eliminados} ubicaciones antiguas",
            "eliminados": eliminados
        })
    except Exception as e:
        print(f"[ERROR] api_limpiar_ubicaciones_antiguas: {e}")
        return jsonify({"ok": False, "error": str(e)})


# ==================== FUNCIONES DE INTEGRACIÓN CON CHAT ====================

def api_obtener_conductores_chat():
    """
    Obtiene conductores conectados al chat con ubicaciones en tiempo real
    """
    try:
        from chat_conductores import api_obtener_conductores_conectados
        return api_obtener_conductores_conectados()
    except ImportError as e:
        print(f"[ERROR] chat_conductores no importado: {e}")
        return jsonify({"ok": False, "error": "Módulo de chat no disponible", "conductores": []})
    except Exception as e:
        print(f"[ERROR] api_obtener_conductores_chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e), "conductores": []})


def api_mensajes_conductor():
    """
    Obtiene mensajes de un conductor específico
    """
    try:
        from chat_conductores import api_obtener_mensajes_conductor
        return api_obtener_mensajes_conductor()
    except ImportError as e:
        print(f"[ERROR] chat_conductores no importado: {e}")
        return jsonify({"ok": False, "error": "Módulo de chat no disponible", "mensajes": []})
    except Exception as e:
        print(f"[ERROR] api_mensajes_conductor: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e), "mensajes": []})


def api_limpiar_mensajes_conductor():
    """
    Limpia mensajes de un conductor
    """
    try:
        from chat_conductores import api_limpiar_mensajes_conductor
        return api_limpiar_mensajes_conductor()
    except ImportError as e:
        print(f"[ERROR] chat_conductores no importado: {e}")
        return jsonify({"ok": False, "error": "Módulo de chat no disponible"})
    except Exception as e:
        print(f"[ERROR] api_limpiar_mensajes_conductor: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_limpiar_todos_mensajes():
    """
    Limpia todos los mensajes de todos los conductores
    """
    try:
        from chat_conductores import api_limpiar_todos_mensajes
        return api_limpiar_todos_mensajes()
    except ImportError as e:
        print(f"[ERROR] chat_conductores no importado: {e}")
        return jsonify({"ok": False, "error": "Módulo de chat no disponible"})
    except Exception as e:
        print(f"[ERROR] api_limpiar_todos_mensajes: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_eliminar_mensaje():
    """
    Elimina un mensaje específico
    """
    try:
        from chat_conductores import api_eliminar_mensaje
        return api_eliminar_mensaje()
    except ImportError as e:
        print(f"[ERROR] chat_conductores no importado: {e}")
        return jsonify({"ok": False, "error": "Módulo de chat no disponible"})
    except Exception as e:
        print(f"[ERROR] api_eliminar_mensaje: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_descargar_archivo_chat():
    """
    Descarga un archivo del chat
    """
    try:
        from chat_conductores import api_descargar_archivo
        return api_descargar_archivo()
    except ImportError as e:
        print(f"[ERROR] chat_conductores no importado: {e}")
        return jsonify({"ok": False, "error": "Módulo de chat no disponible"})
    except Exception as e:
        print(f"[ERROR] api_descargar_archivo_chat: {e}")
        return jsonify({"ok": False, "error": str(e)})