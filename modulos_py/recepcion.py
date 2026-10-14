# ==================== MÓDULO RECEPCIÓN ====================
import os
import json
from datetime import datetime, timedelta
from flask import jsonify, request

# ==================== CONFIGURACIÓN ====================
ARCHIVO_PEDIDOS = None
ARCHIVO_FACTURAS = None
ARCHIVO_PEDIDOS_FACTURACION = None
ARCHIVO_ESTADOS_FACTURAS = None
ARCHIVO_OBSERVACIONES = None

_cargar_json = None
_guardar_json = None

# Estados de operación
ESTADO_ESPERA = 'espera'
ESTADO_COMPROBANTE = 'comprobante'
ESTADO_CAMINO = 'camino'
ESTADO_ENTREGADO = 'entregado'
ESTADO_FACTURACION = 'facturacion'


# ==================== INICIALIZACIÓN ====================
def inicializar_recepcion(pedidos_path, facturas_path, cargar_json_func, guardar_json_func, pedidos_facturacion_path=None):
    global ARCHIVO_PEDIDOS, ARCHIVO_FACTURAS, ARCHIVO_PEDIDOS_FACTURACION
    global _cargar_json, _guardar_json, ARCHIVO_OBSERVACIONES, ARCHIVO_ESTADOS_FACTURAS
    
    ARCHIVO_PEDIDOS = pedidos_path
    ARCHIVO_FACTURAS = facturas_path
    ARCHIVO_PEDIDOS_FACTURACION = pedidos_facturacion_path
    _cargar_json = cargar_json_func
    _guardar_json = guardar_json_func
    
    # Directorio base para estados
    base_dir = os.path.dirname(pedidos_path) if pedidos_path else "datos"
    ARCHIVO_ESTADOS_FACTURAS = os.path.join(base_dir, "estados_facturas.json")
    ARCHIVO_OBSERVACIONES = os.path.join(base_dir, "observaciones.json")
    
    print(f"[INFO] Módulo Recepción inicializado")
    print(f"[INFO] Archivo pedidos: {ARCHIVO_PEDIDOS}")
    print(f"[INFO] Archivo facturas: {ARCHIVO_FACTURAS}")
    print(f"[INFO] Archivo pedidos_facturacion: {ARCHIVO_PEDIDOS_FACTURACION}")
    print(f"[INFO] Archivo estados: {ARCHIVO_ESTADOS_FACTURAS}")


def cargar_estados_facturas():
    """Carga los estados de las facturas"""
    try:
        if ARCHIVO_ESTADOS_FACTURAS and os.path.exists(ARCHIVO_ESTADOS_FACTURAS):
            with open(ARCHIVO_ESTADOS_FACTURAS, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}


def guardar_estados_facturas(estados):
    """Guarda los estados de las facturas"""
    try:
        if ARCHIVO_ESTADOS_FACTURAS:
            with open(ARCHIVO_ESTADOS_FACTURAS, 'w', encoding='utf-8') as f:
                json.dump(estados, f, indent=2, ensure_ascii=False)
            return True
    except:
        pass
    return False


def cargar_observaciones():
    """Carga las observaciones"""
    try:
        if ARCHIVO_OBSERVACIONES and os.path.exists(ARCHIVO_OBSERVACIONES):
            with open(ARCHIVO_OBSERVACIONES, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}


def cargar_pedidos():
    """Carga los pedidos pendientes desde pedidos_combustible.json"""
    try:
        if ARCHIVO_PEDIDOS and os.path.exists(ARCHIVO_PEDIDOS):
            with open(ARCHIVO_PEDIDOS, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
                if isinstance(data, list):
                    return [item for item in data if isinstance(item, dict)]
                elif isinstance(data, dict) and "pedidos" in data:
                    return [item for item in data["pedidos"] if isinstance(item, dict)]
                return []
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON inválido en {ARCHIVO_PEDIDOS}: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] cargar_pedidos: {e}")
    return []


def guardar_pedidos(pedidos):
    """Guarda pedidos en pedidos_combustible.json"""
    if _guardar_json:
        return _guardar_json(ARCHIVO_PEDIDOS, pedidos)
    try:
        with open(ARCHIVO_PEDIDOS, 'w', encoding='utf-8') as f:
            json.dump(pedidos, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] guardar_pedidos: {e}")
        return False


