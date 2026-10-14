# ==================== MÓDULO REPORTES ====================
import os
import json
import base64
import io
from datetime import datetime, timedelta
from flask import jsonify, request, send_file

# ==================== CONFIGURACIÓN ====================
ARCHIVO_PEDIDOS = None
ARCHIVO_FACTURAS = None
ARCHIVO_PEDIDOS_FACTURACION = None
ARCHIVO_ESTADOS_FACTURAS = None
ARCHIVO_OBSERVACIONES = None
ARCHIVO_REPORTES_DATA = None
CARPETA_EXCEL_REPORTES = None
CARPETA_PDF_REPORTES = None

_cargar_json = None
_guardar_json = None

# Estados de operación
ESTADO_ESPERA = 'espera'
ESTADO_COMPROBANTE = 'comprobante'
ESTADO_CAMINO = 'camino'
ESTADO_ENTREGADO = 'entregado'
ESTADO_FACTURACION = 'facturacion'


# ==================== INICIALIZACIÓN ====================
def inicializar_reportes(main_funciones=None, rutas_config=None):
    global _cargar_json, _guardar_json, ARCHIVO_PEDIDOS, ARCHIVO_FACTURAS
    global ARCHIVO_PEDIDOS_FACTURACION, ARCHIVO_ESTADOS_FACTURAS, ARCHIVO_OBSERVACIONES
    global CARPETA_EXCEL_REPORTES, CARPETA_PDF_REPORTES, ARCHIVO_REPORTES_DATA
    
    if main_funciones:
        _cargar_json = main_funciones.get('cargar_json')
        _guardar_json = main_funciones.get('guardar_json')
    
    if rutas_config:
        ARCHIVO_PEDIDOS = rutas_config.get('pedidos')
        ARCHIVO_FACTURAS = rutas_config.get('facturas')
        ARCHIVO_PEDIDOS_FACTURACION = rutas_config.get('pedidos_facturacion')
        CARPETA_EXCEL_REPORTES = rutas_config.get('excel_reportes')
        CARPETA_PDF_REPORTES = rutas_config.get('pdf_reportes')
        ARCHIVO_REPORTES_DATA = rutas_config.get('reportes_data')
        
        if ARCHIVO_PEDIDOS:
            base_dir = os.path.dirname(ARCHIVO_PEDIDOS)
            ARCHIVO_ESTADOS_FACTURAS = os.path.join(base_dir, "estados_facturas.json")
            ARCHIVO_OBSERVACIONES = os.path.join(base_dir, "observaciones.json")
        
        # Crear carpetas si no existen
        if CARPETA_EXCEL_REPORTES:
            try:
                os.makedirs(CARPETA_EXCEL_REPORTES, exist_ok=True)
                print(f"[INFO] Carpeta Excel Reportes: {CARPETA_EXCEL_REPORTES}")
            except Exception as e:
                print(f"[ERROR] Creando carpeta Excel Reportes: {e}")
        
        if CARPETA_PDF_REPORTES:
            try:
                os.makedirs(CARPETA_PDF_REPORTES, exist_ok=True)
                print(f"[INFO] Carpeta PDF Reportes: {CARPETA_PDF_REPORTES}")
            except Exception as e:
                print(f"[ERROR] Creando carpeta PDF Reportes: {e}")
    
    print(f"[INFO] Módulo Reportes inicializado")
    print(f"[INFO] Archivo reportes_data: {ARCHIVO_REPORTES_DATA}")
    print(f"[INFO] Archivo facturas: {ARCHIVO_FACTURAS}")


def cargar_json_seguro(ruta, default=None):
    if _cargar_json:
        return _cargar_json(ruta, default)
    
    try:
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read().strip()
                if not contenido:
                    return default if default is not None else {} if isinstance(default, dict) else []
                return json.loads(contenido)
    except Exception as e:
        print(f"[ERROR] cargar_json_seguro: {e}")
    return default if default is not None else {} if isinstance(default, dict) else []


def guardar_json_seguro(ruta, data):
    if _guardar_json:
        return _guardar_json(ruta, data)
    
    try:
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] guardar_json_seguro: {e}")
        return False


def cargar_estados_facturas():
    try:
        if ARCHIVO_ESTADOS_FACTURAS and os.path.exists(ARCHIVO_ESTADOS_FACTURAS):
            return cargar_json_seguro(ARCHIVO_ESTADOS_FACTURAS, {})
    except:
        pass
    return {}


def cargar_observaciones():
    try:
        if ARCHIVO_OBSERVACIONES and os.path.exists(ARCHIVO_OBSERVACIONES):
            return cargar_json_seguro(ARCHIVO_OBSERVACIONES, {})
    except:
        pass
    return {}


def cargar_pedidos():
    try:
        if ARCHIVO_PEDIDOS and os.path.exists(ARCHIVO_PEDIDOS):
            return cargar_json_seguro(ARCHIVO_PEDIDOS, [])
    except Exception as e:
        print(f"[ERROR] cargar_pedidos: {e}")
    return []


def cargar_facturas():
    try:
        if ARCHIVO_FACTURAS and os.path.exists(ARCHIVO_FACTURAS):
            data = cargar_json_seguro(ARCHIVO_FACTURAS, {"facturas": []})
            if isinstance(data, dict) and "facturas" in data:
                return data["facturas"]
            elif isinstance(data, list):
                return data
            return []
    except Exception as e:
        print(f"[ERROR] cargar_facturas: {e}")
    return []


