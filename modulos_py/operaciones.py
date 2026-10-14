# ==================== MODULO OPERACIONES - COMPLETO ACTUALIZADO ====================
import os
import json
import random
import time
import threading
from datetime import datetime, timedelta
from flask import jsonify, request

# ==================== CONFIGURACIÓN DE ARCHIVOS ====================
ARCHIVO_OPERACIONES = None
ARCHIVO_PEDIDOS = None
ARCHIVO_PEDIDOS_FACTURACION = None
ARCHIVO_CONDUCTORES = None
ARCHIVO_CAMIONES = None
ARCHIVO_TABLAS_EDITABLES = None
ARCHIVO_BITACORA = None
ARCHIVO_ESTADOS_FACTURAS = None
ARCHIVO_FACTURAS = None
ARCHIVO_OBSERVACIONES = None
ARCHIVO_COSTOS_TRASLADO = None
ARCHIVO_CLIENTES = None
ARCHIVO_EMPRESAS = None

# ==================== REFERENCIAS A FUNCIONES DEL MAIN ====================
_cargar_json = None
_guardar_json = None
_registrar_bitacora = None

# Estados de operación
ESTADO_ESPERA = 'espera'
ESTADO_COMPROBANTE = 'comprobante'
ESTADO_CAMINO = 'camino'
ESTADO_ENTREGADO = 'entregado'
ESTADO_FACTURACION = 'facturacion'


# ==================== INICIALIZACIÓN ====================
def inicializar_operaciones(ruta_archivo, main_funciones=None):
    global ARCHIVO_OPERACIONES, ARCHIVO_TABLAS_EDITABLES
    global ARCHIVO_PEDIDOS, ARCHIVO_PEDIDOS_FACTURACION
    global ARCHIVO_CONDUCTORES, ARCHIVO_CAMIONES
    global ARCHIVO_BITACORA, ARCHIVO_ESTADOS_FACTURAS
    global _cargar_json, _guardar_json, _registrar_bitacora
    global ARCHIVO_OBSERVACIONES, ARCHIVO_FACTURAS
    global ARCHIVO_COSTOS_TRASLADO, ARCHIVO_CLIENTES
    
    ARCHIVO_OPERACIONES = ruta_archivo
    ARCHIVO_TABLAS_EDITABLES = ruta_archivo
    
    if main_funciones:
        _cargar_json = main_funciones.get('cargar_json')
        _guardar_json = main_funciones.get('guardar_json')
        _registrar_bitacora = main_funciones.get('registrar_bitacora')
        # Obtener archivo de clientes desde main_funciones
        ARCHIVO_CLIENTES = main_funciones.get('archivo_clientes')
    
    base_dir = os.path.dirname(ruta_archivo) if ruta_archivo else "datos"
    ARCHIVO_ESTADOS_FACTURAS = os.path.join(base_dir, "estados_facturas.json")
    ARCHIVO_OBSERVACIONES = os.path.join(base_dir, "observaciones.json")
    ARCHIVO_COSTOS_TRASLADO = os.path.join(base_dir, "costos_traslado.json")
    
    # Si no se pasó ARCHIVO_CLIENTES, intentar localizarlo
    if not ARCHIVO_CLIENTES:
        ARCHIVO_CLIENTES = os.path.join(base_dir, "clientes.json")
    
    print(f"[INFO] ARCHIVO_CLIENTES: {ARCHIVO_CLIENTES}")
    print(f"[INFO] ARCHIVO_EMPRESAS: {ARCHIVO_EMPRESAS}")
    
    if ARCHIVO_OPERACIONES:
        try:
            os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
            if not os.path.exists(ruta_archivo):
                guardar_estado_operaciones({})
            if not os.path.exists(ARCHIVO_ESTADOS_FACTURAS):
                guardar_estados_facturas({})
            if not os.path.exists(ARCHIVO_OBSERVACIONES):
                guardar_observaciones({})
        except:
            pass
    
    print(f"[INFO] Módulo Operaciones inicializado")


def configurar_archivos(pedidos, pedidos_facturacion, conductores, camiones, bitacora, tablas_editables, facturas=None, costos_traslado=None, empresas=None):
    global ARCHIVO_PEDIDOS, ARCHIVO_PEDIDOS_FACTURACION, ARCHIVO_CONDUCTORES
    global ARCHIVO_CAMIONES, ARCHIVO_BITACORA, ARCHIVO_TABLAS_EDITABLES, ARCHIVO_FACTURAS
    global ARCHIVO_COSTOS_TRASLADO, ARCHIVO_EMPRESAS
    
    ARCHIVO_PEDIDOS = pedidos
    ARCHIVO_PEDIDOS_FACTURACION = pedidos_facturacion
    ARCHIVO_CONDUCTORES = conductores
    ARCHIVO_CAMIONES = camiones
    ARCHIVO_BITACORA = bitacora
    ARCHIVO_TABLAS_EDITABLES = tablas_editables
    ARCHIVO_FACTURAS = facturas
    ARCHIVO_COSTOS_TRASLADO = costos_traslado or os.path.join(os.path.dirname(pedidos), "costos_traslado.json")
    ARCHIVO_EMPRESAS = empresas or os.path.join(os.path.dirname(pedidos), "empresas.json")
    
    print(f"[DEBUG] Archivos configurados en Operaciones")
    print(f"[DEBUG] ARCHIVO_PEDIDOS: {ARCHIVO_PEDIDOS}")
    print(f"[DEBUG] ARCHIVO_PEDIDOS_FACTURACION: {ARCHIVO_PEDIDOS_FACTURACION}")
    print(f"[DEBUG] ARCHIVO_FACTURAS: {ARCHIVO_FACTURAS}")
    print(f"[DEBUG] ARCHIVO_COSTOS_TRASLADO: {ARCHIVO_COSTOS_TRASLADO}")
    print(f"[DEBUG] ARCHIVO_EMPRESAS: {ARCHIVO_EMPRESAS}")


# ==================== FUNCIONES PARA OBTENER DATOS DE GESTIÓN CLIENTES ====================

