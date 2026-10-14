# ==================== MODULO TABLAS EDITABLES ====================
from flask import jsonify, request, send_file
import json
import os
from datetime import datetime

# Archivo para persistencia de tablas editables
TABLAS_EDITABLES_FILE = None

def inicializar_tablas_editables(ruta_archivo):
    """Inicializa el modulo con la ruta del archivo de persistencia"""
    global TABLAS_EDITABLES_FILE
    TABLAS_EDITABLES_FILE = ruta_archivo
    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
    if not os.path.exists(ruta_archivo):
        guardar_tablas_en_archivo({
            "empresas": [], 
            "pedidos": [], 
            "pedidos_camino": [],
            "pedidos_entregados": [],
            "costos": [], 
            "conductores": [], 
            "camiones": [], 
            "facturas": [],
            "reportes": [],
            "ultima_actualizacion": datetime.now().isoformat(),
            "fecha_creacion": datetime.now().isoformat(),
            "version": "2.0"
        })
    print(f"[INFO] Tablas editables inicializadas en: {ruta_archivo}")


def cargar_tablas_desde_archivo():
    """Carga los datos desde el archivo JSON con fallback a fuentes originales"""
    try:
        if TABLAS_EDITABLES_FILE and os.path.exists(TABLAS_EDITABLES_FILE):
            with open(TABLAS_EDITABLES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                keys_requeridas = ["reportes", "empresas", "pedidos", "pedidos_camino", "pedidos_entregados", "costos", "conductores", "camiones", "facturas"]
                for key in keys_requeridas:
                    if key not in data:
                        data[key] = []
                
                # Asegurar campos de fecha
                if "fecha_creacion" not in data:
                    data["fecha_creacion"] = datetime.now().isoformat()
                if "version" not in data:
                    data["version"] = "2.0"
                
                tiene_datos_camino = len(data.get('pedidos_camino', [])) > 0
                tiene_datos_entregados = len(data.get('pedidos_entregados', [])) > 0
                
                print(f"[DEBUG] Datos en bitácora: Camino={len(data.get('pedidos_camino', []))}, Entregados={len(data.get('pedidos_entregados', []))}")
                print(f"[DEBUG] Fecha creación: {data.get('fecha_creacion', 'N/A')}")
                print(f"[DEBUG] Última actualización: {data.get('ultima_actualizacion', 'N/A')}")
                
                if not tiene_datos_camino and not tiene_datos_entregados:
                    print("[INFO] Bitácora vacía, intentando sincronizar desde fuentes...")
                    data = sincronizar_desde_fuentes(data)
                
                return data
        else:
            data = {
                "empresas": [], 
                "pedidos": [], 
                "pedidos_camino": [], 
                "pedidos_entregados": [], 
                "costos": [], 
                "conductores": [], 
                "camiones": [], 
                "facturas": [], 
                "reportes": [],
                "ultima_actualizacion": datetime.now().isoformat(),
                "fecha_creacion": datetime.now().isoformat(),
                "version": "2.0"
            }
            guardar_tablas_en_archivo(data)
            print("[INFO] Archivo de bitácora creado vacío")
            data = sincronizar_desde_fuentes(data)
            return data
            
    except Exception as e:
        print(f"[ERROR] cargar_tablas_desde_archivo: {e}")
        import traceback
        traceback.print_exc()
    
    return {
        "empresas": [], 
        "pedidos": [], 
        "pedidos_camino": [], 
        "pedidos_entregados": [], 
        "costos": [], 
        "conductores": [], 
        "camiones": [], 
        "facturas": [], 
        "reportes": [],
        "ultima_actualizacion": datetime.now().isoformat(),
        "fecha_creacion": datetime.now().isoformat(),
        "version": "2.0"
    }


def agregar_fechas_a_registro(registro):
    """Agrega campos de fecha a un registro si no existen"""
    ahora = datetime.now().isoformat()
    
    # Fecha de creación
    if "fecha_creacion" not in registro:
        registro["fecha_creacion"] = ahora
    
    # Fecha de actualización (siempre se actualiza)
    registro["fecha_actualizacion"] = ahora
    
    # Fecha/hora legible
    if "fecha_hora" not in registro:
        registro["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return registro


def sincronizar_desde_fuentes(data):
    """Sincroniza datos desde las fuentes originales con todos los detalles y fechas"""
    try:
        from main import (ARCHIVO_FACTURAS, ARCHIVO_ESTADOS_FACTURAS, ARCHIVO_PEDIDOS_FACTURACION, 
                         ARCHIVO_PEDIDOS, cargar_json, ARCHIVO_EMPRESAS, ARCHIVO_CONDUCTORES, 
                         ARCHIVO_CAMIONES, ARCHIVO_COSTOS_TRASLADO, ARCHIVO_REPORTES_DATA, ARCHIVO_CLIENTES)
        
        print("[INFO] Sincronizando desde fuentes originales...")
        ahora = datetime.now().isoformat()
        
        # ========== SINCRONIZAR EMPRESAS ==========
        clientes = cargar_clientes_desde_gestion()
        if clientes:
            empresas_con_fechas = []
            for c in clientes:
                if "fecha_creacion" not in c:
                    c["fecha_creacion"] = c.get("fecha_registro", ahora)
                c["fecha_actualizacion"] = ahora
                c["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                empresas_con_fechas.append(c)
            data['empresas'] = empresas_con_fechas
            print(f"[DEBUG] Sincronizados {len(empresas_con_fechas)} clientes desde Gestión Clientes")
        else:
            empresas = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
            empresas_lista = empresas.get('empresas', [])
            if empresas_lista:
                empresas_con_fechas = []
                for e in empresas_lista:
                    if "fecha_creacion" not in e:
                        e["fecha_creacion"] = e.get("fecha_registro", ahora)
                    e["fecha_actualizacion"] = ahora
                    e["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    empresas_con_fechas.append(e)
                data['empresas'] = empresas_con_fechas
                print(f"[DEBUG] Sincronizadas {len(empresas_con_fechas)} empresas desde empresas.json")
        
        # ========== SINCRONIZAR PEDIDOS ==========
        pedidos = cargar_json(ARCHIVO_PEDIDOS, [])
        if pedidos:
            pedidos_con_fechas = []
            for p in pedidos:
                if "fecha_creacion" not in p:
                    p["fecha_creacion"] = p.get("fecha", ahora)
                p["fecha_actualizacion"] = ahora
                p["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                empresa_id = p.get('empresa_id', '')
                if empresa_id:
                    datos_cliente = obtener_bonos_viaticos_cliente(empresa_id)
                    if not p.get('bono1') and datos_cliente.get('bono1'):
                        p['bono1'] = datos_cliente.get('bono1')
                    if not p.get('bono2') and datos_cliente.get('bono2'):
                        p['bono2'] = datos_cliente.get('bono2')
                    if not p.get('viatico1') and datos_cliente.get('viatico1'):
                        p['viatico1'] = datos_cliente.get('viatico1')
                    if not p.get('viatico2') and datos_cliente.get('viatico2'):
                        p['viatico2'] = datos_cliente.get('viatico2')
                pedidos_con_fechas.append(p)
            data['pedidos'] = pedidos_con_fechas
            print(f"[DEBUG] Sincronizados {len(pedidos_con_fechas)} pedidos pendientes")
        
        # ========== SINCRONIZAR CONDUCTORES ==========
        conductores = cargar_json(ARCHIVO_CONDUCTORES, {"conductores": []})
        conductores_lista = conductores.get('conductores', [])
        if conductores_lista:
            conductores_con_fechas = []
            for c in conductores_lista:
                if "fecha_creacion" not in c:
                    c["fecha_creacion"] = c.get("fecha_registro", ahora)
                c["fecha_actualizacion"] = ahora
                c["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conductores_con_fechas.append(c)
            data['conductores'] = conductores_con_fechas
            print(f"[DEBUG] Sincronizados {len(conductores_con_fechas)} conductores")
        
        # ========== SINCRONIZAR CAMIONES ==========
        camiones = cargar_json(ARCHIVO_CAMIONES, {"camiones": []})
        camiones_lista = camiones.get('camiones', [])
        if camiones_lista:
            camiones_con_fechas = []
            for c in camiones_lista:
                if "fecha_creacion" not in c:
                    c["fecha_creacion"] = c.get("fecha_registro", ahora)
                c["fecha_actualizacion"] = ahora
                c["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                camiones_con_fechas.append(c)
            data['camiones'] = camiones_con_fechas
            print(f"[DEBUG] Sincronizados {len(camiones_con_fechas)} camiones")
        
        # ========== SINCRONIZAR COSTOS ==========
        costos = cargar_json(ARCHIVO_COSTOS_TRASLADO, {"costos": []})
        costos_lista = costos.get('costos', [])
        if costos_lista:
            costos_con_fechas = []
            for c in costos_lista:
                if "fecha_creacion" not in c:
                    c["fecha_creacion"] = ahora
                c["fecha_actualizacion"] = ahora
                c["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                costos_con_fechas.append(c)
            data['costos'] = costos_con_fechas
            print(f"[DEBUG] Sincronizados {len(costos_con_fechas)} costos")
        
        # ========== SINCRONIZAR FACTURAS Y PEDIDOS EN CAMINO/ENTREGADOS ==========
        facturas_data = cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
        facturas_lista = facturas_data.get('facturas', [])
        estados_facturas = cargar_json(ARCHIVO_ESTADOS_FACTURAS, {})
        
        pedidos_camino = []
        pedidos_entregados = []
        facturas_con_fechas = []
        
        print(f"[DEBUG] Procesando {len(facturas_lista)} facturas para clasificar estados...")
        
        for f in facturas_lista:
            if "fecha_creacion" not in f:
                f["fecha_creacion"] = f.get("fecha_emision", ahora)
            f["fecha_actualizacion"] = ahora
            f["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            facturas_con_fechas.append(f)
            
            factura_id = f.get('id', '')
            estado = estados_facturas.get(factura_id, '')
            if not estado:
                estado = f.get('estado_factura', '')
            if not estado:
                estado = f.get('estado_operacion', '')
            if not estado and f.get('entregado', False):
                estado = 'entregado'
            if not estado:
                estado = 'comprobante'
            
            if estado == 'camino' or estado == 'entregado':
                empresa_id = f.get('empresa_id', '')
                datos_cliente = obtener_bonos_viaticos_cliente(empresa_id)
                
                fecha_emision = f.get('fecha_emision', f.get('fecha', ''))
                fecha_str = f.get('fecha_emision_str', f.get('fecha_str', ''))
                if fecha_emision and 'T' in fecha_emision:
                    fecha_emision = fecha_emision[:19]
                if fecha_str and 'T' in fecha_str:
                    fecha_str = fecha_str[:19]
                
                item = {
                    "id": factura_id,
                    "factura_id": factura_id,
                    "pedido_id": f.get('pedido_id', ''),
                    "empresa_id": empresa_id,
                    "nombre": f.get('empresa_nombre', f.get('nombre', datos_cliente.get('nombre', 'Cliente'))),
                    "fecha": fecha_emision,
                    "fecha_str": fecha_str,
                    "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "fecha_creacion": f.get("fecha_creacion", ahora),
                    "fecha_actualizacion": ahora,
                    "galones": f.get('galones', 0),
                    "precio_por_galon": f.get('precio_por_galon', 0),
                    "total": f.get('total', f.get('costo_total', 0)),
                    "conductor_asignado": f.get('conductor_asignado', ''),
                    "conductor2_asignado": f.get('conductor2_asignado', ''),
                    "camion_asignado": f.get('camion_asignado', ''),
                    "camion2_asignado": f.get('camion2_asignado', ''),
                    "bono1": f.get('bono1', datos_cliente.get('bono1', '')),
                    "bono2": f.get('bono2', datos_cliente.get('bono2', '')),
                    "viatico1": f.get('viatico1', datos_cliente.get('viatico1', 0)),
                    "viatico2": f.get('viatico2', datos_cliente.get('viatico2', 0)),
                    "origen": f.get('origen', datos_cliente.get('origen', '')),
                    "destino": f.get('destino', datos_cliente.get('destino', '')),
                    "estado": estado,
                    "tipo_combustible": f.get('tipo_combustible', ''),
                    "distancia_km": f.get('distancia_km', datos_cliente.get('distancia', 0)),
                    "costo_traslado": f.get('costo_traslado', datos_cliente.get('traslado', 0)),
                    "fecha_entrega": f.get('fecha_entrega', ''),
                    "fecha_envio": f.get('fecha_envio', ''),
                    "observacion": f.get('observacion', ''),
                    "filas": f.get('filas', [])
                }
                
                if estado == 'camino':
                    pedidos_camino.append(item)
                elif estado == 'entregado':
                    pedidos_entregados.append(item)
        
        # También buscar en pedidos_facturacion.json
        try:
            pedidos_facturacion = cargar_json(ARCHIVO_PEDIDOS_FACTURACION, [])
            for p in pedidos_facturacion:
                estado = p.get('estado_operacion', '')
                if estado == 'camino' or estado == 'entregado':
                    exists = any(item.get('id') == p.get('id') for item in (pedidos_camino if estado == 'camino' else pedidos_entregados))
                    if not exists:
                        empresa_id = p.get('empresa_id', '')
                        datos_cliente = obtener_bonos_viaticos_cliente(empresa_id)
                        
                        fecha = p.get('fecha', '')
                        fecha_str = p.get('fecha_str', '')
                        if fecha and 'T' in fecha:
                            fecha = fecha[:19]
                        if fecha_str and 'T' in fecha_str:
                            fecha_str = fecha_str[:19]
                        
                        item = {
                            "id": p.get('id', ''),
                            "factura_id": p.get('factura_id', p.get('id', '')),
                            "pedido_id": p.get('id', ''),
                            "empresa_id": empresa_id,
                            "nombre": p.get('nombre', datos_cliente.get('nombre', 'Cliente')),
                            "fecha": fecha,
                            "fecha_str": fecha_str,
                            "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "fecha_creacion": p.get("fecha_creacion", ahora),
                            "fecha_actualizacion": ahora,
                            "galones": p.get('galones', 0),
                            "precio_por_galon": p.get('precio_por_galon', 0),
                            "total": p.get('total', p.get('costo_total', 0)),
                            "conductor_asignado": p.get('conductor_asignado', ''),
                            "conductor2_asignado": p.get('conductor2_asignado', ''),
                            "camion_asignado": p.get('camion_asignado', ''),
                            "camion2_asignado": p.get('camion2_asignado', ''),
                            "bono1": p.get('bono1', datos_cliente.get('bono1', '')),
                            "bono2": p.get('bono2', datos_cliente.get('bono2', '')),
                            "viatico1": p.get('viatico1', datos_cliente.get('viatico1', 0)),
                            "viatico2": p.get('viatico2', datos_cliente.get('viatico2', 0)),
                            "origen": p.get('origen', datos_cliente.get('origen', '')),
                            "destino": p.get('destino', datos_cliente.get('destino', '')),
                            "estado": estado,
                            "tipo_combustible": p.get('tipo_combustible', ''),
                            "distancia_km": p.get('distancia_km', datos_cliente.get('distancia', 0)),
                            "costo_traslado": p.get('costo_traslado', datos_cliente.get('traslado', 0)),
                            "fecha_entrega": p.get('fecha_entrega', ''),
                            "fecha_envio": p.get('fecha_envio', ''),
                            "observacion": p.get('observacion', ''),
                            "filas": p.get('filas', [])
                        }
                        if estado == 'camino':
                            pedidos_camino.append(item)
                        else:
                            pedidos_entregados.append(item)
        except Exception as e:
            print(f"[WARN] Error sincronizando pedidos_facturacion: {e}")
        
        print(f"[DEBUG] Pedidos en camino encontrados: {len(pedidos_camino)}")
        print(f"[DEBUG] Pedidos entregados encontrados: {len(pedidos_entregados)}")
        
        if pedidos_camino:
            # Agregar fechas a cada pedido en camino
            for p in pedidos_camino:
                agregar_fechas_a_registro(p)
            data['pedidos_camino'] = pedidos_camino
        else:
            data['pedidos_camino'] = []
        
        if pedidos_entregados:
            # Agregar fechas a cada pedido entregado
            for p in pedidos_entregados:
                agregar_fechas_a_registro(p)
            data['pedidos_entregados'] = pedidos_entregados
        else:
            data['pedidos_entregados'] = []
        
        # ========== SINCRONIZAR REPORTES ==========
        try:
            reportes_data = cargar_json(ARCHIVO_REPORTES_DATA, {})
            reportes_lista = reportes_data.get('datos_tabla', [])
            if reportes_lista:
                reportes_con_fechas = []
                for r in reportes_lista:
                    if "fecha_creacion" not in r:
                        r["fecha_creacion"] = r.get("Fecha", ahora)
                    r["fecha_actualizacion"] = ahora
                    r["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    reportes_con_fechas.append(r)
                data['reportes'] = reportes_con_fechas
                print(f"[DEBUG] Sincronizados {len(reportes_con_fechas)} registros de reportes")
        except Exception as e:
            print(f"[WARN] Error sincronizando reportes: {e}")
        
        # ========== SINCRONIZAR FACTURAS ==========
        if facturas_con_fechas:
            data['facturas'] = facturas_con_fechas
            print(f"[DEBUG] Sincronizadas {len(facturas_con_fechas)} facturas")
        
        # Guardar los datos sincronizados
        data['ultima_actualizacion'] = datetime.now().isoformat()
        if "fecha_creacion" not in data:
            data["fecha_creacion"] = datetime.now().isoformat()
        data["version"] = "2.0"
        
        guardar_tablas_en_archivo(data)
        print("[INFO] ✅ Bitácora sincronizada y guardada")
        
    except Exception as e:
        print(f"[ERROR] Error en sincronización desde fuentes: {e}")
        import traceback
        traceback.print_exc()
    
    return data


def guardar_tablas_en_archivo(data):
    """Guarda los datos en el archivo JSON con fechas"""
    if TABLAS_EDITABLES_FILE:
        try:
            keys_requeridas = ["reportes", "empresas", "pedidos", "pedidos_camino", "pedidos_entregados", "costos", "conductores", "camiones", "facturas"]
            for key in keys_requeridas:
                if key not in data:
                    data[key] = []
            
            # Asegurar campos de fecha a nivel de archivo
            if "fecha_creacion" not in data:
                data["fecha_creacion"] = datetime.now().isoformat()
            data["ultima_actualizacion"] = datetime.now().isoformat()
            data["version"] = "2.0"
            
            with open(TABLAS_EDITABLES_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando: {e}")
            return False
    return False


def cargar_clientes_desde_gestion():
    """Carga los clientes desde el archivo de Gestión Clientes"""
    try:
        from main import ARCHIVO_CLIENTES, cargar_json
        if ARCHIVO_CLIENTES and os.path.exists(ARCHIVO_CLIENTES):
            data = cargar_json(ARCHIVO_CLIENTES, {"clientes": []})
            if isinstance(data, dict) and "clientes" in data:
                return data.get("clientes", [])
    except Exception as e:
        print(f"[ERROR] cargar_clientes_desde_gestion: {e}")
    
    try:
        ruta_clientes = os.path.join(os.path.dirname(TABLAS_EDITABLES_FILE), "clientes.json") if TABLAS_EDITABLES_FILE else "datos/clientes.json"
        if os.path.exists(ruta_clientes):
            with open(ruta_clientes, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and "clientes" in data:
                    return data.get("clientes", [])
    except Exception as e:
        print(f"[ERROR] cargar_clientes_desde_gestion fallback: {e}")
    
    return []


def obtener_cliente_por_id(cliente_id):
    """Obtiene un cliente específico por su ID desde Gestión Clientes"""
    if not cliente_id:
        return None
    clientes = cargar_clientes_desde_gestion()
    for cli in clientes:
        if cli.get("id") == cliente_id:
            return cli
    return None


def obtener_bonos_viaticos_cliente(cliente_id):
    """Obtiene bonos y viáticos de un cliente desde Gestión Clientes"""
    cli = obtener_cliente_por_id(cliente_id)
    if not cli:
        return {
            "bono1": "", "bono2": "", "viatico1": 0, "viatico2": 0,
            "nombre": "", "origen": "", "destino": "", "traslado": 0,
            "distancia": 0, "diesel": 0, "diesel_max": 0, "gasolina": 0, "gasolina_max": 0
        }
    
    return {
        "bono1": cli.get("bono1", ""),
        "bono2": cli.get("bono2", ""),
        "viatico1": float(cli.get("viatico1", 0)),
        "viatico2": float(cli.get("viatico2", 0)),
        "nombre": cli.get("nombre", ""),
        "origen": cli.get("origen", ""),
        "destino": cli.get("destino", ""),
        "traslado": float(cli.get("traslado", 0)),
        "distancia": float(cli.get("distancia", 0)),
        "diesel": float(cli.get("diesel", 0)),
        "diesel_max": float(cli.get("diesel_max", 0)),
        "gasolina": float(cli.get("gasolina", 0)),
        "gasolina_max": float(cli.get("gasolina_max", 0))
    }


# ==================== API PARA OBTENER DATOS DE LA BITÁCORA ====================

def api_obtener_bitacora():
    """Obtiene todos los datos de la bitácora"""
    try:
        datos = cargar_tablas_desde_archivo()
        return jsonify({
            "ok": True,
            "datos": datos,
            "timestamp": datetime.now().isoformat(),
            "fecha_creacion": datos.get("fecha_creacion"),
            "ultima_actualizacion": datos.get("ultima_actualizacion"),
            "version": datos.get("version", "2.0")
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "datos": {}})


# ==================== API PARA SINCRONIZAR BITÁCORA ====================

def api_sincronizar_bitacora():
    """Sincroniza datos desde los módulos principales a la bitácora"""
    try:
        from main import (cargar_json, ARCHIVO_EMPRESAS, ARCHIVO_PEDIDOS, ARCHIVO_CONDUCTORES, 
                         ARCHIVO_CAMIONES, ARCHIVO_COSTOS_TRASLADO, ARCHIVO_FACTURAS, 
                         ARCHIVO_REPORTES_DATA, ARCHIVO_ESTADOS_FACTURAS, ARCHIVO_PEDIDOS_FACTURACION,
                         ARCHIVO_CLIENTES)
        
        datos = cargar_tablas_desde_archivo()
        cambios_realizados = False
        ahora = datetime.now().isoformat()
        
        # ========== SINCRONIZAR EMPRESAS ==========
        clientes = cargar_clientes_desde_gestion()
        if clientes:
            empresas_con_fechas = []
            for c in clientes:
                if "fecha_creacion" not in c:
                    c["fecha_creacion"] = c.get("fecha_registro", ahora)
                c["fecha_actualizacion"] = ahora
                c["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                empresas_con_fechas.append(c)
            datos['empresas'] = empresas_con_fechas
            cambios_realizados = True
            print(f"[DEBUG] Sincronizados {len(empresas_con_fechas)} clientes desde Gestión Clientes")
        else:
            empresas = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
            empresas_lista = empresas.get('empresas', [])
            if empresas_lista:
                empresas_con_fechas = []
                for e in empresas_lista:
                    if "fecha_creacion" not in e:
                        e["fecha_creacion"] = e.get("fecha_registro", ahora)
                    e["fecha_actualizacion"] = ahora
                    e["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    empresas_con_fechas.append(e)
                datos['empresas'] = empresas_con_fechas
                cambios_realizados = True
                print(f"[DEBUG] Sincronizadas {len(empresas_con_fechas)} empresas desde empresas.json")
        
        # ========== SINCRONIZAR PEDIDOS ==========
        pedidos = cargar_json(ARCHIVO_PEDIDOS, [])
        if pedidos:
            pedidos_con_fechas = []
            for p in pedidos:
                if "fecha_creacion" not in p:
                    p["fecha_creacion"] = p.get("fecha", ahora)
                p["fecha_actualizacion"] = ahora
                p["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                empresa_id = p.get('empresa_id', '')
                if empresa_id:
                    datos_cliente = obtener_bonos_viaticos_cliente(empresa_id)
                    if not p.get('bono1') and datos_cliente.get('bono1'):
                        p['bono1'] = datos_cliente.get('bono1')
                    if not p.get('bono2') and datos_cliente.get('bono2'):
                        p['bono2'] = datos_cliente.get('bono2')
                    if not p.get('viatico1') and datos_cliente.get('viatico1'):
                        p['viatico1'] = datos_cliente.get('viatico1')
                    if not p.get('viatico2') and datos_cliente.get('viatico2'):
                        p['viatico2'] = datos_cliente.get('viatico2')
                pedidos_con_fechas.append(p)
            datos['pedidos'] = pedidos_con_fechas
            cambios_realizados = True
            print(f"[DEBUG] Sincronizados {len(pedidos_con_fechas)} pedidos pendientes")
        
        # ========== SINCRONIZAR CONDUCTORES ==========
        conductores = cargar_json(ARCHIVO_CONDUCTORES, {"conductores": []})
        conductores_lista = conductores.get('conductores', [])
        if conductores_lista:
            conductores_con_fechas = []
            for c in conductores_lista:
                if "fecha_creacion" not in c:
                    c["fecha_creacion"] = c.get("fecha_registro", ahora)
                c["fecha_actualizacion"] = ahora
                c["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conductores_con_fechas.append(c)
            datos['conductores'] = conductores_con_fechas
            cambios_realizados = True
            print(f"[DEBUG] Sincronizados {len(conductores_con_fechas)} conductores")
        
        # ========== SINCRONIZAR CAMIONES ==========
        camiones = cargar_json(ARCHIVO_CAMIONES, {"camiones": []})
        camiones_lista = camiones.get('camiones', [])
        if camiones_lista:
            camiones_con_fechas = []
            for c in camiones_lista:
                if "fecha_creacion" not in c:
                    c["fecha_creacion"] = c.get("fecha_registro", ahora)
                c["fecha_actualizacion"] = ahora
                c["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                camiones_con_fechas.append(c)
            datos['camiones'] = camiones_con_fechas
            cambios_realizados = True
            print(f"[DEBUG] Sincronizados {len(camiones_con_fechas)} camiones")
        
        # ========== SINCRONIZAR COSTOS ==========
        costos = cargar_json(ARCHIVO_COSTOS_TRASLADO, {"costos": []})
        costos_lista = costos.get('costos', [])
        if costos_lista:
            costos_con_fechas = []
            for c in costos_lista:
                if "fecha_creacion" not in c:
                    c["fecha_creacion"] = ahora
                c["fecha_actualizacion"] = ahora
                c["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                costos_con_fechas.append(c)
            datos['costos'] = costos_con_fechas
            cambios_realizados = True
            print(f"[DEBUG] Sincronizados {len(costos_con_fechas)} costos")
        
        # ========== SINCRONIZAR FACTURAS Y PEDIDOS EN CAMINO/ENTREGADOS ==========
        facturas_data = cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
        facturas_lista = facturas_data.get('facturas', [])
        estados_facturas = cargar_json(ARCHIVO_ESTADOS_FACTURAS, {})
        
        pedidos_camino = []
        pedidos_entregados = []
        facturas_con_fechas = []
        
        print(f"[DEBUG] Procesando {len(facturas_lista)} facturas para clasificar estados...")
        
        for f in facturas_lista:
            if "fecha_creacion" not in f:
                f["fecha_creacion"] = f.get("fecha_emision", ahora)
            f["fecha_actualizacion"] = ahora
            f["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            facturas_con_fechas.append(f)
            
            factura_id = f.get('id', '')
            estado = estados_facturas.get(factura_id, '')
            if not estado:
                estado = f.get('estado_factura', '')
            if not estado:
                estado = f.get('estado_operacion', '')
            if not estado and f.get('entregado', False):
                estado = 'entregado'
            if not estado:
                estado = 'comprobante'
            
            if estado == 'camino' or estado == 'entregado':
                empresa_id = f.get('empresa_id', '')
                datos_cliente = obtener_bonos_viaticos_cliente(empresa_id)
                
                fecha_emision = f.get('fecha_emision', f.get('fecha', ''))
                fecha_str = f.get('fecha_emision_str', f.get('fecha_str', ''))
                if fecha_emision and 'T' in fecha_emision:
                    fecha_emision = fecha_emision[:19]
                if fecha_str and 'T' in fecha_str:
                    fecha_str = fecha_str[:19]
                
                item = {
                    "id": factura_id,
                    "factura_id": factura_id,
                    "pedido_id": f.get('pedido_id', ''),
                    "empresa_id": empresa_id,
                    "nombre": f.get('empresa_nombre', f.get('nombre', datos_cliente.get('nombre', 'Cliente'))),
                    "fecha": fecha_emision,
                    "fecha_str": fecha_str,
                    "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "fecha_creacion": f.get("fecha_creacion", ahora),
                    "fecha_actualizacion": ahora,
                    "galones": f.get('galones', 0),
                    "precio_por_galon": f.get('precio_por_galon', 0),
                    "total": f.get('total', f.get('costo_total', 0)),
                    "conductor_asignado": f.get('conductor_asignado', ''),
                    "conductor2_asignado": f.get('conductor2_asignado', ''),
                    "camion_asignado": f.get('camion_asignado', ''),
                    "camion2_asignado": f.get('camion2_asignado', ''),
                    "bono1": f.get('bono1', datos_cliente.get('bono1', '')),
                    "bono2": f.get('bono2', datos_cliente.get('bono2', '')),
                    "viatico1": f.get('viatico1', datos_cliente.get('viatico1', 0)),
                    "viatico2": f.get('viatico2', datos_cliente.get('viatico2', 0)),
                    "origen": f.get('origen', datos_cliente.get('origen', '')),
                    "destino": f.get('destino', datos_cliente.get('destino', '')),
                    "estado": estado,
                    "tipo_combustible": f.get('tipo_combustible', ''),
                    "distancia_km": f.get('distancia_km', datos_cliente.get('distancia', 0)),
                    "costo_traslado": f.get('costo_traslado', datos_cliente.get('traslado', 0)),
                    "fecha_entrega": f.get('fecha_entrega', ''),
                    "fecha_envio": f.get('fecha_envio', ''),
                    "observacion": f.get('observacion', ''),
                    "filas": f.get('filas', [])
                }
                
                if estado == 'camino':
                    pedidos_camino.append(item)
                elif estado == 'entregado':
                    pedidos_entregados.append(item)
        
        # También buscar en pedidos_facturacion.json
        try:
            pedidos_facturacion = cargar_json(ARCHIVO_PEDIDOS_FACTURACION, [])
            for p in pedidos_facturacion:
                estado = p.get('estado_operacion', '')
                if estado == 'camino' or estado == 'entregado':
                    exists = any(item.get('id') == p.get('id') for item in (pedidos_camino if estado == 'camino' else pedidos_entregados))
                    if not exists:
                        empresa_id = p.get('empresa_id', '')
                        datos_cliente = obtener_bonos_viaticos_cliente(empresa_id)
                        
                        fecha = p.get('fecha', '')
                        fecha_str = p.get('fecha_str', '')
                        if fecha and 'T' in fecha:
                            fecha = fecha[:19]
                        if fecha_str and 'T' in fecha_str:
                            fecha_str = fecha_str[:19]
                        
                        item = {
                            "id": p.get('id', ''),
                            "factura_id": p.get('factura_id', p.get('id', '')),
                            "pedido_id": p.get('id', ''),
                            "empresa_id": empresa_id,
                            "nombre": p.get('nombre', datos_cliente.get('nombre', 'Cliente')),
                            "fecha": fecha,
                            "fecha_str": fecha_str,
                            "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "fecha_creacion": p.get("fecha_creacion", ahora),
                            "fecha_actualizacion": ahora,
                            "galones": p.get('galones', 0),
                            "precio_por_galon": p.get('precio_por_galon', 0),
                            "total": p.get('total', p.get('costo_total', 0)),
                            "conductor_asignado": p.get('conductor_asignado', ''),
                            "conductor2_asignado": p.get('conductor2_asignado', ''),
                            "camion_asignado": p.get('camion_asignado', ''),
                            "camion2_asignado": p.get('camion2_asignado', ''),
                            "bono1": p.get('bono1', datos_cliente.get('bono1', '')),
                            "bono2": p.get('bono2', datos_cliente.get('bono2', '')),
                            "viatico1": p.get('viatico1', datos_cliente.get('viatico1', 0)),
                            "viatico2": p.get('viatico2', datos_cliente.get('viatico2', 0)),
                            "origen": p.get('origen', datos_cliente.get('origen', '')),
                            "destino": p.get('destino', datos_cliente.get('destino', '')),
                            "estado": estado,
                            "tipo_combustible": p.get('tipo_combustible', ''),
                            "distancia_km": p.get('distancia_km', datos_cliente.get('distancia', 0)),
                            "costo_traslado": p.get('costo_traslado', datos_cliente.get('traslado', 0)),
                            "fecha_entrega": p.get('fecha_entrega', ''),
                            "fecha_envio": p.get('fecha_envio', ''),
                            "observacion": p.get('observacion', ''),
                            "filas": p.get('filas', [])
                        }
                        if estado == 'camino':
                            pedidos_camino.append(item)
                        else:
                            pedidos_entregados.append(item)
        except Exception as e:
            print(f"[WARN] Error sincronizando pedidos_facturacion: {e}")
        
        print(f"[DEBUG] Pedidos en camino encontrados: {len(pedidos_camino)}")
        print(f"[DEBUG] Pedidos entregados encontrados: {len(pedidos_entregados)}")
        
        if pedidos_camino:
            for p in pedidos_camino:
                agregar_fechas_a_registro(p)
            datos['pedidos_camino'] = pedidos_camino
            cambios_realizados = True
        else:
            datos['pedidos_camino'] = []
        
        if pedidos_entregados:
            for p in pedidos_entregados:
                agregar_fechas_a_registro(p)
            datos['pedidos_entregados'] = pedidos_entregados
            cambios_realizados = True
        else:
            datos['pedidos_entregados'] = []
        
        # ========== SINCRONIZAR REPORTES ==========
        try:
            reportes_data = cargar_json(ARCHIVO_REPORTES_DATA, {})
            reportes_lista = reportes_data.get('datos_tabla', [])
            if reportes_lista:
                reportes_con_fechas = []
                for r in reportes_lista:
                    if "fecha_creacion" not in r:
                        r["fecha_creacion"] = r.get("Fecha", ahora)
                    r["fecha_actualizacion"] = ahora
                    r["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    reportes_con_fechas.append(r)
                datos['reportes'] = reportes_con_fechas
                cambios_realizados = True
                print(f"[DEBUG] Sincronizados {len(reportes_con_fechas)} registros de reportes")
        except Exception as e:
            print(f"[WARN] Error sincronizando reportes: {e}")
        
        # ========== SINCRONIZAR FACTURAS ==========
        if facturas_con_fechas:
            datos['facturas'] = facturas_con_fechas
            cambios_realizados = True
            print(f"[DEBUG] Sincronizadas {len(facturas_con_fechas)} facturas")
        
        if cambios_realizados:
            datos['ultima_actualizacion'] = datetime.now().isoformat()
            if "fecha_creacion" not in datos:
                datos["fecha_creacion"] = datetime.now().isoformat()
            datos["version"] = "2.0"
            
            if guardar_tablas_en_archivo(datos):
                print(f"[DEBUG] ✅ Bitácora sincronizada exitosamente")
                return jsonify({
                    "ok": True, 
                    "mensaje": "Bitácora sincronizada", 
                    "timestamp": datetime.now().isoformat(),
                    "fecha_creacion": datos.get("fecha_creacion"),
                    "ultima_actualizacion": datos.get("ultima_actualizacion")
                })
        
        return jsonify({
            "ok": True, 
            "mensaje": "No hay cambios para sincronizar", 
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"[ERROR] api_sincronizar_bitacora: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


# ==================== API PARA LIMPIAR POR FECHAS ====================

def api_limpiar_por_fechas():
    try:
        data = request.get_json()
        fecha_desde = data.get('fecha_desde')
        fecha_hasta = data.get('fecha_hasta')
        modulo = data.get('modulo', 'todos')
        
        if not fecha_desde or not fecha_hasta:
            return jsonify({"ok": False, "error": "Se requieren fechas"})
        
        print(f"[DEBUG] Limpiando registros desde {fecha_desde} hasta {fecha_hasta} - Módulo: {modulo}")
        
        datos = cargar_tablas_desde_archivo()
        
        fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
        fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
        fecha_hasta_dt = fecha_hasta_dt.replace(hour=23, minute=59, second=59)
        
        total_eliminados = 0
        
        modulos_a_limpiar = []
        if modulo == 'todos':
            modulos_a_limpiar = ['empresas', 'pedidos', 'pedidos_camino', 'pedidos_entregados', 'costos', 'conductores', 'camiones', 'facturas', 'reportes']
        else:
            modulos_a_limpiar = [modulo]
        
        for mod in modulos_a_limpiar:
            if mod in datos and isinstance(datos[mod], list):
                original_count = len(datos[mod])
                nuevos_datos = []
                
                for registro in datos[mod]:
                    if not isinstance(registro, dict):
                        nuevos_datos.append(registro)
                        continue
                    
                    fecha_registro = None
                    for campo_fecha in ['fecha', 'fecha_registro', 'fecha_emision', 'fecha_actualizacion', 'fecha_creacion', 'fecha_str', 'Fecha', 'fecha_entrega', 'fecha_hora']:
                        if campo_fecha in registro and registro[campo_fecha]:
                            try:
                                fecha_str = registro[campo_fecha]
                                if 'T' in fecha_str:
                                    fecha_registro = datetime.fromisoformat(fecha_str[:19])
                                else:
                                    fecha_registro = datetime.strptime(fecha_str[:10], '%Y-%m-%d')
                                break
                            except:
                                continue
                    
                    if not fecha_registro:
                        nuevos_datos.append(registro)
                        continue
                    
                    if fecha_desde_dt <= fecha_registro <= fecha_hasta_dt:
                        total_eliminados += 1
                    else:
                        nuevos_datos.append(registro)
                
                datos[mod] = nuevos_datos
                print(f"[DEBUG] {mod}: {original_count} -> {len(nuevos_datos)} (eliminados: {original_count - len(nuevos_datos)})")
        
        datos['ultima_actualizacion'] = datetime.now().isoformat()
        
        if guardar_tablas_en_archivo(datos):
            return jsonify({
                "ok": True, 
                "eliminados": total_eliminados,
                "mensaje": f"Se eliminaron {total_eliminados} registros entre {fecha_desde} y {fecha_hasta}",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"ok": False, "error": "Error al guardar"})
            
    except Exception as e:
        print(f"[ERROR] api_limpiar_por_fechas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


# ==================== API PARA EXPORTAR EXCEL ====================

def api_exportar_excel():
    """Exporta TODOS los datos de la bitácora a Excel con todas las hojas y timestamps"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        from openpyxl.chart import BarChart, Reference
        
        datos = cargar_tablas_desde_archivo()
        
        empresas = datos.get('empresas', [])
        pedidos = datos.get('pedidos', [])
        pedidos_camino = datos.get('pedidos_camino', [])
        pedidos_entregados = datos.get('pedidos_entregados', [])
        costos = datos.get('costos', [])
        conductores = datos.get('conductores', [])
        camiones = datos.get('camiones', [])
        facturas = datos.get('facturas', [])
        reportes = datos.get('reportes', [])
        
        print(f"[DEBUG] Exportando Excel completo - Empresas: {len(empresas)}, Pedidos: {len(pedidos)}, Camino: {len(pedidos_camino)}, Entregados: {len(pedidos_entregados)}")
        
        total_registros = len(empresas) + len(pedidos) + len(pedidos_camino) + len(pedidos_entregados) + len(costos) + len(conductores) + len(camiones) + len(facturas) + len(reportes)
        
        if total_registros == 0:
            return jsonify({"ok": False, "error": "No hay datos para exportar en ninguna pestaña"}), 400
        
        wb = Workbook()
        header_font = Font(bold=True, color="FFFFFF")
        center_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style='thin', color='CCCCCC'), right=Side(style='thin', color='CCCCCC'),
            top=Side(style='thin', color='CCCCCC'), bottom=Side(style='thin', color='CCCCCC')
        )
        
        colores = {
            'empresas': '3B82F6', 'pedidos': 'F59E0B', 'camino': '8B5CF6',
            'entregados': '10B981', 'costos': 'EF4444', 'conductores': '06B6D4',
            'camiones': 'F472B6', 'facturas': 'F97316', 'reportes': '6366F1'
        }
        
        def crear_hoja(ws, titulo, headers, data, color_hex, ancho_extra=0):
            ws.title = titulo[:31]
            header_fill = PatternFill(start_color=color_hex, end_color=color_hex, fill_type="solid")
            
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col)
                cell.value = header
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
                cell.border = thin_border
            
            for row_idx, item in enumerate(data, start=2):
                row_data = []
                for header in headers:
                    value = None
                    for key, val in item.items():
                        if key.lower() == header.lower():
                            value = val
                            break
                    if value is None:
                        for key, val in item.items():
                            if header.lower() in key.lower() or key.lower() in header.lower():
                                value = val
                                break
                    row_data.append(value if value is not None else '')
                
                for col, value in enumerate(row_data, 1):
                    if isinstance(value, (int, float)):
                        ws.cell(row=row_idx, column=col, value=value)
                    else:
                        ws.cell(row=row_idx, column=col, value=str(value) if value is not None else '')
                    ws.cell(row=row_idx, column=col).alignment = center_alignment
                    ws.cell(row=row_idx, column=col).border = thin_border
            
            for col in range(1, len(headers) + 1):
                max_length = 0
                for row in range(1, len(data) + 2):
                    cell = ws.cell(row=row, column=col)
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                ws.column_dimensions[get_column_letter(col)].width = min(max_length + 2 + ancho_extra, 30)
        
        timestamp_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ===== HOJA 1: RESUMEN GENERAL =====
        ws_resumen = wb.active
        ws_resumen.title = "Resumen General"
        
        ws_resumen['A1'] = "BITÁCORA DE DATOS - RESUMEN GENERAL"
        ws_resumen['A1'].font = Font(bold=True, size=16)
        ws_resumen.merge_cells('A1:F1')
        ws_resumen['A1'].alignment = Alignment(horizontal="center")
        
        ws_resumen['A2'] = f"Generado: {timestamp_actual}"
        ws_resumen.merge_cells('A2:F2')
        ws_resumen['A2'].alignment = Alignment(horizontal="center")
        
        ws_resumen['A3'] = f"Fecha creación archivo: {datos.get('fecha_creacion', 'N/A')}"
        ws_resumen.merge_cells('A3:F3')
        ws_resumen['A3'].alignment = Alignment(horizontal="center")
        
        ws_resumen['A4'] = f"Última actualización: {datos.get('ultima_actualizacion', 'N/A')}"
        ws_resumen.merge_cells('A4:F4')
        ws_resumen['A4'].alignment = Alignment(horizontal="center")
        
        stats = [
            ["Módulo", "Registros", "Columnas", "Fecha/Hora", "Última actualización", "Fecha creación"],
            ["Empresas", len(empresas), "8", timestamp_actual, datos.get('ultima_actualizacion', '')[:19], datos.get('fecha_creacion', '')[:19]],
            ["Pedidos", len(pedidos), "11", timestamp_actual, datos.get('ultima_actualizacion', '')[:19], datos.get('fecha_creacion', '')[:19]],
            ["Pedidos En Camino", len(pedidos_camino), "14", timestamp_actual, datos.get('ultima_actualizacion', '')[:19], datos.get('fecha_creacion', '')[:19]],
            ["Pedidos Entregados", len(pedidos_entregados), "13", timestamp_actual, datos.get('ultima_actualizacion', '')[:19], datos.get('fecha_creacion', '')[:19]],
            ["Costos", len(costos), "5", timestamp_actual, datos.get('ultima_actualizacion', '')[:19], datos.get('fecha_creacion', '')[:19]],
            ["Conductores", len(conductores), "7", timestamp_actual, datos.get('ultima_actualizacion', '')[:19], datos.get('fecha_creacion', '')[:19]],
            ["Camiones", len(camiones), "7", timestamp_actual, datos.get('ultima_actualizacion', '')[:19], datos.get('fecha_creacion', '')[:19]],
            ["Facturas", len(facturas), "8", timestamp_actual, datos.get('ultima_actualizacion', '')[:19], datos.get('fecha_creacion', '')[:19]],
            ["Reportes", len(reportes), "8", timestamp_actual, datos.get('ultima_actualizacion', '')[:19], datos.get('fecha_creacion', '')[:19]],
            ["TOTAL", total_registros, "", timestamp_actual, "", ""]
        ]
        
        for i, row in enumerate(stats, start=6):
            for j, val in enumerate(row):
                cell = ws_resumen.cell(row=i, column=j+1, value=val)
                if i == 6:
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(start_color="F59E0B", end_color="F59E0B", fill_type="solid")
                    cell.font = Font(bold=True, color="FFFFFF")
                if i == len(stats) + 5:
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
                    cell.font = Font(bold=True, color="FFFFFF")
                cell.alignment = center_alignment
                cell.border = thin_border
        
        for col in range(1, 7):
            ws_resumen.column_dimensions[get_column_letter(col)].width = 20
        
        # ===== HOJA 2: EMPRESAS =====
        if empresas:
            ws = wb.create_sheet("Empresas")
            headers = ["ID", "Nombre", "Contacto", "Teléfono", "Email", "Crédito", "Límite", "Estado", "Fecha Creación", "Fecha Actualización", "Fecha/Hora"]
            data = []
            for e in empresas:
                data.append({
                    "ID": e.get('id', ''),
                    "Nombre": e.get('nombre', ''),
                    "Contacto": e.get('contacto', ''),
                    "Teléfono": e.get('telefono', ''),
                    "Email": e.get('email', ''),
                    "Crédito": e.get('credito', 0),
                    "Límite": e.get('limite_credito', 0),
                    "Estado": "Activo" if e.get('activo', True) else "Inactivo",
                    "Fecha Creación": e.get('fecha_creacion', '')[:19] if e.get('fecha_creacion') else '',
                    "Fecha Actualización": e.get('fecha_actualizacion', '')[:19] if e.get('fecha_actualizacion') else '',
                    "Fecha/Hora": e.get('fecha_hora', '')
                })
            crear_hoja(ws, "Empresas", headers, data, colores['empresas'], 2)
        
        # ===== HOJA 3: PEDIDOS =====
        if pedidos:
            ws = wb.create_sheet("Pedidos")
            headers = ["ID", "Fecha", "Hora", "Cliente", "Combustible", "Galones", "Origen", "Destino", "Total", "Estado", "Conductor", "Placa", "Fecha Creación", "Fecha Actualización"]
            data = []
            for p in pedidos[:500]:
                fecha = p.get('fecha_str', p.get('fecha', ''))
                hora = ""
                if fecha and 'T' in fecha:
                    partes = fecha.split('T')
                    fecha = partes[0]
                    hora = partes[1][:8] if len(partes) > 1 else ""
                data.append({
                    "ID": p.get('id', ''),
                    "Fecha": fecha,
                    "Hora": hora,
                    "Cliente": p.get('nombre', p.get('empresa_nombre', '')),
                    "Combustible": p.get('tipo_combustible', ''),
                    "Galones": p.get('galones', 0),
                    "Origen": p.get('origen', ''),
                    "Destino": p.get('destino', ''),
                    "Total": p.get('importe', p.get('costo_total', 0)),
                    "Estado": p.get('estado_operacion', ''),
                    "Conductor": p.get('conductor_asignado', ''),
                    "Placa": p.get('camion_asignado', ''),
                    "Fecha Creación": p.get('fecha_creacion', '')[:19] if p.get('fecha_creacion') else '',
                    "Fecha Actualización": p.get('fecha_actualizacion', '')[:19] if p.get('fecha_actualizacion') else ''
                })
            crear_hoja(ws, "Pedidos", headers, data, colores['pedidos'])
        
        # ===== HOJA 4: EN CAMINO =====
        if pedidos_camino:
            ws = wb.create_sheet("En Camino")
            headers = ["Factura", "Cliente", "Fecha", "Hora", "Galones", "Total", "Conductor 1", "Conductor 2", "Camión 1", "Camión 2", "Origen", "Destino", "Estado", "Fecha Creación", "Fecha Actualización", "Última Actualización"]
            data = []
            for p in pedidos_camino:
                fecha = p.get('fecha_str', p.get('fecha', ''))
                hora = ""
                if fecha and 'T' in fecha:
                    partes = fecha.split('T')
                    fecha = partes[0]
                    hora = partes[1][:8] if len(partes) > 1 else ""
                data.append({
                    "Factura": p.get('factura_id', p.get('id', '')),
                    "Cliente": p.get('nombre', ''),
                    "Fecha": fecha,
                    "Hora": hora,
                    "Galones": p.get('galones', 0),
                    "Total": p.get('total', 0),
                    "Conductor 1": p.get('conductor_asignado', ''),
                    "Conductor 2": p.get('conductor2_asignado', ''),
                    "Camión 1": p.get('camion_asignado', ''),
                    "Camión 2": p.get('camion2_asignado', ''),
                    "Origen": p.get('origen', ''),
                    "Destino": p.get('destino', ''),
                    "Estado": "🚚 En Camino",
                    "Fecha Creación": p.get('fecha_creacion', '')[:19] if p.get('fecha_creacion') else '',
                    "Fecha Actualización": p.get('fecha_actualizacion', '')[:19] if p.get('fecha_actualizacion') else '',
                    "Última Actualización": p.get('fecha_actualizacion', '')[:19] if p.get('fecha_actualizacion') else timestamp_actual
                })
            crear_hoja(ws, "En Camino", headers, data, colores['camino'])
        
        # ===== HOJA 5: ENTREGADOS =====
        if pedidos_entregados:
            ws = wb.create_sheet("Entregados")
            headers = ["Factura", "Cliente", "Fecha", "Hora", "Fecha Entrega", "Galones", "Total", "Conductor 1", "Conductor 2", "Camión 1", "Camión 2", "Estado", "Fecha Creación", "Fecha Actualización", "Última Actualización"]
            data = []
            for p in pedidos_entregados:
                fecha = p.get('fecha_str', p.get('fecha', ''))
                hora = ""
                if fecha and 'T' in fecha:
                    partes = fecha.split('T')
                    fecha = partes[0]
                    hora = partes[1][:8] if len(partes) > 1 else ""
                fecha_entrega = p.get('fecha_entrega', '')
                if fecha_entrega and 'T' in fecha_entrega:
                    fecha_entrega = fecha_entrega.split('T')[0]
                data.append({
                    "Factura": p.get('factura_id', p.get('id', '')),
                    "Cliente": p.get('nombre', ''),
                    "Fecha": fecha,
                    "Hora": hora,
                    "Fecha Entrega": fecha_entrega,
                    "Galones": p.get('galones', 0),
                    "Total": p.get('total', 0),
                    "Conductor 1": p.get('conductor_asignado', ''),
                    "Conductor 2": p.get('conductor2_asignado', ''),
                    "Camión 1": p.get('camion_asignado', ''),
                    "Camión 2": p.get('camion2_asignado', ''),
                    "Estado": "✅ Entregado",
                    "Fecha Creación": p.get('fecha_creacion', '')[:19] if p.get('fecha_creacion') else '',
                    "Fecha Actualización": p.get('fecha_actualizacion', '')[:19] if p.get('fecha_actualizacion') else '',
                    "Última Actualización": p.get('fecha_actualizacion', '')[:19] if p.get('fecha_actualizacion') else timestamp_actual
                })
            crear_hoja(ws, "Entregados", headers, data, colores['entregados'])
        
        # ===== HOJA 6: COSTOS =====
        if costos:
            ws = wb.create_sheet("Costos")
            headers = ["Empresa ID", "Precio por Galón", "Distancia (km)", "Costo por km", "Costo Traslado", "Fecha Creación", "Fecha Actualización", "Fecha/Hora"]
            data = []
            for c in costos:
                distancia = c.get('distancia_km', c.get('Distancia', 0))
                costo_km = c.get('costo_km', c.get('CostoKm', 0))
                data.append({
                    "Empresa ID": c.get('empresa_id', ''),
                    "Precio por Galón": c.get('precio_galon', c.get('precio_diesel', 0)),
                    "Distancia (km)": distancia,
                    "Costo por km": costo_km,
                    "Costo Traslado": distancia * costo_km,
                    "Fecha Creación": c.get('fecha_creacion', '')[:19] if c.get('fecha_creacion') else '',
                    "Fecha Actualización": c.get('fecha_actualizacion', '')[:19] if c.get('fecha_actualizacion') else '',
                    "Fecha/Hora": c.get('fecha_hora', '')
                })
            crear_hoja(ws, "Costos", headers, data, colores['costos'])
        
        # ===== HOJA 7: CONDUCTORES =====
        if conductores:
            ws = wb.create_sheet("Conductores")
            headers = ["ID", "Nombre", "Cédula", "Licencia", "Teléfono", "Dirección", "Estado", "Fecha Creación", "Fecha Actualización", "Fecha/Hora"]
            data = []
            for c in conductores:
                data.append({
                    "ID": c.get('id', ''),
                    "Nombre": c.get('nombre', ''),
                    "Cédula": c.get('cedula', ''),
                    "Licencia": c.get('licencia', ''),
                    "Teléfono": c.get('telefono', ''),
                    "Dirección": c.get('direccion', ''),
                    "Estado": "Activo" if c.get('activo', True) else "Inactivo",
                    "Fecha Creación": c.get('fecha_creacion', '')[:19] if c.get('fecha_creacion') else '',
                    "Fecha Actualización": c.get('fecha_actualizacion', '')[:19] if c.get('fecha_actualizacion') else '',
                    "Fecha/Hora": c.get('fecha_hora', '')
                })
            crear_hoja(ws, "Conductores", headers, data, colores['conductores'])
        
        # ===== HOJA 8: CAMIONES =====
        if camiones:
            ws = wb.create_sheet("Camiones")
            headers = ["ID", "Placa", "Marca", "Modelo", "Capacidad (gal)", "Conductor Asignado", "Estado", "Fecha Creación", "Fecha Actualización", "Fecha/Hora"]
            data = []
            for c in camiones:
                data.append({
                    "ID": c.get('id', ''),
                    "Placa": c.get('placa', ''),
                    "Marca": c.get('marca', ''),
                    "Modelo": c.get('modelo', ''),
                    "Capacidad (gal)": c.get('capacidad_galones', 0),
                    "Conductor Asignado": c.get('conductor_asignado', ''),
                    "Estado": "Activo" if c.get('activo', True) else "Inactivo",
                    "Fecha Creación": c.get('fecha_creacion', '')[:19] if c.get('fecha_creacion') else '',
                    "Fecha Actualización": c.get('fecha_actualizacion', '')[:19] if c.get('fecha_actualizacion') else '',
                    "Fecha/Hora": c.get('fecha_hora', '')
                })
            crear_hoja(ws, "Camiones", headers, data, colores['camiones'])
        
        # ===== HOJA 9: FACTURAS =====
        if facturas:
            ws = wb.create_sheet("Facturas")
            headers = ["ID", "Cliente", "Fecha", "Hora", "Total", "Estado", "Conductor", "Placa", "Fecha Creación", "Fecha Actualización", "Última Actualización"]
            data = []
            for f in facturas[:500]:
                fecha = f.get('fecha_emision_str', f.get('fecha_emision', f.get('fecha', '')))
                hora = ""
                if fecha and 'T' in fecha:
                    partes = fecha.split('T')
                    fecha = partes[0]
                    hora = partes[1][:8] if len(partes) > 1 else ""
                data.append({
                    "ID": f.get('id', ''),
                    "Cliente": f.get('empresa_nombre', f.get('nombre', '')),
                    "Fecha": fecha,
                    "Hora": hora,
                    "Total": f.get('total', f.get('costo_total', 0)),
                    "Estado": f.get('estado_factura', f.get('estado_operacion', '')),
                    "Conductor": f.get('conductor_asignado', ''),
                    "Placa": f.get('camion_asignado', ''),
                    "Fecha Creación": f.get('fecha_creacion', '')[:19] if f.get('fecha_creacion') else '',
                    "Fecha Actualización": f.get('fecha_actualizacion', '')[:19] if f.get('fecha_actualizacion') else '',
                    "Última Actualización": f.get('fecha_actualizacion', '')[:19] if f.get('fecha_actualizacion') else timestamp_actual
                })
            crear_hoja(ws, "Facturas", headers, data, colores['facturas'])
        
        # ===== HOJA 10: REPORTES =====
        if reportes:
            ws = wb.create_sheet("Reportes")
            headers = ["Factura", "Empresa", "Fecha", "Hora", "Galones", "Subtotal", "TOTAL", "Conductor", "Placa", "Fecha Creación", "Fecha Actualización", "Fecha/Hora"]
            data = []
            for r in reportes[:500]:
                fecha = r.get('Fecha', r.get('fecha', ''))
                hora = ""
                if fecha and 'T' in fecha:
                    partes = fecha.split('T')
                    fecha = partes[0]
                    hora = partes[1][:8] if len(partes) > 1 else ""
                data.append({
                    "Factura": r.get('Factura', r.get('factura', '')),
                    "Empresa": r.get('Empresa', r.get('empresa', '')),
                    "Fecha": fecha,
                    "Hora": hora,
                    "Galones": r.get('Galones', r.get('galones', 0)),
                    "Subtotal": r.get('Subtotal', r.get('subtotal', 0)),
                    "TOTAL": r.get('TOTAL', r.get('total', 0)),
                    "Conductor": r.get('Conductor 1', r.get('conductor', '')),
                    "Placa": r.get('Camión 1', r.get('placa', '')),
                    "Fecha Creación": r.get('fecha_creacion', '')[:19] if r.get('fecha_creacion') else '',
                    "Fecha Actualización": r.get('fecha_actualizacion', '')[:19] if r.get('fecha_actualizacion') else '',
                    "Fecha/Hora": r.get('fecha_hora', '')
                })
            crear_hoja(ws, "Reportes", headers, data, colores['reportes'])
        
        # ===== GRÁFICAS =====
        if pedidos_entregados or pedidos_camino:
            ws_graficas = wb.create_sheet("Gráficas")
            
            ws_graficas['A1'] = "GRÁFICAS - BITÁCORA DE DATOS"
            ws_graficas['A1'].font = Font(bold=True, size=14)
            ws_graficas.merge_cells('A1:D1')
            ws_graficas['A1'].alignment = Alignment(horizontal="center")
            
            ws_graficas['A2'] = f"Generado: {timestamp_actual}"
            ws_graficas.merge_cells('A2:D2')
            ws_graficas['A2'].alignment = Alignment(horizontal="center")
            
            ws_graficas['A3'] = f"Fecha creación archivo: {datos.get('fecha_creacion', 'N/A')}"
            ws_graficas.merge_cells('A3:D3')
            ws_graficas['A3'].alignment = Alignment(horizontal="center")
            
            if pedidos_entregados:
                ventas_cliente = {}
                for p in pedidos_entregados:
                    nombre = p.get('nombre', 'Desconocido')[:20]
                    ventas_cliente[nombre] = ventas_cliente.get(nombre, 0) + p.get('total', 0)
                
                top_clientes = sorted(ventas_cliente.items(), key=lambda x: x[1], reverse=True)[:5]
                if top_clientes:
                    for i, (cliente, venta) in enumerate(top_clientes, start=5):
                        ws_graficas.cell(row=i, column=1, value=cliente)
                        ws_graficas.cell(row=i, column=2, value=venta)
                    
                    chart = BarChart()
                    chart.title = "Top 5 Clientes por Ventas (Entregados)"
                    chart.x_axis.title = "Cliente"
                    chart.y_axis.title = "Ventas (C$)"
                    data = Reference(ws_graficas, min_col=2, min_row=5, max_row=len(top_clientes)+4)
                    cats = Reference(ws_graficas, min_col=1, min_row=5, max_row=len(top_clientes)+4)
                    chart.add_data(data, titles_from_data=False)
                    chart.set_categories(cats)
                    chart.width = 15
                    chart.height = 10
                    ws_graficas.add_chart(chart, "D5")
            
            # Resumen de Pedidos
            ws_graficas.cell(row=5, column=6, value="RESUMEN DE PEDIDOS")
            ws_graficas.cell(row=5, column=6).font = Font(bold=True, size=12)
            
            resumen_data = [
                ["Estado", "Cantidad", "Fecha/Hora"],
                ["En Camino", len(pedidos_camino), timestamp_actual],
                ["Entregados", len(pedidos_entregados), timestamp_actual],
                ["Total", len(pedidos_camino) + len(pedidos_entregados), timestamp_actual]
            ]
            for i, row in enumerate(resumen_data, start=6):
                for j, val in enumerate(row):
                    ws_graficas.cell(row=i, column=6+j, value=val)
                    if i == 6:
                        ws_graficas.cell(row=i, column=6+j).font = Font(bold=True)
                        ws_graficas.cell(row=i, column=6+j).fill = PatternFill(start_color="F59E0B", end_color="F59E0B", fill_type="solid")
                        ws_graficas.cell(row=i, column=6+j).font = Font(bold=True, color="FFFFFF")
            
            if pedidos_camino or pedidos_entregados:
                chart2 = BarChart()
                chart2.title = "Resumen de Pedidos"
                chart2.x_axis.title = "Estado"
                chart2.y_axis.title = "Cantidad"
                data2 = Reference(ws_graficas, min_col=7, min_row=6, max_row=8)
                cats2 = Reference(ws_graficas, min_col=6, min_row=7, max_row=8)
                chart2.add_data(data2, titles_from_data=True)
                chart2.set_categories(cats2)
                chart2.width = 10
                chart2.height = 8
                ws_graficas.add_chart(chart2, "K6")
        
        # Guardar archivo
        from main import CARPETA_EXCEL_REPORTES
        if not os.path.exists(CARPETA_EXCEL_REPORTES):
            os.makedirs(CARPETA_EXCEL_REPORTES, exist_ok=True)
        
        filename = f"bitacora_completa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(CARPETA_EXCEL_REPORTES, filename)
        wb.save(filepath)
        
        print(f"[DEBUG] ✅ Excel completo guardado en: {filepath} ({total_registros} registros totales)")
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"[ERROR] api_exportar_excel: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


# ==================== API PARA EXPORTAR PDF ====================

def api_exportar_pdf():
    """Exporta TODOS los datos de la bitácora a PDF con todas las tablas y timestamps"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.units import cm
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        
        datos = cargar_tablas_desde_archivo()
        
        empresas = datos.get('empresas', [])
        pedidos = datos.get('pedidos', [])
        pedidos_camino = datos.get('pedidos_camino', [])
        pedidos_entregados = datos.get('pedidos_entregados', [])
        costos = datos.get('costos', [])
        conductores = datos.get('conductores', [])
        camiones = datos.get('camiones', [])
        facturas = datos.get('facturas', [])
        reportes = datos.get('reportes', [])
        
        total_registros = len(empresas) + len(pedidos) + len(pedidos_camino) + len(pedidos_entregados) + len(costos) + len(conductores) + len(camiones) + len(facturas) + len(reportes)
        
        if total_registros == 0:
            return jsonify({"ok": False, "error": "No hay datos para exportar en ninguna pestaña"}), 400
        
        from main import CARPETA_PDF_REPORTES
        if not os.path.exists(CARPETA_PDF_REPORTES):
            os.makedirs(CARPETA_PDF_REPORTES, exist_ok=True)
        
        timestamp_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"bitacora_completa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(CARPETA_PDF_REPORTES, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=16, textColor=colors.HexColor("#f59e0b"))
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10, textColor=colors.grey)
        header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#f59e0b"), alignment=TA_LEFT)
        normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=8)
        small_style = ParagraphStyle('Small', parent=styles['Normal'], fontSize=6)
        
        elements = []
        
        # ===== PORTADA =====
        elements.append(Paragraph("BITÁCORA DE DATOS - GRUPO GSN", title_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"Generado: {timestamp_actual}", subtitle_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"Total de registros: {total_registros}", subtitle_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"Fecha creación archivo: {datos.get('fecha_creacion', 'N/A')}", subtitle_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"Última actualización: {datos.get('ultima_actualizacion', '')[:19] if datos.get('ultima_actualizacion') else 'N/A'}", subtitle_style))
        elements.append(Spacer(1, 20))
        
        def crear_tabla(titulo, headers, data, max_rows=20, color_header=colors.HexColor("#f59e0b")):
            elements.append(Paragraph(titulo, header_style))
            elements.append(Spacer(1, 4))
            
            if not data:
                elements.append(Paragraph("No hay datos para mostrar", normal_style))
                elements.append(Spacer(1, 8))
                return
            
            data_mostrar = data[:max_rows]
            
            table_data = [headers]
            for item in data_mostrar:
                row = []
                for header in headers:
                    value = None
                    for key, val in item.items():
                        if key.lower() == header.lower():
                            value = val
                            break
                    if value is None:
                        for key, val in item.items():
                            if header.lower() in key.lower() or key.lower() in header.lower():
                                value = val
                                break
                    if isinstance(value, (int, float)):
                        if isinstance(value, float) and value % 1 != 0:
                            row.append(f"{value:.2f}")
                        else:
                            row.append(str(value))
                    else:
                        row.append(str(value) if value else '')
                table_data.append(row)
            
            col_widths = []
            for i in range(len(headers)):
                max_len = len(headers[i])
                for row in table_data[1:]:
                    if i < len(row):
                        max_len = max(max_len, len(str(row[i])) if row[i] else 0)
                col_widths.append(min(max_len * 0.25 + 0.5, 3.5) * cm)
            
            tabla = Table(table_data, colWidths=col_widths, repeatRows=1)
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), color_header),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 7),
                ('GRID', (0,0), (-1,-1), 0.3, colors.grey),
                ('FONTSIZE', (0,1), (-1,-1), 6),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            elements.append(tabla)
            elements.append(Spacer(1, 8))
            
            if len(data) > max_rows:
                elements.append(Paragraph(f"Mostrando {max_rows} de {len(data)} registros", small_style))
                elements.append(Spacer(1, 4))
        
        # ===== RESUMEN =====
        elements.append(Paragraph("RESUMEN POR MÓDULO", header_style))
        elements.append(Spacer(1, 4))
        
        resumen_data = [
            ["Módulo", "Registros", "Fecha/Hora", "Fecha Creación"],
            ["Empresas", str(len(empresas)), timestamp_actual, datos.get('fecha_creacion', '')[:19]],
            ["Pedidos", str(len(pedidos)), timestamp_actual, datos.get('fecha_creacion', '')[:19]],
            ["Pedidos En Camino", str(len(pedidos_camino)), timestamp_actual, datos.get('fecha_creacion', '')[:19]],
            ["Pedidos Entregados", str(len(pedidos_entregados)), timestamp_actual, datos.get('fecha_creacion', '')[:19]],
            ["Costos", str(len(costos)), timestamp_actual, datos.get('fecha_creacion', '')[:19]],
            ["Conductores", str(len(conductores)), timestamp_actual, datos.get('fecha_creacion', '')[:19]],
            ["Camiones", str(len(camiones)), timestamp_actual, datos.get('fecha_creacion', '')[:19]],
            ["Facturas", str(len(facturas)), timestamp_actual, datos.get('fecha_creacion', '')[:19]],
            ["Reportes", str(len(reportes)), timestamp_actual, datos.get('fecha_creacion', '')[:19]],
            ["TOTAL", str(total_registros), timestamp_actual, ""]
        ]
        
        tabla_resumen = Table(resumen_data, colWidths=[4*cm, 2.5*cm, 4*cm, 4*cm])
        tabla_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f59e0b")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('BACKGROUND', (0,10), (-1,10), colors.HexColor("#10b981")),
            ('TEXTCOLOR', (0,10), (-1,10), colors.white),
            ('FONTNAME', (0,10), (-1,10), 'Helvetica-Bold'),
        ]))
        elements.append(tabla_resumen)
        elements.append(Spacer(1, 15))
        
        # ===== GRÁFICA =====
        if pedidos_entregados:
            elements.append(Paragraph("TOP CLIENTES POR VENTAS", header_style))
            elements.append(Spacer(1, 4))
            
            ventas_cliente = {}
            for p in pedidos_entregados:
                nombre = p.get('nombre', 'Desconocido')[:15]
                ventas_cliente[nombre] = ventas_cliente.get(nombre, 0) + p.get('total', 0)
            
            top_clientes = sorted(ventas_cliente.items(), key=lambda x: x[1], reverse=True)[:5]
            
            if top_clientes:
                drawing = Drawing(400, 150)
                bc = VerticalBarChart()
                bc.x = 50
                bc.y = 40
                bc.width = 300
                bc.height = 90
                bc.data = [[v for _, v in top_clientes]]
                bc.categoryAxis.categoryNames = [c[:10] + "..." if len(c) > 10 else c for c, _ in top_clientes]
                bc.categoryAxis.labels.fontSize = 7
                bc.valueAxis.labels.fontSize = 7
                bc.bars[0].fillColor = colors.HexColor("#f59e0b")
                drawing.add(bc)
                elements.append(drawing)
                elements.append(Spacer(1, 10))
        
        elements.append(PageBreak())
        
        # ===== CADA MÓDULO =====
        # Empresas
        if empresas:
            data = []
            for e in empresas:
                data.append({
                    "ID": e.get('id', ''),
                    "Nombre": e.get('nombre', ''),
                    "Contacto": e.get('contacto', ''),
                    "Teléfono": e.get('telefono', ''),
                    "Email": e.get('email', ''),
                    "Crédito": e.get('credito', 0),
                    "Límite": e.get('limite_credito', 0),
                    "Estado": "Activo" if e.get('activo', True) else "Inactivo",
                    "Fecha Crea": e.get('fecha_creacion', '')[:10] if e.get('fecha_creacion') else '',
                    "Fecha Actualiza": e.get('fecha_actualizacion', '')[:10] if e.get('fecha_actualizacion') else ''
                })
            crear_tabla("EMPRESAS", ["ID", "Nombre", "Contacto", "Teléfono", "Email", "Crédito", "Límite", "Estado", "Fecha Crea", "Fecha Actualiza"], 
                       data, max_rows=20, color_header=colors.HexColor("#3B82F6"))
        
        # Pedidos
        if pedidos:
            data = []
            for p in pedidos[:200]:
                fecha = p.get('fecha_str', p.get('fecha', ''))
                hora = ""
                if fecha and 'T' in fecha:
                    partes = fecha.split('T')
                    fecha = partes[0]
                    hora = partes[1][:8] if len(partes) > 1 else ""
                data.append({
                    "ID": p.get('id', ''),
                    "Fecha": fecha,
                    "Hora": hora,
                    "Cliente": p.get('nombre', p.get('empresa_nombre', '')),
                    "Galones": p.get('galones', 0),
                    "Total": p.get('importe', p.get('costo_total', 0)),
                    "Estado": p.get('estado_operacion', ''),
                    "Fecha Crea": p.get('fecha_creacion', '')[:10] if p.get('fecha_creacion') else ''
                })
            crear_tabla("PEDIDOS", ["ID", "Fecha", "Hora", "Cliente", "Galones", "Total", "Estado", "Fecha Crea"], data, max_rows=18, color_header=colors.HexColor("#F59E0B"))
        
        # En Camino
        if pedidos_camino:
            data = []
            for p in pedidos_camino:
                fecha = p.get('fecha_str', p.get('fecha', ''))
                hora = ""
                if fecha and 'T' in fecha:
                    partes = fecha.split('T')
                    fecha = partes[0]
                    hora = partes[1][:8] if len(partes) > 1 else ""
                data.append({
                    "Factura": p.get('factura_id', p.get('id', '')),
                    "Cliente": p.get('nombre', ''),
                    "Fecha": fecha,
                    "Hora": hora,
                    "Galones": p.get('galones', 0),
                    "Total": p.get('total', 0),
                    "Conductor": p.get('conductor_asignado', ''),
                    "Camión": p.get('camion_asignado', ''),
                    "Estado": "En Camino",
                    "Fecha Crea": p.get('fecha_creacion', '')[:10] if p.get('fecha_creacion') else ''
                })
            crear_tabla("PEDIDOS EN CAMINO", ["Factura", "Cliente", "Fecha", "Hora", "Galones", "Total", "Conductor", "Camión", "Estado", "Fecha Crea"], 
                       data, max_rows=18, color_header=colors.HexColor("#8B5CF6"))
        
        # Entregados
        if pedidos_entregados:
            data = []
            for p in pedidos_entregados:
                fecha = p.get('fecha_str', p.get('fecha', ''))
                hora = ""
                if fecha and 'T' in fecha:
                    partes = fecha.split('T')
                    fecha = partes[0]
                    hora = partes[1][:8] if len(partes) > 1 else ""
                fecha_entrega = p.get('fecha_entrega', '')
                if fecha_entrega and 'T' in fecha_entrega:
                    fecha_entrega = fecha_entrega.split('T')[0]
                data.append({
                    "Factura": p.get('factura_id', p.get('id', '')),
                    "Cliente": p.get('nombre', ''),
                    "Fecha": fecha,
                    "Hora": hora,
                    "Fecha Entrega": fecha_entrega,
                    "Galones": p.get('galones', 0),
                    "Total": p.get('total', 0),
                    "Conductor": p.get('conductor_asignado', ''),
                    "Camión": p.get('camion_asignado', ''),
                    "Estado": "Entregado",
                    "Fecha Crea": p.get('fecha_creacion', '')[:10] if p.get('fecha_creacion') else ''
                })
            crear_tabla("PEDIDOS ENTREGADOS", ["Factura", "Cliente", "Fecha", "Hora", "Fecha Entrega", "Galones", "Total", "Conductor", "Camión", "Estado", "Fecha Crea"], 
                       data, max_rows=18, color_header=colors.HexColor("#10B981"))
        
        # Costos
        if costos:
            data = []
            for c in costos:
                data.append({
                    "Empresa ID": c.get('empresa_id', ''),
                    "Precio x Gal": c.get('precio_galon', c.get('precio_diesel', 0)),
                    "Distancia": c.get('distancia_km', c.get('Distancia', 0)),
                    "Costo Traslado": c.get('distancia_km', c.get('Distancia', 0)) * c.get('costo_km', c.get('CostoKm', 0)),
                    "Fecha Crea": c.get('fecha_creacion', '')[:10] if c.get('fecha_creacion') else ''
                })
            crear_tabla("COSTOS", ["Empresa ID", "Precio x Gal", "Distancia", "Costo Traslado", "Fecha Crea"], data, max_rows=15, color_header=colors.HexColor("#EF4444"))
        
        # Conductores
        if conductores:
            data = []
            for c in conductores:
                data.append({
                    "ID": c.get('id', ''),
                    "Nombre": c.get('nombre', ''),
                    "Cédula": c.get('cedula', ''),
                    "Licencia": c.get('licencia', ''),
                    "Teléfono": c.get('telefono', ''),
                    "Fecha Crea": c.get('fecha_creacion', '')[:10] if c.get('fecha_creacion') else ''
                })
            crear_tabla("CONDUCTORES", ["ID", "Nombre", "Cédula", "Licencia", "Teléfono", "Fecha Crea"], data, max_rows=15, color_header=colors.HexColor("#06B6D4"))
        
        # Camiones
        if camiones:
            data = []
            for c in camiones:
                data.append({
                    "ID": c.get('id', ''),
                    "Placa": c.get('placa', ''),
                    "Marca": c.get('marca', ''),
                    "Capacidad": c.get('capacidad_galones', 0),
                    "Conductor": c.get('conductor_asignado', ''),
                    "Fecha Crea": c.get('fecha_creacion', '')[:10] if c.get('fecha_creacion') else ''
                })
            crear_tabla("CAMIONES", ["ID", "Placa", "Marca", "Capacidad", "Conductor", "Fecha Crea"], data, max_rows=15, color_header=colors.HexColor("#F472B6"))
        
        # Facturas
        if facturas:
            data = []
            for f in facturas[:200]:
                fecha = f.get('fecha_emision_str', f.get('fecha_emision', f.get('fecha', '')))
                hora = ""
                if fecha and 'T' in fecha:
                    partes = fecha.split('T')
                    fecha = partes[0]
                    hora = partes[1][:8] if len(partes) > 1 else ""
                data.append({
                    "ID": f.get('id', ''),
                    "Cliente": f.get('empresa_nombre', f.get('nombre', '')),
                    "Fecha": fecha,
                    "Hora": hora,
                    "Total": f.get('total', f.get('costo_total', 0)),
                    "Estado": f.get('estado_factura', f.get('estado_operacion', '')),
                    "Fecha Crea": f.get('fecha_creacion', '')[:10] if f.get('fecha_creacion') else ''
                })
            crear_tabla("FACTURAS", ["ID", "Cliente", "Fecha", "Hora", "Total", "Estado", "Fecha Crea"], data, max_rows=18, color_header=colors.HexColor("#F97316"))
        
        # Reportes
        if reportes:
            data = []
            for r in reportes[:200]:
                fecha = r.get('Fecha', r.get('fecha', ''))
                hora = ""
                if fecha and 'T' in fecha:
                    partes = fecha.split('T')
                    fecha = partes[0]
                    hora = partes[1][:8] if len(partes) > 1 else ""
                data.append({
                    "Factura": r.get('Factura', r.get('factura', '')),
                    "Empresa": r.get('Empresa', r.get('empresa', '')),
                    "Fecha": fecha,
                    "Hora": hora,
                    "Galones": r.get('Galones', r.get('galones', 0)),
                    "TOTAL": r.get('TOTAL', r.get('total', 0)),
                    "Fecha Crea": r.get('fecha_creacion', '')[:10] if r.get('fecha_creacion') else ''
                })
            crear_tabla("REPORTES", ["Factura", "Empresa", "Fecha", "Hora", "Galones", "TOTAL", "Fecha Crea"], data, max_rows=18, color_header=colors.HexColor("#6366F1"))
        
        # Pie de página
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"Documento generado el {timestamp_actual} - Grupo GSN", subtitle_style))
        elements.append(Paragraph(f"Fecha creación archivo: {datos.get('fecha_creacion', 'N/A')}", subtitle_style))
        
        doc.build(elements)
        
        print(f"[DEBUG] ✅ PDF completo guardado en: {filepath} ({total_registros} registros totales)")
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"[ERROR] api_exportar_pdf: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


# ==================== API PARA TABLA DE EMPRESAS ====================

def api_guardar_tabla_empresas():
    try:
        data = request.get_json()
        datos = data.get('datos', [])
        existing = cargar_tablas_desde_archivo()
        
        # Agregar fechas a cada registro
        for item in datos:
            agregar_fechas_a_registro(item)
        
        existing['empresas'] = datos
        existing['ultima_actualizacion'] = datetime.now().isoformat()
        if guardar_tablas_en_archivo(existing):
            return jsonify({"ok": True, "mensaje": "Datos guardados"})
        return jsonify({"ok": False, "error": "Error al guardar"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_cargar_tabla_empresas():
    try:
        data = cargar_tablas_desde_archivo()
        empresas = data.get('empresas', [])
        return jsonify({"datos": empresas})
    except Exception as e:
        return jsonify({"datos": [], "error": str(e)})


# ==================== API PARA TABLA DE PEDIDOS ====================

def api_guardar_tabla_pedidos():
    try:
        data = request.get_json()
        datos = data.get('datos', [])
        existing = cargar_tablas_desde_archivo()
        
        for item in datos:
            agregar_fechas_a_registro(item)
        
        existing['pedidos'] = datos
        if guardar_tablas_en_archivo(existing):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Error al guardar"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_cargar_tabla_pedidos():
    try:
        data = cargar_tablas_desde_archivo()
        return jsonify({"datos": data.get('pedidos', [])})
    except Exception as e:
        return jsonify({"datos": [], "error": str(e)})


# ==================== API PARA TABLA DE PEDIDOS EN CAMINO ====================

def api_guardar_tabla_pedidos_camino():
    try:
        data = request.get_json()
        datos = data.get('datos', [])
        existing = cargar_tablas_desde_archivo()
        
        for item in datos:
            agregar_fechas_a_registro(item)
        
        existing['pedidos_camino'] = datos
        if guardar_tablas_en_archivo(existing):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Error al guardar"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_cargar_tabla_pedidos_camino():
    try:
        data = cargar_tablas_desde_archivo()
        return jsonify({"datos": data.get('pedidos_camino', [])})
    except Exception as e:
        return jsonify({"datos": [], "error": str(e)})


# ==================== API PARA TABLA DE PEDIDOS ENTREGADOS ====================

def api_guardar_tabla_pedidos_entregados():
    try:
        data = request.get_json()
        datos = data.get('datos', [])
        existing = cargar_tablas_desde_archivo()
        
        for item in datos:
            agregar_fechas_a_registro(item)
        
        existing['pedidos_entregados'] = datos
        if guardar_tablas_en_archivo(existing):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Error al guardar"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_cargar_tabla_pedidos_entregados():
    try:
        data = cargar_tablas_desde_archivo()
        return jsonify({"datos": data.get('pedidos_entregados', [])})
    except Exception as e:
        return jsonify({"datos": [], "error": str(e)})


# ==================== API PARA TABLA DE COSTOS ====================

def api_guardar_tabla_costos():
    try:
        data = request.get_json()
        datos = data.get('datos', [])
        existing = cargar_tablas_desde_archivo()
        
        for item in datos:
            agregar_fechas_a_registro(item)
        
        existing['costos'] = datos
        if guardar_tablas_en_archivo(existing):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Error al guardar"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_cargar_tabla_costos():
    try:
        data = cargar_tablas_desde_archivo()
        return jsonify({"datos": data.get('costos', [])})
    except Exception as e:
        return jsonify({"datos": [], "error": str(e)})


# ==================== FUNCIONES DE SINCRONIZACION ====================

def sincronizar_con_empresas_json():
    try:
        from main import ARCHIVO_EMPRESAS, cargar_json, guardar_json
        
        empresas_principales = cargar_json(ARCHIVO_EMPRESAS, {"empresas": []})
        data = cargar_tablas_desde_archivo()
        empresas_editables = data.get('empresas', [])
        
        for emp_principal in empresas_principales.get("empresas", []):
            for emp_editable in empresas_editables:
                if emp_editable.get("ID") == emp_principal.get("id"):
                    emp_principal["credito"] = float(emp_editable.get("Credito", 0))
                    emp_principal["limite_credito"] = float(emp_editable.get("Limite Credito", 0))
                    break
        
        guardar_json(ARCHIVO_EMPRESAS, empresas_principales)
        return True
    except Exception as e:
        print(f"Error sincronizando: {e}")
        return False