def cargar_pedidos_facturacion():
    try:
        if ARCHIVO_PEDIDOS_FACTURACION and os.path.exists(ARCHIVO_PEDIDOS_FACTURACION):
            return cargar_json_seguro(ARCHIVO_PEDIDOS_FACTURACION, [])
    except Exception as e:
        print(f"[ERROR] cargar_pedidos_facturacion: {e}")
    return []


def guardar_facturas(facturas):
    try:
        if ARCHIVO_FACTURAS:
            if not isinstance(facturas, list):
                facturas = []
            data = {"facturas": facturas}
            return guardar_json_seguro(ARCHIVO_FACTURAS, data)
    except Exception as e:
        print(f"[ERROR] guardar_facturas: {e}")
    return False


# ==================== DATOS DE TABLA ====================

def cargar_datos_tabla():
    """Carga los datos guardados de la tabla editable"""
    try:
        if ARCHIVO_REPORTES_DATA and os.path.exists(ARCHIVO_REPORTES_DATA):
            data = cargar_json_seguro(ARCHIVO_REPORTES_DATA, {})
            if "totals_editados" not in data:
                data["totals_editados"] = {}
            if "columnas_personalizadas" not in data:
                data["columnas_personalizadas"] = []
            if "datos_tabla" not in data:
                data["datos_tabla"] = []
            if "ultima_actualizacion" not in data:
                data["ultima_actualizacion"] = datetime.now().isoformat()
            return data
    except Exception as e:
        print(f"[ERROR] cargar_datos_tabla: {e}")
    return {"columnas_personalizadas": [], "datos_tabla": [], "totals_editados": {}, "ultima_actualizacion": datetime.now().isoformat()}


def guardar_datos_tabla(data):
    """Guarda los datos de la tabla editable"""
    try:
        if ARCHIVO_REPORTES_DATA:
            if "columnas_personalizadas" not in data:
                data["columnas_personalizadas"] = []
            if "datos_tabla" not in data:
                data["datos_tabla"] = []
            if "totals_editados" not in data:
                data["totals_editados"] = {}
            if "ultima_actualizacion" not in data:
                data["ultima_actualizacion"] = datetime.now().isoformat()
            
            print(f"[DEBUG] Guardando datos - columnas: {len(data.get('columnas_personalizadas', []))}, filas: {len(data.get('datos_tabla', []))}, totales: {len(data.get('totals_editados', {}))}")
            
            return guardar_json_seguro(ARCHIVO_REPORTES_DATA, data)
    except Exception as e:
        print(f"[ERROR] guardar_datos_tabla: {e}")
        import traceback
        traceback.print_exc()
    return False


def obtener_estado_factura(factura):
    """Obtiene el estado de una factura buscando en múltiples fuentes"""
    estado = factura.get('estado_factura', '')
    if estado:
        return estado
    
    pedidos = factura.get('pedidos', [])
    for p in pedidos:
        estado_operacion = p.get('estado_operacion', '')
        if estado_operacion:
            return estado_operacion
    
    if factura.get('fecha_entrega'):
        return ESTADO_ENTREGADO
    
    return 'pendiente'


def convertir_factura_a_pedido(factura):
    """Convierte una factura a formato pedido para Reportes"""
    if not isinstance(factura, dict):
        return {}
    
    pedido_data = {}
    if 'pedidos' in factura and isinstance(factura['pedidos'], list) and len(factura['pedidos']) > 0:
        pedido_data = factura['pedidos'][0]
    
    estado = obtener_estado_factura(factura)
    entregado = estado == ESTADO_ENTREGADO
    
    return {
        "id": pedido_data.get('id', factura.get('id', '')),
        "factura_id": factura.get('id', ''),
        "pedido_id": pedido_data.get('id', factura.get('pedido_id', '')),
        "empresa_id": pedido_data.get('empresa_id', factura.get('empresa_id', '')),
        "nombre": pedido_data.get('nombre', factura.get('empresa_nombre', 'Cliente')),
        "empresa_nombre": factura.get('empresa_nombre', ''),
        "cedula": pedido_data.get('cedula', factura.get('empresa_nit', '')),
        "telefono": pedido_data.get('telefono', factura.get('empresa_telefono_cliente', '')),
        "email": pedido_data.get('email', ''),
        "fecha": pedido_data.get('fecha', factura.get('fecha_emision', factura.get('fecha_recepcion', datetime.now().isoformat()))),
        "fecha_str": pedido_data.get('fecha_str', factura.get('fecha_emision', factura.get('fecha_recepcion', '')))[:10] if factura.get('fecha_emision') or factura.get('fecha_recepcion') else datetime.now().strftime("%Y-%m-%d"),
        "fecha_entrega": factura.get('fecha_entrega', factura.get('fecha_envio', '')),
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
        "total": factura.get('total', 0),
        "subtotal": pedido_data.get('costo_total', factura.get('costo_total', 0)),
        "estado_operacion": estado,
        "estado_factura": estado,
        "conductor_asignado": pedido_data.get('conductor_asignado', factura.get('conductor_asignado', '')),
        "conductor2_asignado": pedido_data.get('conductor2_asignado', factura.get('conductor2_asignado', '')),
        "camion_asignado": pedido_data.get('camion_asignado', factura.get('camion_asignado', '')),
        "camion2_asignado": pedido_data.get('camion2_asignado', factura.get('camion2_asignado', '')),
        "observacion": factura.get('observacion', ''),
        "bono1": factura.get('bono1', ''),
        "bono2": factura.get('bono2', ''),
        "viatico1": factura.get('viatico1', 0),
        "viatico2": factura.get('viatico2', 0),
        "entregado": entregado,
        "filas": factura.get('filas', pedido_data.get('filas', []))
    }