def cargar_clientes():
    """Carga los clientes desde el archivo de Gestión Clientes"""
    if not ARCHIVO_CLIENTES:
        return []
    try:
        if os.path.exists(ARCHIVO_CLIENTES):
            with open(ARCHIVO_CLIENTES, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and "clientes" in data:
                    return data.get("clientes", [])
                return []
    except Exception as e:
        print(f"[ERROR] cargar_clientes: {e}")
    return []


def cargar_empresas():
    """Carga las empresas desde empresas.json (fallback)"""
    if not ARCHIVO_EMPRESAS:
        return []
    try:
        if os.path.exists(ARCHIVO_EMPRESAS):
            with open(ARCHIVO_EMPRESAS, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and "empresas" in data:
                    return data.get("empresas", [])
                return []
    except Exception as e:
        print(f"[ERROR] cargar_empresas: {e}")
    return []


def obtener_cliente_por_id(cliente_id):
    """Obtiene un cliente específico desde Gestión Clientes"""
    if not cliente_id:
        return None
    clientes = cargar_clientes()
    for cli in clientes:
        if cli.get("id") == cliente_id:
            return cli
    return None


def obtener_bonos_viaticos_empresa(cliente_id):
    """
    Obtiene los bonos y viáticos de un cliente desde Gestión Clientes (clientes.json)
    Si no se encuentra, busca en empresas.json (fallback)
    Retorna: (bono1, bono2, viatico1, viatico2)
    """
    if not cliente_id:
        return "", "", 0, 0
    
    print(f"[DEBUG] Buscando bonos/viáticos para cliente: {cliente_id}")
    
    # 1. Buscar en clientes.json (Gestión Clientes)
    cli = obtener_cliente_por_id(cliente_id)
    if cli:
        bono1 = cli.get("bono1", "")
        bono2 = cli.get("bono2", "")
        viatico1 = float(cli.get("viatico1", 0))
        viatico2 = float(cli.get("viatico2", 0))
        
        print(f"[DEBUG] Bonos desde clientes.json - Bono1: '{bono1}', Bono2: '{bono2}', Viatico1: {viatico1}, Viatico2: {viatico2}")
        return bono1, bono2, viatico1, viatico2
    
    # 2. Buscar en empresas.json (fallback para compatibilidad)
    empresas = cargar_empresas()
    for emp in empresas:
        if emp.get("id") == cliente_id:
            bono1 = emp.get("bono1", "")
            bono2 = emp.get("bono2", "")
            viatico1 = float(emp.get("viatico1", 0))
            viatico2 = float(emp.get("viatico2", 0))
            print(f"[DEBUG] Bonos desde empresas.json - Bono1: '{bono1}', Bono2: '{bono2}', Viatico1: {viatico1}, Viatico2: {viatico2}")
            return bono1, bono2, viatico1, viatico2
    
    print(f"[DEBUG] No se encontraron bonos/viáticos para {cliente_id}")
    return "", "", 0, 0


def obtener_datos_ruta_cliente(cliente_id):
    """Obtiene los datos de ruta de un cliente desde Gestión Clientes"""
    cli = obtener_cliente_por_id(cliente_id)
    if not cli:
        return {"origen": "", "destino": "", "traslado": 0, "distancia": 0}
    
    return {
        "origen": cli.get("origen", ""),
        "destino": cli.get("destino", ""),
        "traslado": float(cli.get("traslado", 0)),
        "distancia": float(cli.get("distancia", 0))
    }


def obtener_credito_cliente(cliente_id):
    """Obtiene el crédito y límite de crédito de un cliente desde Gestión Clientes"""
    cli = obtener_cliente_por_id(cliente_id)
    if not cli:
        return {"credito": 0, "limite_credito": 0, "disponible": 0}
    
    credito = float(cli.get("credito", 0))
    limite = float(cli.get("limite_credito", 0))
    
    return {
        "credito": credito,
        "limite_credito": limite,
        "disponible": max(0, limite - credito) if limite > 0 else float('inf')
    }


def obtener_detalle_cliente_completo(cliente_id):
    """Obtiene todos los datos de un cliente desde Gestión Clientes"""
    cli = obtener_cliente_por_id(cliente_id)
    if not cli:
        return {}
    
    return {
        "nombre": cli.get("nombre", ""),
        "cedula": cli.get("cedula", ""),
        "telefono": cli.get("telefono", ""),
        "email": cli.get("email", ""),
        "direccion": cli.get("direccion", ""),
        "origen": cli.get("origen", ""),
        "destino": cli.get("destino", ""),
        "placa": cli.get("placa", ""),
        "conductor": cli.get("conductor", ""),
        "tipo": cli.get("tipo", "Cliente"),
        "credito": float(cli.get("credito", 0)),
        "limite_credito": float(cli.get("limite_credito", 0)),
        "diesel": float(cli.get("diesel", 0)),
        "diesel_max": float(cli.get("diesel_max", 0)),
        "gasolina": float(cli.get("gasolina", 0)),
        "gasolina_max": float(cli.get("gasolina_max", 0)),
        "bono1": cli.get("bono1", ""),
        "bono2": cli.get("bono2", ""),
        "viatico1": float(cli.get("viatico1", 0)),
        "viatico2": float(cli.get("viatico2", 0)),
        "traslado": float(cli.get("traslado", 0)),
        "distancia": float(cli.get("distancia", 0)),
        "costo_total": float(cli.get("costo_total", 0)),
        "activo": cli.get("activo", True)
    }


# ==================== FUNCIONES DE PERSISTENCIA ====================
def cargar_estado_operaciones():
    if ARCHIVO_OPERACIONES and os.path.exists(ARCHIVO_OPERACIONES):
        try:
            with open(ARCHIVO_OPERACIONES, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


def guardar_estado_operaciones(data):
    if ARCHIVO_OPERACIONES:
        try:
            with open(ARCHIVO_OPERACIONES, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
    return False


def guardar_asignacion_pedido(pedido_id, asignacion_data):
    estado = cargar_estado_operaciones()
    if "asignaciones" not in estado:
        estado["asignaciones"] = {}
    estado["asignaciones"][pedido_id] = {
        **asignacion_data,
        "fecha_actualizacion": datetime.now().isoformat()
    }
    guardar_estado_operaciones(estado)


def cargar_asignacion_pedido(pedido_id):
    estado = cargar_estado_operaciones()
    return estado.get("asignaciones", {}).get(pedido_id, {})


def guardar_pedido_seleccionado(pedido_id):
    estado = cargar_estado_operaciones()
    estado["pedido_seleccionado"] = pedido_id
    estado["ultima_actualizacion"] = datetime.now().isoformat()
    guardar_estado_operaciones(estado)


def cargar_pedido_seleccionado():
    estado = cargar_estado_operaciones()
    return estado.get("pedido_seleccionado", None)


def cargar_estados_facturas():
    if ARCHIVO_ESTADOS_FACTURAS and os.path.exists(ARCHIVO_ESTADOS_FACTURAS):
        try:
            with open(ARCHIVO_ESTADOS_FACTURAS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


def guardar_estados_facturas(estados):
    if ARCHIVO_ESTADOS_FACTURAS:
        try:
            with open(ARCHIVO_ESTADOS_FACTURAS, 'w', encoding='utf-8') as f:
                json.dump(estados, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
    return False


def cargar_observaciones():
    if ARCHIVO_OBSERVACIONES and os.path.exists(ARCHIVO_OBSERVACIONES):
        try:
            with open(ARCHIVO_OBSERVACIONES, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


def guardar_observaciones(observaciones):
    if ARCHIVO_OBSERVACIONES:
        try:
            with open(ARCHIVO_OBSERVACIONES, 'w', encoding='utf-8') as f:
                json.dump(observaciones, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
    return False


def guardar_observacion(factura_id, observacion, usuario="sistema"):
    observaciones = cargar_observaciones()
    observaciones[factura_id] = {
        "factura_id": factura_id,
        "observacion": observacion,
        "fecha": datetime.now().isoformat(),
        "usuario": usuario
    }
    guardar_observaciones(observaciones)
    return True


def obtener_observacion(factura_id):
    observaciones = cargar_observaciones()
    if factura_id in observaciones:
        return observaciones[factura_id].get("observacion", "")
    return ""


def cargar_pedidos():
    if _cargar_json:
        return _cargar_json(ARCHIVO_PEDIDOS, [])
    if ARCHIVO_PEDIDOS and os.path.exists(ARCHIVO_PEDIDOS):
        try:
            with open(ARCHIVO_PEDIDOS, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "pedidos" in data:
                    return data["pedidos"]
                return []
        except:
            return []
    return []


def guardar_pedidos(pedidos):
    if _guardar_json:
        return _guardar_json(ARCHIVO_PEDIDOS, pedidos)
    try:
        with open(ARCHIVO_PEDIDOS, 'w', encoding='utf-8') as f:
            json.dump(pedidos, f, indent=2, ensure_ascii=False)
        print(f"[DEBUG] ✅ Guardados {len(pedidos)} pedidos en {ARCHIVO_PEDIDOS}")
        return True
    except Exception as e:
        print(f"[ERROR] guardar_pedidos: {e}")
        return False


def cargar_pedidos_facturacion():
    if ARCHIVO_PEDIDOS_FACTURACION is None:
        return []
    if _cargar_json:
        return _cargar_json(ARCHIVO_PEDIDOS_FACTURACION, [])
    if os.path.exists(ARCHIVO_PEDIDOS_FACTURACION):
        try:
            with open(ARCHIVO_PEDIDOS_FACTURACION, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def guardar_pedidos_facturacion(pedidos):
    if ARCHIVO_PEDIDOS_FACTURACION is None:
        return False
    if _guardar_json:
        return _guardar_json(ARCHIVO_PEDIDOS_FACTURACION, pedidos)
    try:
        with open(ARCHIVO_PEDIDOS_FACTURACION, 'w', encoding='utf-8') as f:
            json.dump(pedidos, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] guardar_pedidos_facturacion: {e}")
        return False


def cargar_conductores():
    try:
        if _cargar_json:
            data = _cargar_json(ARCHIVO_CONDUCTORES, {"conductores": [], "ultimo_id": 0})
        else:
            if os.path.exists(ARCHIVO_CONDUCTORES):
                with open(ARCHIVO_CONDUCTORES, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"conductores": [], "ultimo_id": 0}
        return data.get("conductores", [])
    except:
        return []


def guardar_conductores(conductores):
    try:
        data = {"conductores": conductores, "ultimo_id": len(conductores)}
        if _guardar_json:
            return _guardar_json(ARCHIVO_CONDUCTORES, data)
        with open(ARCHIVO_CONDUCTORES, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] guardar_conductores: {e}")
        return False


def cargar_camiones():
    try:
        if _cargar_json:
            data = _cargar_json(ARCHIVO_CAMIONES, {"camiones": [], "ultimo_id": 0})
        else:
            if os.path.exists(ARCHIVO_CAMIONES):
                with open(ARCHIVO_CAMIONES, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"camiones": [], "ultimo_id": 0}
        return data.get("camiones", [])
    except:
        return []


def guardar_camiones(camiones):
    try:
        data = {"camiones": camiones, "ultimo_id": len(camiones)}
        if _guardar_json:
            return _guardar_json(ARCHIVO_CAMIONES, data)
        with open(ARCHIVO_CAMIONES, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] guardar_camiones: {e}")
        return False


def cargar_costos_traslado():
    try:
        if ARCHIVO_COSTOS_TRASLADO and os.path.exists(ARCHIVO_COSTOS_TRASLADO):
            with open(ARCHIVO_COSTOS_TRASLADO, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("costos", [])
    except Exception as e:
        print(f"[ERROR] cargar_costos_traslado: {e}")
    return []


def cargar_facturas():
    if ARCHIVO_FACTURAS is None:
        return []
    try:
        if _cargar_json:
            data = _cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
        else:
            if os.path.exists(ARCHIVO_FACTURAS):
                with open(ARCHIVO_FACTURAS, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"facturas": []}
        
        if isinstance(data, dict):
            return data.get("facturas", [])
        elif isinstance(data, list):
            return data
        return []
    except Exception as e:
        print(f"[ERROR] cargar_facturas: {e}")
        return []


def guardar_facturas(facturas):
    if ARCHIVO_FACTURAS is None:
        return False
    try:
        data = {"facturas": facturas}
        if _guardar_json:
            return _guardar_json(ARCHIVO_FACTURAS, data)
        with open(ARCHIVO_FACTURAS, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[DEBUG] ✅ Guardadas {len(facturas)} facturas en {ARCHIVO_FACTURAS}")
        return True
    except Exception as e:
        print(f"[ERROR] guardar_facturas: {e}")
        return False


# ==================== API ENDPOINTS ====================

def api_obtener_conductores():
    try:
        return jsonify({"ok": True, "conductores": cargar_conductores()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "conductores": []})


def api_obtener_camiones():
    try:
        return jsonify({"ok": True, "camiones": cargar_camiones()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "camiones": []})


def api_obtener_resumen_operaciones():
    try:
        pedidos = cargar_pedidos()
        pedidos_facturacion = cargar_pedidos_facturacion()
        
        galones_espera = 0
        galones_comprobante = 0
        galones_trasladando = 0
        galones_entregado = 0
        galones_facturacion = 0
        
        for p in pedidos:
            estado = p.get('estado_operacion', 'espera')
            galones = p.get('galones', 0)
            if estado == 'espera':
                galones_espera += galones
            elif estado == 'comprobante':
                galones_comprobante += galones
            elif estado == 'camino':
                galones_trasladando += galones
            elif estado == 'entregado':
                galones_entregado += galones
        
        for p in pedidos_facturacion:
            galones = p.get('galones', 0)
            galones_facturacion += galones
        
        return jsonify({
            "ok": True,
            "resumen": {
                "galones_espera": galones_espera,
                "galones_comprobante": galones_comprobante,
                "galones_trasladando": galones_trasladando,
                "galones_entregado": galones_entregado,
                "galones_facturacion": galones_facturacion,
                "total_pedidos_espera": len(pedidos),
                "total_pedidos_facturacion": len(pedidos_facturacion)
            }
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_obtener_datos_cliente_desde_gestion():
    """
    API para obtener datos completos de un cliente desde Gestión Clientes
    """
    try:
        cliente_id = request.args.get('cliente_id')
        if not cliente_id:
            return jsonify({"ok": False, "error": "Se requiere cliente_id"})
        
        datos = obtener_detalle_cliente_completo(cliente_id)
        if not datos:
            return jsonify({"ok": False, "error": "Cliente no encontrado"})
        
        return jsonify({"ok": True, "datos": datos})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_obtener_bonos_viaticos():
    """API para obtener bonos y viáticos de un cliente desde Gestión Clientes"""
    try:
        cliente_id = request.args.get('cliente_id')
        if not cliente_id:
            return jsonify({"ok": False, "error": "Se requiere cliente_id"})
        
        bono1, bono2, viatico1, viatico2 = obtener_bonos_viaticos_empresa(cliente_id)
        
        return jsonify({
            "ok": True,
            "bono1": bono1,
            "bono2": bono2,
            "viatico1": viatico1,
            "viatico2": viatico2
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_obtener_credito_cliente():
    """API para obtener el crédito de un cliente desde Gestión Clientes"""
    try:
        cliente_id = request.args.get('cliente_id')
        if not cliente_id:
            return jsonify({"ok": False, "error": "Se requiere cliente_id"})
        
        credito = obtener_credito_cliente(cliente_id)
        return jsonify({"ok": True, "credito": credito})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_actualizar_flota_pedido():
    """
    Actualiza la asignación de flota de un pedido.
    AHORA obtiene bonos y viáticos desde Gestión Clientes.
    """
    try:
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        
        if not pedido_id:
            return jsonify({"ok": False, "error": "Se requiere pedido_id"})
        
        # Obtener el pedido para saber la empresa
        pedido = None
        for p in cargar_pedidos():
            if p.get('id') == pedido_id:
                pedido = p
                break
        
        empresa_id = pedido.get("empresa_id", "") if pedido else ""
        
        # Obtener bonos y viáticos desde Gestión Clientes
        bono1_automatico, bono2_automatico, viatico1_automatico, viatico2_automatico = obtener_bonos_viaticos_empresa(empresa_id)
        
        # Obtener checkboxes del frontend
        check_bono1 = data.get('check_bono1', True)
        check_viatico1 = data.get('check_viatico1', True)
        check_bono2 = data.get('check_bono2', True)
        check_viatico2 = data.get('check_viatico2', True)
        
        # Asignar bonos y viáticos SOLO si los checkboxes están marcados
        bono1_final = data.get('bono1', bono1_automatico) if check_bono1 else ""
        bono2_final = data.get('bono2', bono2_automatico) if check_bono2 else ""
        viatico1_final = float(data.get('viatico1', viatico1_automatico)) if check_viatico1 else 0
        viatico2_final = float(data.get('viatico2', viatico2_automatico)) if check_viatico2 else 0
        
        print(f"[DEBUG] Bonos desde Gestión Clientes - Bono1: '{bono1_automatico}', Bono2: '{bono2_automatico}', Viatico1: {viatico1_automatico}, Viatico2: {viatico2_automatico}")
        print(f"[DEBUG] Checkboxes - Bono1: {check_bono1}, Viatico1: {check_viatico1}, Bono2: {check_bono2}, Viatico2: {check_viatico2}")
        print(f"[DEBUG] Bonos finales - Bono1: '{bono1_final}', Bono2: '{bono2_final}', Viatico1: {viatico1_final}, Viatico2: {viatico2_final}")
        
        asignacion = {
            'conductor_asignado': data.get('conductor', ''),
            'conductor2_asignado': data.get('conductor2', ''),
            'camion_asignado': data.get('camion', ''),
            'camion2_asignado': data.get('camion2', ''),
            'bono1': bono1_final,
            'bono2': bono2_final,
            'viatico1': viatico1_final,
            'viatico2': viatico2_final
        }
        
        guardar_asignacion_pedido(pedido_id, asignacion)
        
        # Actualizar en pedidos activos
        pedidos = cargar_pedidos()
        for p in pedidos:
            if p.get('id') == pedido_id:
                p.update(asignacion)
                break
        guardar_pedidos(pedidos)
        
        # Actualizar también en facturación si existe
        pedidos_facturacion = cargar_pedidos_facturacion()
        for p in pedidos_facturacion:
            if p.get('id') == pedido_id:
                p.update(asignacion)
                break
        guardar_pedidos_facturacion(pedidos_facturacion)
        
        notificar_actualizacion()
        
        return jsonify({"ok": True})
    except Exception as e:
        print(f"[ERROR] api_actualizar_flota_pedido: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_crear_pedido_manual():
    """Crea un nuevo pedido manualmente - Obtiene datos desde Gestión Clientes"""
    try:
        data = request.get_json()
        
        nuevo_id = f"PED-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"
        
        empresa_id = data.get('empresa_id', '')
        
        # Obtener datos del cliente desde Gestión Clientes
        cliente_datos = obtener_detalle_cliente_completo(empresa_id) if empresa_id else {}
        
        galones = float(data.get('galones', 0))
        precio = float(data.get('precio_por_galon', 0))
        costo_traslado = float(data.get('costo_traslado', cliente_datos.get('traslado', 0)))
        costo_combustible = galones * precio
        costo_total = costo_combustible + costo_traslado
        
        # Obtener bonos y viáticos desde Gestión Clientes
        bono1, bono2, viatico1, viatico2 = obtener_bonos_viaticos_empresa(empresa_id)
        
        # Verificar checkboxes para el nuevo pedido (desde el frontend)
        check_bono1 = data.get('check_bono1', True)
        check_viatico1 = data.get('check_viatico1', True)
        check_bono2 = data.get('check_bono2', True)
        check_viatico2 = data.get('check_viatico2', True)
        
        # Solo asignar si los checkboxes están marcados
        bono1_final = bono1 if check_bono1 else ""
        bono2_final = bono2 if check_bono2 else ""
        viatico1_final = viatico1 if check_viatico1 else 0
        viatico2_final = viatico2 if check_viatico2 else 0
        
        # Obtener conductor y placa desde el cliente si no se especificaron
        conductor_asignado = data.get('conductor_asignado', cliente_datos.get('conductor', ''))
        camion_asignado = data.get('camion_asignado', cliente_datos.get('placa', ''))
        
        nuevo_pedido = {
            "id": nuevo_id,
            "empresa_id": empresa_id,
            "nombre": data.get('nombre', cliente_datos.get('nombre', 'Cliente')),
            "cedula": data.get('cedula', cliente_datos.get('cedula', '')),
            "telefono": data.get('telefono', cliente_datos.get('telefono', '')),
            "email": data.get('email', cliente_datos.get('email', '')),
            "fecha": datetime.now().isoformat(),
            "fecha_str": datetime.now().strftime("%Y-%m-%d"),
            "origen": data.get('origen', cliente_datos.get('origen', 'Managua')),
            "destino": data.get('destino', cliente_datos.get('destino', 'León')),
            "tipo_combustible": data.get('tipo_combustible', 'DIESEL'),
            "galones": galones,
            "precio_por_galon": precio,
            "costo_combustible": costo_combustible,
            "costo_traslado": costo_traslado,
            "costo_total": costo_total,
            "iva": round(costo_total * 0.19, 2),
            "importe": round(costo_total * 1.19, 2),
            "facturado": False,
            "estado_operacion": ESTADO_ESPERA,
            "conductor_asignado": conductor_asignado,
            "conductor2_asignado": data.get('conductor2_asignado', ''),
            "camion_asignado": camion_asignado,
            "camion2_asignado": data.get('camion2_asignado', ''),
            # Bonos y viáticos - solo si los checkboxes están marcados
            "bono1": bono1_final,
            "bono2": bono2_final,
            "viatico1": viatico1_final,
            "viatico2": viatico2_final,
            "distancia_km": cliente_datos.get('distancia', 0),
            "costo_km": 0,
            "observacion": data.get('observacion', '')
        }
        
        pedidos = cargar_pedidos()
        pedidos.append(nuevo_pedido)
        guardar_pedidos(pedidos)
        
        notificar_actualizacion()
        
        return jsonify({"ok": True, "pedido": nuevo_pedido, "id": nuevo_id})
    except Exception as e:
        print(f"[ERROR] api_crear_pedido_manual: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_enviar_a_facturacion():
    """
    Envía el pedido a Facturación.
    AHORA obtiene bonos/viáticos desde Gestión Clientes y respeta checkboxes.
    """
    try:
        print("[DEBUG] ===== api_enviar_a_facturacion iniciada =====")
        
        if not request.is_json:
            return jsonify({"ok": False, "error": "La solicitud debe ser JSON"})
        
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        pedido_modificado = data.get('pedido_modificado', {})
        
        if not pedido_id:
            return jsonify({"ok": False, "error": "No se recibió pedido_id"})
        
        pedidos = cargar_pedidos()
        pedido_encontrado = None
        
        for p in pedidos:
            if p.get('id') == pedido_id:
                pedido_encontrado = p.copy()
                break
        
        if not pedido_encontrado and pedido_modificado:
            pedido_encontrado = pedido_modificado.copy()
            pedido_encontrado['id'] = pedido_id
        
        if not pedido_encontrado:
            pedidos_facturacion = cargar_pedidos_facturacion()
            for p in pedidos_facturacion:
                if p.get('id') == pedido_id:
                    pedido_encontrado = p.copy()
                    break
        
        if not pedido_encontrado:
            return jsonify({"ok": False, "error": "No se encontró el pedido"})
        
        # Obtener bonos y viáticos desde Gestión Clientes
        empresa_id = pedido_encontrado.get('empresa_id', '')
        bono1, bono2, viatico1, viatico2 = obtener_bonos_viaticos_empresa(empresa_id)
        
        # Verificar checkboxes que vienen desde el frontend
        check_bono1 = data.get('check_bono1', True)
        check_viatico1 = data.get('check_viatico1', True)
        check_bono2 = data.get('check_bono2', True)
        check_viatico2 = data.get('check_viatico2', True)
        
        # Asignar bonos y viáticos SOLO si los checkboxes están marcados
        bono1_final = bono1 if check_bono1 else ""
        bono2_final = bono2 if check_bono2 else ""
        viatico1_final = viatico1 if check_viatico1 else 0
        viatico2_final = viatico2 if check_viatico2 else 0
        
        print(f"[DEBUG] Bonos desde Gestión Clientes - Bono1: '{bono1}', Bono2: '{bono2}', Viatico1: {viatico1}, Viatico2: {viatico2}")
        print(f"[DEBUG] Checkboxes recibidos - Bono1: {check_bono1}, Viatico1: {check_viatico1}, Bono2: {check_bono2}, Viatico2: {check_viatico2}")
        print(f"[DEBUG] Bonos finales - Bono1: '{bono1_final}', Bono2: '{bono2_final}', Viatico1: {viatico1_final}, Viatico2: {viatico2_final}")
        
        # 2. ELIMINAR de pedidos_combustible.json (desaparece de Recepción)
        pedidos_actualizados = [p for p in pedidos if p.get('id') != pedido_id]
        guardar_pedidos(pedidos_actualizados)
        print(f"[DEBUG] ✅ Pedido {pedido_id} ELIMINADO de pedidos_combustible.json")
        
        # 3. GUARDAR en pedidos_facturacion.json
        pedidos_facturacion = cargar_pedidos_facturacion()
        if not isinstance(pedidos_facturacion, list):
            pedidos_facturacion = []
        
        pedidos_facturacion = [p for p in pedidos_facturacion if p.get('id') != pedido_id]
        
        pedido_para_facturacion = {
            "id": pedido_id,
            "empresa_id": pedido_encontrado.get('empresa_id', ''),
            "nombre": pedido_encontrado.get('nombre', ''),
            "cedula": pedido_encontrado.get('cedula', ''),
            "telefono": pedido_encontrado.get('telefono', ''),
            "email": pedido_encontrado.get('email', ''),
            "fecha": pedido_encontrado.get('fecha', datetime.now().isoformat()),
            "fecha_str": pedido_encontrado.get('fecha_str', datetime.now().strftime("%Y-%m-%d")),
            "origen": pedido_encontrado.get('origen', 'Managua'),
            "destino": pedido_encontrado.get('destino', 'León'),
            "tipo_combustible": pedido_encontrado.get('tipo_combustible', 'DIESEL'),
            "galones": pedido_encontrado.get('galones', 0),
            "precio_por_galon": pedido_encontrado.get('precio_por_galon', 0),
            "costo_combustible": pedido_encontrado.get('costo_combustible', 0),
            "costo_traslado": pedido_encontrado.get('costo_traslado', 0),
            "costo_total": pedido_encontrado.get('costo_total', 0),
            "iva": pedido_encontrado.get('iva', 0),
            "importe": pedido_encontrado.get('importe', 0),
            "facturado": False,
            "conductor_asignado": pedido_encontrado.get('conductor_asignado', ''),
            "conductor2_asignado": pedido_encontrado.get('conductor2_asignado', ''),
            "camion_asignado": pedido_encontrado.get('camion_asignado', ''),
            "camion2_asignado": pedido_encontrado.get('camion2_asignado', ''),
            # USAR los valores finales que respetan los checkboxes
            "bono1": bono1_final,
            "bono2": bono2_final,
            "viatico1": viatico1_final,
            "viatico2": viatico2_final,
            "placa": pedido_encontrado.get('camion_asignado', ''),
            "placa2": pedido_encontrado.get('camion2_asignado', ''),
            "estado_operacion": ESTADO_FACTURACION,
            "fecha_envio_facturacion": datetime.now().isoformat(),
            "observacion": pedido_encontrado.get('observacion', ''),
            "distancia_km": pedido_encontrado.get('distancia_km', 0),
            "costo_km": pedido_encontrado.get('costo_km', 0)
        }
        
        pedidos_facturacion.append(pedido_para_facturacion)
        guardar_pedidos_facturacion(pedidos_facturacion)
        print(f"[DEBUG] ✅ Pedido {pedido_id} GUARDADO en pedidos_facturacion.json con bonos/viáticos desde Gestión Clientes")
        
        estados = cargar_estados_facturas()
        estados[pedido_id] = ESTADO_FACTURACION
        guardar_estados_facturas(estados)
        
        notificar_actualizacion()
        
        try:
            import requests
            requests.post('http://localhost:5000/api/notificar_pedido_facturacion', 
                         json={"pedido_id": pedido_id, "estado": "enviado"}, timeout=2)
            print(f"[DEBUG] ✅ Notificación enviada a Facturación")
        except Exception as e:
            print(f"[WARN] No se pudo notificar a Facturación: {e}")
        
        return jsonify({
            "ok": True,
            "mensaje": "Pedido enviado a Facturación correctamente",
            "pedido_id": pedido_id
        })
    
    except Exception as e:
        print(f"[ERROR] api_enviar_a_facturacion: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


def api_actualizar_estado_operacion():
    try:
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        estado = data.get('estado')
        datos = data.get('datos', {})
        
        pedidos = cargar_pedidos()
        for p in pedidos:
            if p.get('id') == pedido_id:
                p['estado_operacion'] = estado
                for k, v in datos.items():
                    p[k] = v
                guardar_pedidos(pedidos)
                break
        
        pedidos_facturacion = cargar_pedidos_facturacion()
        for p in pedidos_facturacion:
            if p.get('id') == pedido_id:
                p['estado_operacion'] = estado
                for k, v in datos.items():
                    p[k] = v
                break
        guardar_pedidos_facturacion(pedidos_facturacion)
        
        estados = cargar_estados_facturas()
        estados[pedido_id] = estado
        guardar_estados_facturas(estados)
        
        notificar_actualizacion()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_actualizar_estado_con_factura():
    try:
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        factura_id = data.get('factura_id')
        
        print(f"[DEBUG] Notificación de Facturación - Pedido: {pedido_id}, Factura: {factura_id}")
        
        pedidos_facturacion = cargar_pedidos_facturacion()
        pedidos_facturacion = [p for p in pedidos_facturacion if p.get('id') != pedido_id]
        guardar_pedidos_facturacion(pedidos_facturacion)
        print(f"[DEBUG] ✅ Pedido {pedido_id} ELIMINADO de cola de facturación")
        
        estados = cargar_estados_facturas()
        if factura_id:
            estados[factura_id] = ESTADO_COMPROBANTE
        if pedido_id:
            estados[pedido_id] = ESTADO_COMPROBANTE
        guardar_estados_facturas(estados)
        
        notificar_actualizacion()
        
        return jsonify({"ok": True})
    except Exception as e:
        print(f"[ERROR] api_actualizar_estado_con_factura: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_actualizar_pedido_desde_factura():
    try:
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        factura_id = data.get('factura_id')
        nuevo_total = data.get('nuevo_total', 0)
        galones = data.get('galones', 0)
        precio = data.get('precio', 0)
        costo_traslado = data.get('costo_traslado', 0)
        filas = data.get('filas', [])
        
        print(f"[DEBUG] ===== ACTUALIZANDO PEDIDO DESDE FACTURA =====")
        print(f"[DEBUG] Pedido ID: {pedido_id}, Nuevo total: {nuevo_total}")
        
        pedidos_facturacion = cargar_pedidos_facturacion()
        encontrado = False
        
        for p in pedidos_facturacion:
            if p.get('id') == pedido_id:
                p['total'] = nuevo_total
                p['costo_total'] = nuevo_total
                p['galones'] = galones
                p['precio_por_galon'] = precio
                p['costo_traslado'] = costo_traslado
                p['costo_combustible'] = galones * precio
                p['fecha_actualizacion'] = datetime.now().isoformat()
                p['factura_actualizada'] = True
                if filas:
                    p['filas'] = filas
                encontrado = True
                break
        
        if encontrado:
            guardar_pedidos_facturacion(pedidos_facturacion)
            notificar_actualizacion()
            return jsonify({"ok": True})
        else:
            return jsonify({"ok": False, "error": "Pedido no encontrado"})
            
    except Exception as e:
        print(f"[ERROR] api_actualizar_pedido_desde_factura: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_obtener_estados_facturas():
    try:
        estados = cargar_estados_facturas()
        return jsonify({"ok": True, "estados": estados})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "estados": {}})


def api_guardar_estado_factura():
    try:
        data = request.get_json()
        factura_id = data.get('factura_id')
        estado = data.get('estado')
        
        if not factura_id:
            return jsonify({"ok": False, "error": "Se requiere factura_id"})
        
        print(f"[DEBUG] Actualizando estado de factura: {factura_id} -> {estado}")
        
        estados = cargar_estados_facturas()
        estados[factura_id] = estado
        guardar_estados_facturas(estados)
        
        facturas = cargar_facturas()
        for f in facturas:
            if f.get('id') == factura_id:
                f['estado_factura'] = estado
                if estado == ESTADO_ENTREGADO:
                    f['fecha_entrega'] = datetime.now().isoformat()
                break
        guardar_facturas(facturas)
        
        notificar_actualizacion()
        
        return jsonify({"ok": True, "mensaje": f"Estado actualizado a {estado}"})
    except Exception as e:
        print(f"[ERROR] api_guardar_estado_factura: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_marcar_como_entregado():
    try:
        data = request.get_json()
        factura_id = data.get('factura_id')
        pedido_id = data.get('pedido_id')
        
        if not factura_id:
            return jsonify({"ok": False, "error": "Se requiere factura_id"})
        
        print(f"[DEBUG] 📦 Marcando como entregado - Factura: {factura_id}, Pedido: {pedido_id}")
        
        estados = cargar_estados_facturas()
        estados[factura_id] = ESTADO_ENTREGADO
        if pedido_id:
            estados[pedido_id] = ESTADO_ENTREGADO
        guardar_estados_facturas(estados)
        
        facturas = cargar_facturas()
        for f in facturas:
            if f.get('id') == factura_id:
                f['estado_factura'] = ESTADO_ENTREGADO
                f['fecha_entrega'] = datetime.now().isoformat()
                f['entregado'] = True
                break
        guardar_facturas(facturas)
        
        pedidos_facturacion = cargar_pedidos_facturacion()
        pedidos_facturacion = [p for p in pedidos_facturacion if p.get('id') != pedido_id]
        guardar_pedidos_facturacion(pedidos_facturacion)
        
        guardar_pedido_seleccionado(None)
        notificar_actualizacion()
        
        return jsonify({"ok": True, "mensaje": "Pedido marcado como entregado"})
    except Exception as e:
        print(f"[ERROR] api_marcar_como_entregado: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_marcar_como_camino():
    try:
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        factura_id = data.get('factura_id')
        
        if not pedido_id and not factura_id:
            return jsonify({"ok": False, "error": "Se requiere pedido_id o factura_id"})
        
        print(f"[DEBUG] 🚚 Marcando como En Camino - Pedido: {pedido_id}, Factura: {factura_id}")
        
        pedidos_facturacion = cargar_pedidos_facturacion()
        pedido_encontrado = None
        
        for p in pedidos_facturacion:
            if p.get('id') == pedido_id:
                pedido_encontrado = p.copy()
                break
        
        if not pedido_encontrado:
            return jsonify({"ok": False, "error": "Pedido no encontrado en cola de facturación"})
        
        facturas = cargar_facturas()
        factura_existente = None
        
        for f in facturas:
            if f.get('id') == factura_id or f.get('pedido_id') == pedido_id:
                factura_existente = f
                break
        
        nueva_factura_id = None
        
        if factura_existente:
            factura_existente['estado_factura'] = ESTADO_CAMINO
            factura_existente['estado_operacion'] = ESTADO_CAMINO
            factura_existente['fecha_envio'] = datetime.now().isoformat()
            nueva_factura_id = factura_existente.get('id')
        else:
            nueva_factura_id = factura_id or f"FAC-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"
            nueva_factura = {
                "id": nueva_factura_id,
                "pedido_id": pedido_id,
                "empresa_id": pedido_encontrado.get('empresa_id', ''),
                "empresa_nombre": pedido_encontrado.get('nombre', ''),
                "cedula": pedido_encontrado.get('cedula', ''),
                "telefono": pedido_encontrado.get('telefono', ''),
                "email": pedido_encontrado.get('email', ''),
                "fecha_emision": datetime.now().isoformat(),
                "fecha_envio": datetime.now().isoformat(),
                "origen": pedido_encontrado.get('origen', 'Managua'),
                "destino": pedido_encontrado.get('destino', ''),
                "tipo_combustible": pedido_encontrado.get('tipo_combustible', 'DIESEL'),
                "galones": pedido_encontrado.get('galones', 0),
                "precio_por_galon": pedido_encontrado.get('precio_por_galon', 0),
                "costo_combustible": pedido_encontrado.get('costo_combustible', 0),
                "costo_traslado": pedido_encontrado.get('costo_traslado', 0),
                "costo_total": pedido_encontrado.get('costo_total', 0),
                "total": pedido_encontrado.get('costo_total', 0),
                "conductor_asignado": pedido_encontrado.get('conductor_asignado', ''),
                "conductor2_asignado": pedido_encontrado.get('conductor2_asignado', ''),
                "camion_asignado": pedido_encontrado.get('camion_asignado', ''),
                "camion2_asignado": pedido_encontrado.get('camion2_asignado', ''),
                "estado_factura": ESTADO_CAMINO,
                "estado_operacion": ESTADO_CAMINO,
                "observacion": pedido_encontrado.get('observacion', '')
            }
            facturas.append(nueva_factura)
        
        guardar_facturas(facturas)
        
        for p in pedidos_facturacion:
            if p.get('id') == pedido_id:
                p['estado_operacion'] = ESTADO_CAMINO
                p['factura_id'] = nueva_factura_id
                break
        guardar_pedidos_facturacion(pedidos_facturacion)
        
        estados = cargar_estados_facturas()
        if nueva_factura_id:
            estados[nueva_factura_id] = ESTADO_CAMINO
        if pedido_id:
            estados[pedido_id] = ESTADO_CAMINO
        guardar_estados_facturas(estados)
        
        notificar_actualizacion()
        
        return jsonify({"ok": True, "mensaje": "Pedido marcado como En Camino", "factura_id": nueva_factura_id})
    except Exception as e:
        print(f"[ERROR] api_marcar_como_camino: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_obtener_facturas_lista():
    try:
        facturas = cargar_facturas()
        estados = cargar_estados_facturas()
        observaciones = cargar_observaciones()
        
        facturas_con_estado = []
        for f in facturas:
            f_copy = f.copy()
            f_copy['estado_factura'] = estados.get(f.get('id'), f.get('estado_factura', ESTADO_COMPROBANTE))
            f_copy['observacion'] = observaciones.get(f.get('id'), {}).get('observacion', '')
            facturas_con_estado.append(f_copy)
        
        facturas_con_estado.sort(key=lambda x: x.get('fecha_emision', ''), reverse=True)
        
        return jsonify({"ok": True, "facturas": facturas_con_estado})
    except Exception as e:
        print(f"[ERROR] api_obtener_facturas_lista: {e}")
        return jsonify({"ok": False, "error": str(e), "facturas": []})


def api_guardar_observacion():
    try:
        data = request.get_json()
        factura_id = data.get('factura_id')
        observacion = data.get('observacion', '')
        usuario = data.get('usuario', 'sistema')
        
        if not factura_id:
            return jsonify({"ok": False, "error": "Se requiere factura_id"})
        
        if not observacion:
            return jsonify({"ok": False, "error": "La observación no puede estar vacía"})
        
        guardar_observacion(factura_id, observacion, usuario)
        
        facturas = cargar_facturas()
        for f in facturas:
            if f.get('id') == factura_id:
                f['observacion'] = observacion
                break
        guardar_facturas(facturas)
        
        pedidos_facturacion = cargar_pedidos_facturacion()
        for p in pedidos_facturacion:
            if p.get('id') == factura_id or p.get('factura_id') == factura_id:
                p['observacion'] = observacion
                break
        guardar_pedidos_facturacion(pedidos_facturacion)
        
        if _registrar_bitacora:
            _registrar_bitacora(usuario, "Guardar Observación", f"Factura: {factura_id}", "Operaciones")
        
        notificar_actualizacion()
        
        return jsonify({"ok": True, "mensaje": "Observación guardada correctamente"})
    except Exception as e:
        print(f"[ERROR] api_guardar_observacion: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_obtener_observacion():
    try:
        factura_id = request.args.get('factura_id')
        if not factura_id:
            return jsonify({"ok": False, "error": "Se requiere factura_id", "observacion": ""})
        
        observacion = obtener_observacion(factura_id)
        
        if not observacion:
            pedidos_facturacion = cargar_pedidos_facturacion()
            for p in pedidos_facturacion:
                if p.get('id') == factura_id or p.get('factura_id') == factura_id:
                    observacion = p.get('observacion', '')
                    break
        
        return jsonify({"ok": True, "observacion": observacion})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "observacion": ""})


def api_obtener_estado_operaciones():
    try:
        estado = cargar_estado_operaciones()
        return jsonify({"ok": True, "estado": estado})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "estado": {}})


def api_guardar_asignacion():
    try:
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        asignacion = data.get('asignacion', {})
        
        if not pedido_id:
            return jsonify({"ok": False, "error": "Se requiere pedido_id"})
        
        guardar_asignacion_pedido(pedido_id, asignacion)
        
        pedidos = cargar_pedidos()
        for p in pedidos:
            if p.get('id') == pedido_id:
                for key, value in asignacion.items():
                    p[key] = value
                break
        guardar_pedidos(pedidos)
        
        pedidos_facturacion = cargar_pedidos_facturacion()
        for p in pedidos_facturacion:
            if p.get('id') == pedido_id:
                for key, value in asignacion.items():
                    p[key] = value
                break
        guardar_pedidos_facturacion(pedidos_facturacion)
        
        return jsonify({"ok": True, "mensaje": "Asignación guardada"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_cargar_asignacion():
    try:
        pedido_id = request.args.get('pedido_id')
        if not pedido_id:
            return jsonify({"ok": False, "error": "Se requiere pedido_id", "asignacion": {}})
        
        asignacion = cargar_asignacion_pedido(pedido_id)
        return jsonify({"ok": True, "asignacion": asignacion})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "asignacion": {}})


def api_guardar_pedido_seleccionado():
    try:
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        guardar_pedido_seleccionado(pedido_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_cargar_pedido_seleccionado():
    try:
        pedido_id = cargar_pedido_seleccionado()
        return jsonify({"ok": True, "pedido_id": pedido_id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "pedido_id": None})


def api_limpiar_datos_falsos():
    try:
        pedidos = cargar_pedidos()
        original_count = len(pedidos)
        
        fecha_limite = datetime.now() - timedelta(days=30)
        pedidos_limpios = []
        
        for p in pedidos:
            try:
                fecha_str = p.get('fecha_str', p.get('fecha', ''))
                if fecha_str:
                    fecha = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
                    if fecha >= fecha_limite:
                        pedidos_limpios.append(p)
            except:
                pedidos_limpios.append(p)
        
        guardar_pedidos(pedidos_limpios)
        
        return jsonify({
            "ok": True,
            "eliminados": original_count - len(pedidos_limpios),
            "restantes": len(pedidos_limpios)
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_pedidos_facturacion():
    try:
        pedidos_facturacion = cargar_pedidos_facturacion()
        return jsonify({"ok": True, "pedidos": pedidos_facturacion})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "pedidos": []})


def api_pedidos_camino():
    try:
        pedidos_camino = []
        
        facturas = cargar_facturas()
        for f in facturas:
            estado = f.get('estado_factura', f.get('estado_operacion', ''))
            if estado == ESTADO_CAMINO:
                pedidos_camino.append(f)
        
        pedidos_facturacion = cargar_pedidos_facturacion()
        for p in pedidos_facturacion:
            estado = p.get('estado_operacion', '')
            if estado == ESTADO_CAMINO:
                pedidos_camino.append(p)
        
        return jsonify({"ok": True, "pedidos": pedidos_camino})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "pedidos": []})


def api_pedidos_entregados():
    try:
        facturas = cargar_facturas()
        
        pedidos_entregados = []
        for f in facturas:
            estado = f.get('estado_factura', f.get('estado_operacion', ''))
            if estado == ESTADO_ENTREGADO:
                pedidos_entregados.append(f)
        
        return jsonify({"ok": True, "pedidos": pedidos_entregados})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "pedidos": []})


def api_crear_factura_desde_pedido():
    try:
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        
        if not pedido_id:
            return jsonify({"ok": False, "error": "Se requiere pedido_id"})
        
        pedidos_facturacion = cargar_pedidos_facturacion()
        pedido = None
        
        for p in pedidos_facturacion:
            if p.get('id') == pedido_id:
                pedido = p.copy()
                break
        
        if not pedido:
            return jsonify({"ok": False, "error": "Pedido no encontrado en cola de facturación"})
        
        factura_id = f"FAC-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"
        
        nueva_factura = {
            "id": factura_id,
            "pedido_id": pedido_id,
            "empresa_id": pedido.get('empresa_id', ''),
            "empresa_nombre": pedido.get('nombre', ''),
            "cedula": pedido.get('cedula', ''),
            "telefono": pedido.get('telefono', ''),
            "email": pedido.get('email', ''),
            "fecha_emision": datetime.now().isoformat(),
            "fecha_envio": datetime.now().isoformat(),
            "origen": pedido.get('origen', 'Managua'),
            "destino": pedido.get('destino', ''),
            "tipo_combustible": pedido.get('tipo_combustible', 'DIESEL'),
            "galones": pedido.get('galones', 0),
            "precio_por_galon": pedido.get('precio_por_galon', 0),
            "costo_combustible": pedido.get('costo_combustible', 0),
            "costo_traslado": pedido.get('costo_traslado', 0),
            "costo_total": pedido.get('costo_total', 0),
            "total": pedido.get('costo_total', 0),
            "conductor_asignado": pedido.get('conductor_asignado', ''),
            "conductor2_asignado": pedido.get('conductor2_asignado', ''),
            "camion_asignado": pedido.get('camion_asignado', ''),
            "camion2_asignado": pedido.get('camion2_asignado', ''),
            "estado_factura": ESTADO_CAMINO,
            "estado_operacion": ESTADO_CAMINO,
            "observacion": pedido.get('observacion', '')
        }
        
        facturas = cargar_facturas()
        facturas.append(nueva_factura)
        guardar_facturas(facturas)
        
        for p in pedidos_facturacion:
            if p.get('id') == pedido_id:
                p['estado_operacion'] = ESTADO_CAMINO
                p['factura_id'] = factura_id
                break
        guardar_pedidos_facturacion(pedidos_facturacion)
        
        estados = cargar_estados_facturas()
        estados[factura_id] = ESTADO_CAMINO
        estados[pedido_id] = ESTADO_CAMINO
        guardar_estados_facturas(estados)
        
        notificar_actualizacion()
        
        return jsonify({"ok": True, "mensaje": "Factura creada", "factura_id": factura_id})
    except Exception as e:
        print(f"[ERROR] api_crear_factura_desde_pedido: {e}")
        return jsonify({"ok": False, "error": str(e)})


# ==================== FUNCIÓN PARA NOTIFICAR ACTUALIZACIONES ====================
def notificar_actualizacion():
    try:
        import requests
        
        print("[DEBUG] Enviando notificaciones de actualización...")
        
        try:
            response = requests.post('http://localhost:5000/api/recepcion/forzar_actualizacion', json={}, timeout=2)
            if response.status_code == 200:
                print("[DEBUG] ✅ Notificación enviada a Recepción")
        except Exception as e:
            print(f"[WARN] No se pudo notificar a Recepción: {e}")
        
        try:
            response = requests.post('http://localhost:5000/api/reportes/recargar', json={}, timeout=2)
            if response.status_code == 200:
                print("[DEBUG] ✅ Notificación enviada a Reportes")
        except Exception as e:
            print(f"[WARN] No se pudo notificar a Reportes: {e}")
            
        # Notificar a Facturación vía mensaje
        try:
            response = requests.post('http://localhost:5000/api/notificar_pedido_facturacion', json={"pedido_id": "actualizacion", "estado": "actualizado"}, timeout=2)
            if response.status_code == 200:
                print("[DEBUG] ✅ Notificación enviada a Facturación")
        except Exception as e:
            print(f"[WARN] No se pudo notificar a Facturación: {e}")
            
    except Exception as e:
        print(f"[WARN] Error general notificando actualización: {e}")


# ==================== RUTAS ADICIONALES PARA OBTENER DATOS ====================
def api_obtener_bonos_viaticos_directo():
    """API para obtener bonos y viáticos directamente desde Gestión Clientes"""
    try:
        cliente_id = request.args.get('cliente_id')
        if not cliente_id:
            return jsonify({"ok": False, "error": "Se requiere cliente_id"})
        
        bono1, bono2, viatico1, viatico2 = obtener_bonos_viaticos_empresa(cliente_id)
        
        return jsonify({
            "ok": True,
            "bono1": bono1,
            "bono2": bono2,
            "viatico1": viatico1,
            "viatico2": viatico2,
            "cliente_id": cliente_id
        })
    except Exception as e:
        print(f"[ERROR] api_obtener_bonos_viaticos_directo: {e}")
        return jsonify({"ok": False, "error": str(e)})