def cargar_facturas():
    """Carga las facturas desde facturas_combustible.json"""
    try:
        if ARCHIVO_FACTURAS and os.path.exists(ARCHIVO_FACTURAS):
            with open(ARCHIVO_FACTURAS, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
                
                # Manejar formato {"facturas": [...]}
                if isinstance(data, dict) and "facturas" in data:
                    facturas = data["facturas"]
                    if isinstance(facturas, list):
                        return [f for f in facturas if isinstance(f, dict)]
                    return []
                # Manejar formato directo de lista
                elif isinstance(data, list):
                    return [f for f in data if isinstance(f, dict)]
                return []
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON inválido en {ARCHIVO_FACTURAS}: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] cargar_facturas: {e}")
    return []


def guardar_facturas(facturas):
    """Guarda las facturas en facturas_combustible.json"""
    try:
        if ARCHIVO_FACTURAS:
            if not isinstance(facturas, list):
                facturas = []
            data = {"facturas": facturas}
            with open(ARCHIVO_FACTURAS, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
    except Exception as e:
        print(f"[ERROR] guardar_facturas: {e}")
    return False


def cargar_pedidos_facturacion():
    """Carga los pedidos desde la cola de facturación"""
    try:
        if ARCHIVO_PEDIDOS_FACTURACION and os.path.exists(ARCHIVO_PEDIDOS_FACTURACION):
            with open(ARCHIVO_PEDIDOS_FACTURACION, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
                if isinstance(data, list):
                    return [item for item in data if isinstance(item, dict)]
                return []
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON inválido en {ARCHIVO_PEDIDOS_FACTURACION}: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] cargar_pedidos_facturacion: {e}")
    return []


def guardar_pedidos_facturacion(pedidos):
    """Guarda pedidos en pedidos_facturacion.json"""
    if ARCHIVO_PEDIDOS_FACTURACION is None:
        return False
    try:
        if not isinstance(pedidos, list):
            pedidos = []
        with open(ARCHIVO_PEDIDOS_FACTURACION, 'w', encoding='utf-8') as f:
            json.dump(pedidos, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] guardar_pedidos_facturacion: {e}")
        return False


def convertir_factura_a_pedido(factura):
    """Convierte una factura a formato pedido para Recepción"""
    if not isinstance(factura, dict):
        return {}
    
    # Extraer el primer pedido del array 'pedidos' si existe
    pedido_data = {}
    if 'pedidos' in factura and isinstance(factura['pedidos'], list) and len(factura['pedidos']) > 0:
        pedido_data = factura['pedidos'][0]
    
    return {
        "id": pedido_data.get('id', factura.get('id', '')),
        "factura_id": factura.get('id', ''),
        "pedido_id": pedido_data.get('id', factura.get('pedido_id', '')),
        "empresa_id": pedido_data.get('empresa_id', factura.get('empresa_id', '')),
        "nombre": pedido_data.get('nombre', factura.get('empresa_nombre', 'Cliente')),
        "cedula": pedido_data.get('cedula', factura.get('empresa_nit', '')),
        "telefono": pedido_data.get('telefono', factura.get('empresa_telefono_cliente', '')),
        "email": pedido_data.get('email', ''),
        "fecha": pedido_data.get('fecha', factura.get('fecha_emision', factura.get('fecha_recepcion', datetime.now().isoformat()))),
        "fecha_str": pedido_data.get('fecha_str', factura.get('fecha_emision', factura.get('fecha_recepcion', '')))[:10] if factura.get('fecha_emision') or factura.get('fecha_recepcion') else datetime.now().strftime("%Y-%m-%d"),
        "fecha_entrega": factura.get('fecha_entrega', ''),
        "fecha_envio": factura.get('fecha_envio', factura.get('fecha_emision', '')),
        "origen": pedido_data.get('origen', factura.get('origen', 'Managua')),
        "destino": pedido_data.get('destino', factura.get('destino', '')),
        "tipo_combustible": pedido_data.get('tipo_combustible', factura.get('tipo_combustible', 'DIESEL')),
        "galones": pedido_data.get('galones', factura.get('galones', 0)),
        "precio_por_galon": pedido_data.get('precio_por_galon', factura.get('precio_por_galon', 0)),
        "costo_combustible": pedido_data.get('costo_combustible', factura.get('costo_combustible', 0)),
        "costo_traslado": pedido_data.get('costo_traslado', factura.get('costo_traslado', 0)),
        "costo_total": pedido_data.get('costo_total', factura.get('total', 0)),
        "importe": pedido_data.get('importe', factura.get('total', 0)),
        "estado_operacion": factura.get('estado_factura', factura.get('estado_operacion', ESTADO_CAMINO)),
        "conductor_asignado": pedido_data.get('conductor_asignado', factura.get('conductor_asignado', '')),
        "conductor2_asignado": pedido_data.get('conductor2_asignado', factura.get('conductor2_asignado', '')),
        "camion_asignado": pedido_data.get('camion_asignado', factura.get('camion_asignado', '')),
        "camion2_asignado": pedido_data.get('camion2_asignado', factura.get('camion2_asignado', '')),
        "observacion": factura.get('observacion', ''),
        "bono1": factura.get('bono1', ''),
        "bono2": factura.get('bono2', ''),
        "viatico1": factura.get('viatico1', 0),
        "viatico2": factura.get('viatico2', 0),
        "filas": factura.get('filas', pedido_data.get('filas', []))
    }


def cargar_pedidos_camino():
    """Carga los pedidos en camino desde:
    1. facturas_combustible.json (estado 'camino')
    2. pedidos_facturacion.json (estado 'camino')
    """
    try:
        pedidos_camino = []
        
        # 1. Buscar en facturas_combustible.json
        facturas = cargar_facturas()
        if isinstance(facturas, list):
            for factura in facturas:
                if isinstance(factura, dict):
                    estado = factura.get('estado_factura', factura.get('estado_operacion', ''))
                    if estado == ESTADO_CAMINO:
                        pedido_convertido = convertir_factura_a_pedido(factura)
                        if pedido_convertido and pedido_convertido.get('id'):
                            pedidos_camino.append(pedido_convertido)
        
        # 2. Buscar en pedidos_facturacion.json
        pedidos_facturacion = cargar_pedidos_facturacion()
        if isinstance(pedidos_facturacion, list):
            for p in pedidos_facturacion:
                if isinstance(p, dict):
                    estado = p.get('estado_operacion', p.get('estado', ''))
                    if estado == ESTADO_CAMINO:
                        p['estado_operacion'] = ESTADO_CAMINO
                        pedidos_camino.append(p)
        
        print(f"[DEBUG] Pedidos en camino: {len(pedidos_camino)}")
        return pedidos_camino
    except Exception as e:
        print(f"[ERROR] cargar_pedidos_camino: {e}")
        import traceback
        traceback.print_exc()
        return []


def cargar_pedidos_entregados():
    """Carga los pedidos entregados desde facturas_combustible.json"""
    try:
        pedidos_entregados = []
        facturas = cargar_facturas()
        
        if isinstance(facturas, list):
            for factura in facturas:
                if isinstance(factura, dict):
                    estado = factura.get('estado_factura', factura.get('estado_operacion', ''))
                    if estado == ESTADO_ENTREGADO:
                        pedido_convertido = convertir_factura_a_pedido(factura)
                        if pedido_convertido and pedido_convertido.get('id'):
                            pedidos_entregados.append(pedido_convertido)
        
        print(f"[DEBUG] Pedidos entregados: {len(pedidos_entregados)}")
        return pedidos_entregados
    except Exception as e:
        print(f"[ERROR] cargar_pedidos_entregados: {e}")
        return []


# ==================== API ENDPOINTS ====================
def api_pedidos_recientes():
    """Obtiene los pedidos recientes (últimos 30 días)"""
    try:
        # Cargar desde múltiples fuentes
        pedidos_pendientes = cargar_pedidos()
        pedidos_camino = cargar_pedidos_camino()
        pedidos_entregados = cargar_pedidos_entregados()
        
        # Combinar todos
        todos_pedidos = pedidos_pendientes + pedidos_camino + pedidos_entregados
        
        estados = cargar_estados_facturas()
        observaciones = cargar_observaciones()
        
        # Enriquecer pedidos con estados y observaciones
        for p in todos_pedidos:
            factura_id = p.get('factura_id', p.get('id', ''))
            
            # Estado
            if factura_id and factura_id in estados:
                p['estado_operacion'] = estados[factura_id]
            elif p.get('id') in estados:
                p['estado_operacion'] = estados[p.get('id')]
            
            # Observación
            if factura_id in observaciones:
                p['observacion'] = observaciones[factura_id].get('observacion', '')
            elif p.get('id') in observaciones:
                p['observacion'] = observaciones[p.get('id')].get('observacion', '')
        
        # Ordenar por fecha (más recientes primero)
        todos_pedidos.sort(key=lambda x: x.get('fecha', ''), reverse=True)
        
        # Limitar a los últimos 30 días
        fecha_limite = datetime.now() - timedelta(days=30)
        pedidos_recientes = []
        for p in todos_pedidos:
            try:
                fecha_str = p.get('fecha_str', p.get('fecha', ''))
                if fecha_str:
                    fecha = datetime.fromisoformat(fecha_str) if 'T' in fecha_str else datetime.strptime(fecha_str[:10], "%Y-%m-%d")
                    if fecha >= fecha_limite:
                        pedidos_recientes.append(p)
                else:
                    pedidos_recientes.append(p)
            except:
                pedidos_recientes.append(p)
        
        return jsonify({"ok": True, "pedidos": pedidos_recientes[:100]})
    except Exception as e:
        print(f"[ERROR] api_pedidos_recientes: {e}")
        return jsonify({"ok": False, "error": str(e), "pedidos": []})


def api_estadisticas_recepcion():
    """Obtiene estadísticas para Recepción (incluyendo en camino y entregados desde facturas)"""
    try:
        # Cargar desde múltiples fuentes
        pedidos_pendientes = cargar_pedidos()
        pedidos_camino = cargar_pedidos_camino()
        pedidos_entregados = cargar_pedidos_entregados()
        
        pendientes = len(pedidos_pendientes)
        camino = len(pedidos_camino)
        entregados = len(pedidos_entregados)
        
        # Calcular totales
        total_costo = sum(p.get('costo_total', p.get('costo_combustible', 0)) for p in pedidos_pendientes)
        total_galones = sum(p.get('galones', 0) for p in pedidos_pendientes)
        
        print(f"[DEBUG] Estadísticas - Pendientes: {pendientes}, Camino: {camino}, Entregados: {entregados}")
        
        return jsonify({
            "ok": True,
            "estadisticas": {
                "pendientes": pendientes,
                "camino": camino,
                "entregados": entregados,
                "total_pedidos": pendientes + camino + entregados,
                "total_costo": total_costo,
                "total_galones": total_galones
            }
        })
    except Exception as e:
        print(f"[ERROR] api_estadisticas_recepcion: {e}")
        return jsonify({"ok": False, "error": str(e), "estadisticas": {}})


def api_datos_graficas():
    """Obtiene datos para gráficas"""
    try:
        # Cargar desde múltiples fuentes
        pedidos_pendientes = cargar_pedidos()
        pedidos_camino = cargar_pedidos_camino()
        pedidos_entregados = cargar_pedidos_entregados()
        
        todos_pedidos = pedidos_pendientes + pedidos_camino + pedidos_entregados
        
        # Costo por mes
        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        costos_por_mes = [0] * 12
        pedidos_por_mes = [0] * 12
        
        # Distribución por tipo de combustible
        tipos = {}
        
        for p in todos_pedidos:
            try:
                fecha = p.get('fecha', '')
                if fecha:
                    if 'T' in fecha:
                        mes = datetime.fromisoformat(fecha).month - 1
                    else:
                        mes = datetime.strptime(fecha[:10], "%Y-%m-%d").month - 1
                    costo = p.get('costo_total', p.get('costo_combustible', 0))
                    costos_por_mes[mes] += costo
                    pedidos_por_mes[mes] += 1
                
                tipo = p.get('tipo_combustible', 'Otro')
                tipos[tipo] = tipos.get(tipo, 0) + 1
            except Exception as e:
                print(f"[WARN] Error procesando pedido: {e}")
        
        return jsonify({
            "ok": True,
            "datos": {
                "costos_mensuales": {
                    "labels": meses,
                    "data": costos_por_mes
                },
                "pedidos_mensuales": {
                    "labels": meses,
                    "data": pedidos_por_mes
                },
                "tipos_combustible": {
                    "labels": list(tipos.keys()),
                    "data": list(tipos.values())
                }
            }
        })
    except Exception as e:
        print(f"[ERROR] api_datos_graficas: {e}")
        return jsonify({"ok": False, "error": str(e), "datos": {}})


def api_forzar_actualizacion():
    """Fuerza la actualización de Recepción"""
    try:
        print("[DEBUG] Forzando actualización de Recepción")
        return jsonify({"ok": True, "mensaje": "Actualización forzada"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_obtener_pedidos_actualizados():
    """Obtiene todos los pedidos con estados actualizados (pendientes, en camino, entregados)"""
    try:
        # 1. Cargar pedidos PENDIENTES (estado 'espera') desde pedidos_combustible.json
        pedidos_pendientes = cargar_pedidos()
        
        # 2. Cargar pedidos EN CAMINO desde facturas y cola de facturación
        pedidos_camino = cargar_pedidos_camino()
        
        # 3. Cargar pedidos ENTREGADOS desde facturas_combustible.json
        pedidos_entregados = cargar_pedidos_entregados()
        
        # 4. Cargar observaciones
        observaciones = cargar_observaciones()
        
        print(f"[DEBUG] Fuentes - Pendientes: {len(pedidos_pendientes)}, Camino: {len(pedidos_camino)}, Entregados: {len(pedidos_entregados)}")
        
        todos_pedidos = []
        
        # Procesar pedidos pendientes
        for p in pedidos_pendientes:
            p_copy = p.copy() if isinstance(p, dict) else {}
            if not p_copy:
                continue
                
            p_copy['estado_operacion'] = ESTADO_ESPERA
            
            # Agregar observación
            factura_id = p_copy.get('factura_id', p_copy.get('id', ''))
            if factura_id in observaciones:
                p_copy['observacion'] = observaciones[factura_id].get('observacion', '')
            elif p_copy.get('id') in observaciones:
                p_copy['observacion'] = observaciones[p_copy.get('id')].get('observacion', '')
            
            # Asegurar campos necesarios
            if 'costo_total' not in p_copy:
                p_copy['costo_total'] = p_copy.get('importe', p_copy.get('costo_combustible', 0))
            
            if 'fecha_str' not in p_copy and 'fecha' in p_copy:
                try:
                    fecha_str = p_copy['fecha']
                    if 'T' in fecha_str:
                        fecha = datetime.fromisoformat(fecha_str)
                    else:
                        fecha = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
                    p_copy['fecha_str'] = fecha.strftime("%Y-%m-%d")
                except:
                    p_copy['fecha_str'] = datetime.now().strftime("%Y-%m-%d")
            
            # Asegurar campos de contacto
            if 'cedula' not in p_copy:
                p_copy['cedula'] = ''
            if 'telefono' not in p_copy:
                p_copy['telefono'] = ''
            if 'email' not in p_copy:
                p_copy['email'] = ''
            
            todos_pedidos.append(p_copy)
        
        # Procesar pedidos en camino
        for p in pedidos_camino:
            if not isinstance(p, dict):
                continue
            p['estado_operacion'] = ESTADO_CAMINO
            
            # Agregar observación si existe
            factura_id = p.get('factura_id', p.get('id', ''))
            if factura_id in observaciones:
                p['observacion'] = observaciones[factura_id].get('observacion', '')
            elif p.get('id') in observaciones:
                p['observacion'] = observaciones[p.get('id')].get('observacion', '')
            
            todos_pedidos.append(p)
        
        # Procesar pedidos entregados - AHORA SÍ SE AGREGARÁN
        for p in pedidos_entregados:
            if not isinstance(p, dict):
                continue
            p['estado_operacion'] = ESTADO_ENTREGADO
            factura_id = p.get('factura_id', p.get('id', ''))
            if factura_id in observaciones:
                p['observacion'] = observaciones[factura_id].get('observacion', '')
            # AGREGAR pedidos entregados a la lista
            todos_pedidos.append(p)
        
        # Ordenar por fecha (más recientes primero)
        todos_pedidos.sort(key=lambda x: x.get('fecha', ''), reverse=True)
        
        # Estadísticas para debug
        pendientes = len(pedidos_pendientes)
        camino = len(pedidos_camino)
        entregados = len(pedidos_entregados)
        
        print(f"[DEBUG] RESULTADO FINAL - Total: {len(todos_pedidos)} | Pendientes: {pendientes} | En Camino: {camino} | Entregados: {entregados}")
        
        return jsonify({
            "ok": True, 
            "pedidos": todos_pedidos,
            "pendientes": pendientes,
            "camino": camino,
            "entregados": entregados,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"[ERROR] api_obtener_pedidos_actualizados: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e), "pedidos": []})


def api_obtener_pedidos_pendientes():
    """Obtiene solo los pedidos pendientes (para Recepción)"""
    try:
        pedidos = cargar_pedidos()
        observaciones = cargar_observaciones()
        
        pedidos_con_observacion = []
        for p in pedidos:
            if not isinstance(p, dict):
                continue
            p_copy = p.copy()
            factura_id = p_copy.get('factura_id', p_copy.get('id', ''))
            
            if factura_id in observaciones:
                p_copy['observacion'] = observaciones[factura_id].get('observacion', '')
            elif p_copy.get('id') in observaciones:
                p_copy['observacion'] = observaciones[p_copy.get('id')].get('observacion', '')
            
            # Asegurar campos
            if 'costo_total' not in p_copy:
                p_copy['costo_total'] = p_copy.get('importe', p_copy.get('costo_combustible', 0))
            
            pedidos_con_observacion.append(p_copy)
        
        pedidos_con_observacion.sort(key=lambda x: x.get('fecha', ''), reverse=True)
        
        return jsonify({"ok": True, "pedidos": pedidos_con_observacion})
    except Exception as e:
        print(f"[ERROR] api_obtener_pedidos_pendientes: {e}")
        return jsonify({"ok": False, "error": str(e), "pedidos": []})


def api_obtener_pedidos_camino():
    """Obtiene solo los pedidos en camino"""
    try:
        pedidos_camino = cargar_pedidos_camino()
        observaciones = cargar_observaciones()
        
        for p in pedidos_camino:
            if not isinstance(p, dict):
                continue
            factura_id = p.get('factura_id', p.get('id', ''))
            if factura_id in observaciones:
                p['observacion'] = observaciones[factura_id].get('observacion', '')
        
        return jsonify({"ok": True, "pedidos": pedidos_camino})
    except Exception as e:
        print(f"[ERROR] api_obtener_pedidos_camino: {e}")
        return jsonify({"ok": False, "error": str(e), "pedidos": []})


def api_obtener_pedidos_entregados():
    """Obtiene solo los pedidos entregados"""
    try:
        pedidos_entregados = cargar_pedidos_entregados()
        observaciones = cargar_observaciones()
        
        for p in pedidos_entregados:
            if not isinstance(p, dict):
                continue
            factura_id = p.get('factura_id', p.get('id', ''))
            if factura_id in observaciones:
                p['observacion'] = observaciones[factura_id].get('observacion', '')
        
        return jsonify({"ok": True, "pedidos": pedidos_entregados})
    except Exception as e:
        print(f"[ERROR] api_obtener_pedidos_entregados: {e}")
        return jsonify({"ok": False, "error": str(e), "pedidos": []})


def api_obtener_observacion():
    """Obtiene observación de un pedido"""
    try:
        factura_id = request.args.get('factura_id')
        if not factura_id:
            return jsonify({"ok": False, "error": "Se requiere factura_id", "observacion": ""})
        
        observaciones = cargar_observaciones()
        if factura_id in observaciones:
            return jsonify({"ok": True, "observacion": observaciones[factura_id].get('observacion', '')})
        
        # Buscar por ID alternativo
        for key, value in observaciones.items():
            if key == factura_id or key.replace('FAC-', '') == factura_id or key.replace('PED-', '') == factura_id:
                return jsonify({"ok": True, "observacion": value.get('observacion', '')})
        
        return jsonify({"ok": True, "observacion": ""})
    except Exception as e:
        print(f"[ERROR] api_obtener_observacion: {e}")
        return jsonify({"ok": False, "error": str(e), "observacion": ""})


def api_obtener_todas_observaciones():
    """Obtiene todas las observaciones"""
    try:
        observaciones = cargar_observaciones()
        return jsonify({"ok": True, "observaciones": observaciones})
    except Exception as e:
        print(f"[ERROR] api_obtener_todas_observaciones: {e}")
        return jsonify({"ok": False, "error": str(e), "observaciones": {}})