def obtener_pedidos_entregados():
    """Obtiene pedidos entregados desde facturas_combustible.json"""
    try:
        pedidos_entregados = []
        facturas = cargar_facturas()
        print(f"[DEBUG] Facturas cargadas: {len(facturas) if facturas else 0}")
        
        if isinstance(facturas, list):
            for factura in facturas:
                if isinstance(factura, dict):
                    estado = obtener_estado_factura(factura)
                    if estado == ESTADO_ENTREGADO:
                        pedido_convertido = convertir_factura_a_pedido(factura)
                        if pedido_convertido and pedido_convertido.get('id'):
                            pedidos_entregados.append(pedido_convertido)
        
        print(f"[DEBUG] Pedidos entregados encontrados: {len(pedidos_entregados)}")
        return pedidos_entregados
    except Exception as e:
        print(f"[ERROR] obtener_pedidos_entregados: {e}")
        import traceback
        traceback.print_exc()
        return []


# ==================== API ENDPOINTS ====================

def api_estadisticas():
    try:
        pedidos_entregados = obtener_pedidos_entregados()
        
        total_entregados = len(pedidos_entregados)
        total_galones = sum(p.get('galones', 0) for p in pedidos_entregados)
        total_costo = sum(p.get('costo_total', p.get('costo_combustible', 0)) for p in pedidos_entregados)
        total_venta = sum(p.get('total', p.get('costo_total', p.get('importe', 0))) for p in pedidos_entregados)
        total_margen = total_venta - total_costo
        porcentaje_margen = (total_margen / total_venta * 100) if total_venta > 0 else 0
        
        pedidos_por_mes = {}
        for p in pedidos_entregados:
            try:
                fecha_str = p.get('fecha_entrega', p.get('fecha_str', p.get('fecha', '')))
                if fecha_str:
                    mes = fecha_str[:7]
                    pedidos_por_mes[mes] = pedidos_por_mes.get(mes, 0) + 1
            except:
                pass
        
        return jsonify({
            "ok": True,
            "estadisticas": {
                "total_entregados": total_entregados,
                "total_galones": total_galones,
                "total_costo": total_costo,
                "total_venta": total_venta,
                "total_margen": total_margen,
                "porcentaje_margen": round(porcentaje_margen, 1),
                "pedidos_por_mes": pedidos_por_mes
            }
        })
    except Exception as e:
        print(f"[ERROR] api_estadisticas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e), "estadisticas": {}})


def api_guardar_datos_tabla():
    """Guarda los datos completos de la tabla editable"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"ok": False, "error": "No data provided"})
        
        print(f"[DEBUG] ===== GUARDANDO DATOS =====")
        print(f"[DEBUG] Columnas: {len(data.get('columnas_personalizadas', []))}")
        print(f"[DEBUG] Filas: {len(data.get('datos_tabla', []))}")
        print(f"[DEBUG] Totales editados: {len(data.get('totals_editados', {}))}")
        print(f"[DEBUG] Ruta: {ARCHIVO_REPORTES_DATA}")
        
        datos_guardar = {
            "columnas_personalizadas": data.get("columnas_personalizadas", []),
            "datos_tabla": data.get("datos_tabla", []),
            "totals_editados": data.get("totals_editados", {}),
            "ultima_actualizacion": datetime.now().isoformat()
        }
        
        if guardar_datos_tabla(datos_guardar):
            print(f"[DEBUG] ✅ Datos guardados exitosamente")
            return jsonify({"ok": True, "mensaje": "Datos guardados correctamente"})
        print(f"[DEBUG] ❌ Error al guardar")
        return jsonify({"ok": False, "error": "Error al guardar"})
    except Exception as e:
        print(f"[ERROR] api_guardar_datos_tabla: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


def api_cargar_datos_tabla():
    """Carga los datos guardados de la tabla editable"""
    try:
        data = cargar_datos_tabla()
        print(f"[DEBUG] Cargando datos - columnas: {len(data.get('columnas_personalizadas', []))}, filas: {len(data.get('datos_tabla', []))}, totales: {len(data.get('totals_editados', {}))}")
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        print(f"[ERROR] api_cargar_datos_tabla: {e}")
        return jsonify({"ok": False, "error": str(e), "data": {"columnas_personalizadas": [], "datos_tabla": [], "totals_editados": {}}})


def api_guardar_celda_tabla():
    """Guarda una celda específica de la tabla editable (TOTAL o columnas personalizadas)"""
    try:
        data = request.get_json()
        factura_id = data.get('factura_id')
        columna = data.get('columna')
        valor = data.get('valor')
        
        if not factura_id or not columna:
            return jsonify({"ok": False, "error": "Se requiere factura_id y columna"})
        
        print(f"[DEBUG] Guardando celda - factura: {factura_id}, columna: {columna}, valor: {valor}")
        
        datos_guardados = cargar_datos_tabla()
        
        if "totals_editados" not in datos_guardados:
            datos_guardados["totals_editados"] = {}
        
        if factura_id not in datos_guardados["totals_editados"]:
            datos_guardados["totals_editados"][factura_id] = {}
        
        datos_guardados["totals_editados"][factura_id][columna] = float(valor) if columna == 'TOTAL' else valor
        datos_guardados["ultima_actualizacion"] = datetime.now().isoformat()
        
        if "datos_tabla" in datos_guardados:
            for fila in datos_guardados["datos_tabla"]:
                if fila.get("Factura") == factura_id or fila.get("id") == factura_id:
                    fila[columna] = float(valor) if columna == 'TOTAL' else valor
                    break
        
        if guardar_datos_tabla(datos_guardados):
            return jsonify({"ok": True, "mensaje": "Celda guardada"})
        return jsonify({"ok": False, "error": "Error al guardar"})
    except Exception as e:
        print(f"[ERROR] api_guardar_celda_tabla: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


def api_guardar_totales():
    """Guarda solo los totales editados"""
    try:
        data = request.get_json()
        totals = data.get('totals', {})
        
        print(f"[DEBUG] Guardando totales: {len(totals)} facturas")
        
        if not totals:
            return jsonify({"ok": True, "mensaje": "No hay totales para guardar"})
        
        datos_guardados = cargar_datos_tabla()
        datos_guardados["totals_editados"] = totals
        datos_guardados["ultima_actualizacion"] = datetime.now().isoformat()
        
        if guardar_datos_tabla(datos_guardados):
            return jsonify({"ok": True, "mensaje": "Totales guardados"})
        return jsonify({"ok": False, "error": "Error al guardar"})
    except Exception as e:
        print(f"[ERROR] api_guardar_totales: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


def api_guardar_columnas_tabla():
    """Guarda las columnas personalizadas de la tabla editable"""
    try:
        data = request.get_json()
        columnas = data.get('columnas', [])
        
        print(f"[DEBUG] Guardando columnas: {columnas}")
        
        datos_guardados = cargar_datos_tabla()
        datos_guardados["columnas_personalizadas"] = columnas
        datos_guardados["ultima_actualizacion"] = datetime.now().isoformat()
        
        if guardar_datos_tabla(datos_guardados):
            return jsonify({"ok": True, "mensaje": "Columnas guardadas"})
        return jsonify({"ok": False, "error": "Error al guardar"})
    except Exception as e:
        print(f"[ERROR] api_guardar_columnas_tabla: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_recargar():
    """Endpoint para recargar datos"""
    try:
        print("[DEBUG] Reportes recargando datos...")
        return jsonify({"ok": True, "mensaje": "Datos recargados"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_facturas_lista():
    """Retorna la lista de facturas para Reportes con estado detectado"""
    try:
        facturas = cargar_facturas()
        estados = cargar_estados_facturas()
        observaciones = cargar_observaciones()
        
        facturas_con_estado = []
        for f in facturas:
            f_copy = f.copy()
            
            estado = estados.get(f.get('id'), '')
            
            if not estado:
                estado = f.get('estado_factura', '')
            
            if not estado:
                pedidos = f.get('pedidos', [])
                for p in pedidos:
                    estado_operacion = p.get('estado_operacion', '')
                    if estado_operacion:
                        estado = estado_operacion
                        break
            
            if not estado and f.get('fecha_entrega'):
                estado = ESTADO_ENTREGADO
            
            f_copy['estado_factura'] = estado or 'pendiente'
            f_copy['observacion'] = observaciones.get(f.get('id'), {}).get('observacion', '')
            
            if estado == ESTADO_ENTREGADO and not f_copy.get('fecha_entrega'):
                f_copy['fecha_entrega'] = f.get('fecha_emision') or f.get('fecha_recepcion') or datetime.now().isoformat()
            
            facturas_con_estado.append(f_copy)
        
        facturas_con_estado.sort(key=lambda x: x.get('fecha_emision', ''), reverse=True)
        
        entregadas = sum(1 for f in facturas_con_estado if f.get('estado_factura') == ESTADO_ENTREGADO)
        print(f"[DEBUG] Facturas totales: {len(facturas_con_estado)}, Entregadas: {entregadas}")
        
        return jsonify({"ok": True, "facturas": facturas_con_estado})
    except Exception as e:
        print(f"[ERROR] api_facturas_lista: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e), "facturas": []})


def api_exportar_excel():
    """Exporta los pedidos entregados a Excel con todas las columnas y gráficas"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils.dataframe import dataframe_to_rows
        from openpyxl.chart import BarChart, LineChart, PieChart, Reference
        from openpyxl.utils import get_column_letter
        from openpyxl.drawing.image import Image
        from openpyxl.chart.label import DataLabelList
        
        pedidos_entregados = obtener_pedidos_entregados()
        print(f"[DEBUG] Exportando Excel - Pedidos encontrados: {len(pedidos_entregados)}")
        print(f"[DEBUG] Carpeta Excel: {CARPETA_EXCEL_REPORTES}")
        
        if not pedidos_entregados:
            return jsonify({"ok": False, "error": "No hay pedidos entregados para exportar"}), 400
        
        wb = Workbook()
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="F59E0B", end_color="F59E0B", fill_type="solid")
        
        # ===== HOJA 1: DATOS COMPLETOS =====
        ws_datos = wb.active
        ws_datos.title = "Datos Completos"
        
        # TODAS LAS COLUMNAS DE LA TABLA
        all_headers = [
            "ID Pedido", "Factura", "Empresa", "Cédula/RUC", 
            "Fecha Entrega", "Fecha Envío", "Origen", "Destino",
            "Tipo Combustible", "Galones", "Precio/Galón", 
            "Costo Combustible", "Costo Traslado", "Costo Total",
            "IVA", "Importe", "Total", "Subtotal",
            "Estado Operación", "Estado Factura",
            "Conductor 1", "Conductor 2", "Camión 1", "Camión 2",
            "Bono 1", "Bono 2", "Viático 1", "Viático 2",
            "Observación", "Entregado"
        ]
        
        # Encabezados
        for col, header in enumerate(all_headers, 1):
            cell = ws_datos.cell(row=1, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Datos
        for row_idx, p in enumerate(pedidos_entregados, start=2):
            costo = p.get('costo_total', p.get('costo_combustible', 0))
            venta = p.get('total', p.get('costo_total', p.get('importe', 0)))
            iva = venta * 0.19 if venta else 0
            importe = venta + iva if venta else 0
            
            row_data = [
                p.get('id', ''),
                p.get('factura_id', ''),
                p.get('nombre', p.get('empresa_nombre', '')),
                p.get('cedula', ''),
                p.get('fecha_entrega', p.get('fecha_str', ''))[:10],
                p.get('fecha_envio', ''),
                p.get('origen', ''),
                p.get('destino', ''),
                p.get('tipo_combustible', ''),
                p.get('galones', 0),
                p.get('precio_por_galon', 0),
                round(costo, 2),
                p.get('costo_traslado', 0),
                round(costo, 2),
                round(iva, 2),
                round(importe, 2),
                round(venta, 2),
                p.get('subtotal', 0),
                p.get('estado_operacion', ''),
                p.get('estado_factura', ''),
                p.get('conductor_asignado', ''),
                p.get('conductor2_asignado', ''),
                p.get('camion_asignado', ''),
                p.get('camion2_asignado', ''),
                p.get('bono1', ''),
                p.get('bono2', ''),
                p.get('viatico1', 0),
                p.get('viatico2', 0),
                p.get('observacion', ''),
                "Sí" if p.get('entregado') else "No"
            ]
            for col, value in enumerate(row_data, 1):
                ws_datos.cell(row=row_idx, column=col, value=value)
        
        # Ajustar anchos de columna
        for col in ws_datos.columns:
            max_length = 0
            for cell in col:
                try:
                    if cell.value and len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            if max_length > 0:
                adjusted_width = min(max_length + 2, 35)
                col_letter = get_column_letter(col[0].column)
                ws_datos.column_dimensions[col_letter].width = adjusted_width
        
        # ===== HOJA 2: GRÁFICAS =====
        ws_graficas = wb.create_sheet("Gráficas")
        
        # ===== GRÁFICA 1: Evolución Ventas vs Costo =====
        fechas_group = {}
        for p in pedidos_entregados:
            fecha_str = p.get('fecha_entrega', p.get('fecha_str', ''))
            if fecha_str:
                fecha_key = fecha_str[:10]
                if fecha_key not in fechas_group:
                    fechas_group[fecha_key] = {"costo": 0, "venta": 0}
                fechas_group[fecha_key]["costo"] += p.get('costo_total', p.get('costo_combustible', 0))
                fechas_group[fecha_key]["venta"] += p.get('total', p.get('costo_total', p.get('importe', 0)))
        
        fechas_ordenadas = sorted(fechas_group.keys())[-7:]
        
        if fechas_ordenadas:
            # Datos para gráfica
            ws_graficas['A1'] = "FECHA"
            ws_graficas['B1'] = "COSTO DIRECTO"
            ws_graficas['C1'] = "TOTAL VENTAS"
            
            for i, fecha in enumerate(fechas_ordenadas, start=2):
                ws_graficas[f'A{i}'] = fecha[5:]
                ws_graficas[f'B{i}'] = fechas_group[fecha]["costo"]
                ws_graficas[f'C{i}'] = fechas_group[fecha]["venta"]
            
            # Crear gráfica de barras
            chart1 = BarChart()
            chart1.type = "col"
            chart1.style = 10
            chart1.title = "Evolución Ventas vs Costo (Últimos 7 días)"
            chart1.y_axis.title = "Monto (C$)"
            chart1.x_axis.title = "Fecha"
            
            data1 = Reference(ws_graficas, min_col=2, min_row=1, max_col=3, max_row=len(fechas_ordenadas)+1)
            cats1 = Reference(ws_graficas, min_col=1, min_row=2, max_row=len(fechas_ordenadas)+1)
            chart1.add_data(data1, titles_from_data=True)
            chart1.set_categories(cats1)
            chart1.shape = 4
            chart1.height = 6
            chart1.width = 12
            chart1.legend.position = 'b'
            
            ws_graficas.add_chart(chart1, "E2")
        
        # ===== GRÁFICA 2: Top Clientes por Galones =====
        vol_cliente = {}
        for p in pedidos_entregados:
            nombre = p.get('nombre', p.get('empresa_nombre', 'Desconocido'))[:20]
            vol_cliente[nombre] = vol_cliente.get(nombre, 0) + p.get('galones', 0)
        
        top_clientes = sorted(vol_cliente.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if top_clientes:
            col_start = 6  # Columna F
            
            # Datos para gráfica
            ws_graficas.cell(row=1, column=col_start, value="CLIENTE")
            ws_graficas.cell(row=1, column=col_start+1, value="GALONES")
            
            for i, (cliente, galones) in enumerate(top_clientes, start=2):
                ws_graficas.cell(row=i, column=col_start, value=cliente)
                ws_graficas.cell(row=i, column=col_start+1, value=galones)
            
            # Crear gráfica de barras
            chart2 = BarChart()
            chart2.type = "col"
            chart2.style = 11
            chart2.title = "Top Clientes por Galones"
            chart2.y_axis.title = "Galones"
            chart2.x_axis.title = "Cliente"
            
            data2 = Reference(ws_graficas, min_col=col_start+1, min_row=1, max_col=col_start+1, max_row=len(top_clientes)+1)
            cats2 = Reference(ws_graficas, min_col=col_start, min_row=2, max_row=len(top_clientes)+1)
            chart2.add_data(data2, titles_from_data=True)
            chart2.set_categories(cats2)
            chart2.shape = 4
            chart2.height = 6
            chart2.width = 10
            chart2.legend.position = 'b'
            
            ws_graficas.add_chart(chart2, "Q2")
        
        # ===== GRÁFICA 3: Margen por Cliente (Pie) =====
        margen_cliente = {}
        for p in pedidos_entregados:
            nombre = p.get('nombre', p.get('empresa_nombre', 'Desconocido'))[:15]
            venta = p.get('total', p.get('costo_total', p.get('importe', 0)))
            costo = p.get('costo_total', p.get('costo_combustible', 0))
            margen = venta - costo
            if margen > 0:
                margen_cliente[nombre] = margen_cliente.get(nombre, 0) + margen
        
        top_margen = sorted(margen_cliente.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if top_margen:
            row_start = len(top_clientes) + 4 if top_clientes else 2
            col_start = 6
            
            # Datos para gráfica
            ws_graficas.cell(row=row_start, column=col_start, value="CLIENTE")
            ws_graficas.cell(row=row_start, column=col_start+1, value="MARGEN")
            
            for i, (cliente, margen_val) in enumerate(top_margen, start=row_start+1):
                ws_graficas.cell(row=i, column=col_start, value=cliente)
                ws_graficas.cell(row=i, column=col_start+1, value=margen_val)
            
            # Crear gráfica de torta
            chart3 = PieChart()
            chart3.title = "Margen por Cliente"
            chart3.style = 10
            
            data3 = Reference(ws_graficas, min_col=col_start+1, min_row=row_start, max_row=row_start+len(top_margen))
            cats3 = Reference(ws_graficas, min_col=col_start, min_row=row_start+1, max_row=row_start+len(top_margen))
            chart3.add_data(data3, titles_from_data=True)
            chart3.set_categories(cats3)
            chart3.height = 6
            chart3.width = 8
            
            ws_graficas.add_chart(chart3, "Q" + str(row_start+2))
        
        # Ajustar anchos de columna
        for col in ws_graficas.columns:
            max_length = 0
            for cell in col:
                try:
                    if cell.value and len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            if max_length > 0:
                adjusted_width = min(max_length + 2, 30)
                col_letter = get_column_letter(col[0].column)
                ws_graficas.column_dimensions[col_letter].width = adjusted_width
        
        # ===== HOJA 3: RESUMEN ESTADÍSTICAS =====
        ws_resumen = wb.create_sheet("Resumen")
        
        # Título
        ws_resumen['A1'] = "REPORTE DE PEDIDOS ENTREGADOS - RESUMEN"
        ws_resumen['A1'].font = Font(bold=True, size=16)
        ws_resumen.merge_cells('A1:F1')
        ws_resumen['A1'].alignment = Alignment(horizontal="center")
        
        ws_resumen['A2'] = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        ws_resumen.merge_cells('A2:F2')
        ws_resumen['A2'].alignment = Alignment(horizontal="center")
        
        # Estadísticas
        total_venta = sum(p.get('total', p.get('costo_total', p.get('importe', 0))) for p in pedidos_entregados)
        total_costo = sum(p.get('costo_total', p.get('costo_combustible', 0)) for p in pedidos_entregados)
        total_galones = sum(p.get('galones', 0) for p in pedidos_entregados)
        margen = total_venta - total_costo
        pct_margen = (margen / total_venta * 100) if total_venta > 0 else 0
        
        stats = [
            ["Total Pedidos", len(pedidos_entregados)],
            ["Total Galones", round(total_galones, 0)],
            ["Costo Total", f"C$ {round(total_costo, 2):,.2f}"],
            ["Venta Total", f"C$ {round(total_venta, 2):,.2f}"],
            ["Margen Bruto", f"C$ {round(margen, 2):,.2f}"],
            ["% Margen", f"{round(pct_margen, 1)}%"]
        ]
        
        for i, (label, value) in enumerate(stats, start=4):
            ws_resumen[f'A{i}'] = label
            ws_resumen[f'A{i}'].font = Font(bold=True)
            ws_resumen[f'B{i}'] = value
        
        # Ajustar anchos
        ws_resumen.column_dimensions['A'].width = 20
        ws_resumen.column_dimensions['B'].width = 25
        
        # Guardar archivo
        if not os.path.exists(CARPETA_EXCEL_REPORTES):
            os.makedirs(CARPETA_EXCEL_REPORTES, exist_ok=True)
        
        filename = f"pedidos_entregados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(CARPETA_EXCEL_REPORTES, filename)
        wb.save(filepath)
        
        print(f"[DEBUG] ✅ Archivo Excel guardado en: {filepath}")
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"[ERROR] api_exportar_excel: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


def api_exportar_pdf():
    """Exporta los pedidos entregados a PDF con gráficas"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, A4, letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.units import inch
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.charts.legends import Legend
        from reportlab.graphics.widgets.markers import makeMarker
        
        pedidos_entregados = obtener_pedidos_entregados()
        print(f"[DEBUG] Exportando PDF - Pedidos encontrados: {len(pedidos_entregados)}")
        print(f"[DEBUG] Carpeta PDF: {CARPETA_PDF_REPORTES}")
        
        if not pedidos_entregados:
            return jsonify({"ok": False, "error": "No hay pedidos entregados para exportar"}), 400
        
        if not os.path.exists(CARPETA_PDF_REPORTES):
            os.makedirs(CARPETA_PDF_REPORTES, exist_ok=True)
        
        filename = f"pedidos_entregados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(CARPETA_PDF_REPORTES, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=16, textColor=colors.HexColor("#f59e0b"))
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10, textColor=colors.grey)
        header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor("#f59e0b"), alignment=TA_LEFT)
        
        # Estadísticas
        total_pedidos = len(pedidos_entregados)
        total_galones = sum(p.get('galones', 0) for p in pedidos_entregados)
        total_venta = sum(p.get('total', p.get('costo_total', p.get('importe', 0))) for p in pedidos_entregados)
        total_costo = sum(p.get('costo_total', p.get('costo_combustible', 0)) for p in pedidos_entregados)
        total_margen = total_venta - total_costo
        pct_margen = (total_margen / total_venta * 100) if total_venta > 0 else 0
        
        elements = []
        
        # Título
        elements.append(Paragraph("REPORTE DE PEDIDOS ENTREGADOS", title_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", subtitle_style))
        elements.append(Spacer(1, 12))
        
        # Estadísticas en tabla
        stats_data = [
            ["Total Pedidos", "Total Galones", "Costo Total", "Venta Total", "Margen Bruto", "% Margen"],
            [str(total_pedidos), f"{total_galones:,.0f}", f"C$ {total_costo:,.2f}", f"C$ {total_venta:,.2f}", f"C$ {total_margen:,.2f}", f"{pct_margen:.1f}%"]
        ]
        stats_table = Table(stats_data, colWidths=[1.2*inch]*6)
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f59e0b")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#f9f9f9")),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 16))
        
        # ===== GRÁFICA 1: Evolución Ventas vs Costo =====
        elements.append(Paragraph("EVOLUCIÓN VENTAS VS COSTO (Últimos 7 días)", header_style))
        elements.append(Spacer(1, 6))
        
        fechas_group = {}
        for p in pedidos_entregados:
            fecha_str = p.get('fecha_entrega', p.get('fecha_str', ''))
            if fecha_str:
                fecha_key = fecha_str[:10]
                if fecha_key not in fechas_group:
                    fechas_group[fecha_key] = {"costo": 0, "venta": 0}
                fechas_group[fecha_key]["costo"] += p.get('costo_total', p.get('costo_combustible', 0))
                fechas_group[fecha_key]["venta"] += p.get('total', p.get('costo_total', p.get('importe', 0)))
        
        fechas_ordenadas = sorted(fechas_group.keys())[-7:]
        
        if fechas_ordenadas:
            drawing1 = Drawing(400, 200)
            bc1 = VerticalBarChart()
            bc1.x = 50
            bc1.y = 50
            bc1.width = 300
            bc1.height = 120
            bc1.data = [
                [fechas_group[f]["costo"] for f in fechas_ordenadas],
                [fechas_group[f]["venta"] for f in fechas_ordenadas]
            ]
            bc1.categoryAxis.categoryNames = [f[5:] for f in fechas_ordenadas]
            bc1.categoryAxis.labels.boxAnchor = 'ne'
            bc1.categoryAxis.labels.dx = 0
            bc1.categoryAxis.labels.dy = 0
            bc1.categoryAxis.labels.angle = 0
            bc1.categoryAxis.labels.fontSize = 6
            bc1.valueAxis.valueMin = 0
            bc1.valueAxis.valueMax = max(max(fechas_group[f]["venta"] for f in fechas_ordenadas), 1) * 1.1
            bc1.valueAxis.labels.fontSize = 6
            bc1.bars[0].fillColor = colors.HexColor("#ef4444")
            bc1.bars[1].fillColor = colors.HexColor("#10b981")
            try:
                bc1.legend.fontSize = 7
                bc1.legend.alignment = TA_CENTER
            except:
                pass
            drawing1.add(bc1)
            elements.append(drawing1)
            elements.append(Spacer(1, 8))
        
        # ===== GRÁFICA 2: Top Clientes =====
        elements.append(Paragraph("TOP CLIENTES POR GALONES", header_style))
        elements.append(Spacer(1, 6))
        
        vol_cliente = {}
        for p in pedidos_entregados:
            nombre = p.get('nombre', p.get('empresa_nombre', 'Desconocido'))[:15]
            vol_cliente[nombre] = vol_cliente.get(nombre, 0) + p.get('galones', 0)
        
        top_clientes = sorted(vol_cliente.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if top_clientes:
            drawing2 = Drawing(400, 180)
            bc2 = VerticalBarChart()
            bc2.x = 50
            bc2.y = 50
            bc2.width = 300
            bc2.height = 100
            bc2.data = [[v for _, v in top_clientes]]
            bc2.categoryAxis.categoryNames = [c[:10] + "..." if len(c) > 10 else c for c, _ in top_clientes]
            bc2.categoryAxis.labels.boxAnchor = 'ne'
            bc2.categoryAxis.labels.dx = 0
            bc2.categoryAxis.labels.dy = 0
            bc2.categoryAxis.labels.angle = 0
            bc2.categoryAxis.labels.fontSize = 6
            bc2.valueAxis.valueMin = 0
            bc2.valueAxis.labels.fontSize = 6
            bc2.bars[0].fillColor = colors.HexColor("#f59e0b")
            try:
                bc2.legend.fontSize = 7
            except:
                pass
            drawing2.add(bc2)
            elements.append(drawing2)
            elements.append(Spacer(1, 8))
        
        # ===== GRÁFICA 3: Margen por Cliente (Pie) =====
        elements.append(Paragraph("MARGEN POR CLIENTE", header_style))
        elements.append(Spacer(1, 6))
        
        margen_cliente = {}
        for p in pedidos_entregados:
            nombre = p.get('nombre', p.get('empresa_nombre', 'Desconocido'))[:15]
            venta = p.get('total', p.get('costo_total', p.get('importe', 0)))
            costo = p.get('costo_total', p.get('costo_combustible', 0))
            margen = venta - costo
            if margen > 0:
                margen_cliente[nombre] = margen_cliente.get(nombre, 0) + margen
        
        top_margen = sorted(margen_cliente.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if top_margen:
            drawing3 = Drawing(400, 180)
            pie = Pie()
            pie.x = 150
            pie.y = 20
            pie.width = 150
            pie.height = 150
            pie.data = [v for _, v in top_margen]
            pie.labels = [c[:10] + "..." if len(c) > 10 else c for c, _ in top_margen]
            pie.fontSize = 7
            pie.slices.strokeWidth = 0.5
            pie.slices[0].fillColor = colors.HexColor("#f59e0b")
            pie.slices[1].fillColor = colors.HexColor("#10b981")
            pie.slices[2].fillColor = colors.HexColor("#8b5cf6")
            pie.slices[3].fillColor = colors.HexColor("#ef4444")
            pie.slices[4].fillColor = colors.HexColor("#06b6d4")
            drawing3.add(pie)
            elements.append(drawing3)
            elements.append(Spacer(1, 8))
        
        # ===== TABLA DE PEDIDOS (CON TODAS LAS COLUMNAS PRINCIPALES) =====
        elements.append(Paragraph("DETALLE DE PEDIDOS", header_style))
        elements.append(Spacer(1, 6))
        
        table_data = [["ID", "Empresa", "Fecha", "Galones", "Venta", "Conductor"]]
        for p in pedidos_entregados[:50]:
            table_data.append([
                p.get('id', '')[:15],
                p.get('nombre', p.get('empresa_nombre', ''))[:20],
                p.get('fecha_entrega', p.get('fecha_str', ''))[:10],
                str(p.get('galones', 0)),
                f"C$ {p.get('total', p.get('costo_total', p.get('importe', 0))):,.2f}",
                p.get('conductor_asignado', '')[:15]
            ])
        
        if len(pedidos_entregados) > 50:
            table_data.append(["", "", "", "", f"... {len(pedidos_entregados) - 50} más", ""])
        
        tabla = Table(table_data, colWidths=[1.2*inch, 2.5*inch, 1.5*inch, 1*inch, 1.5*inch, 1.5*inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f59e0b")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,1), (-1,-1), 7),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(tabla)
        
        # Footer
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Reporte generado automáticamente - Grupo GSN", subtitle_style))
        
        doc.build(elements)
        print(f"[DEBUG] ✅ Archivo PDF guardado en: {filepath}")
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"[ERROR] api_exportar_pdf: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


def api_descargar_reporte():
    try:
        filename = request.args.get('filename', '')
        if not filename:
            return jsonify({"ok": False, "error": "Nombre de archivo requerido"}), 400
        
        for carpeta in [CARPETA_EXCEL_REPORTES, CARPETA_PDF_REPORTES]:
            if carpeta:
                filepath = os.path.join(carpeta, filename)
                if os.path.exists(filepath):
                    return send_file(filepath, as_attachment=True, download_name=filename)
        
        return jsonify({"ok": False, "error": "Archivo no encontrado"}), 404
    except Exception as e:
        print(f"[ERROR] api_descargar_reporte: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


def api_estadisticas_avanzadas():
    """Estadísticas avanzadas para reportes"""
    try:
        pedidos_entregados = obtener_pedidos_entregados()
        
        ventas_por_mes = {}
        galones_por_mes = {}
        
        for p in pedidos_entregados:
            try:
                fecha_str = p.get('fecha_entrega', p.get('fecha_str', p.get('fecha', '')))
                if fecha_str:
                    mes = fecha_str[:7]
                    venta = p.get('total', p.get('costo_total', p.get('importe', 0)))
                    galones = p.get('galones', 0)
                    
                    ventas_por_mes[mes] = ventas_por_mes.get(mes, 0) + venta
                    galones_por_mes[mes] = galones_por_mes.get(mes, 0) + galones
            except:
                pass
        
        top_empresas = {}
        for p in pedidos_entregados:
            empresa = p.get('nombre', p.get('empresa_nombre', 'Desconocido'))
            venta = p.get('total', p.get('costo_total', p.get('importe', 0)))
            top_empresas[empresa] = top_empresas.get(empresa, 0) + venta
        
        top_empresas_lista = sorted(top_empresas.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return jsonify({
            "ok": True,
            "estadisticas": {
                "ventas_por_mes": ventas_por_mes,
                "galones_por_mes": galones_por_mes,
                "top_empresas": [{"nombre": k, "total": v} for k, v in top_empresas_lista]
            }
        })
    except Exception as e:
        print(f"[ERROR] api_estadisticas_avanzadas: {e}")
        return jsonify({"ok": False, "error": str(e)})