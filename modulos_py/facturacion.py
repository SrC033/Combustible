# ==================== MÓDULO FACTURACIÓN - CORREGIDO COMPLETO ====================
import os
import random
import json
import re
import time
import shutil
import threading
from datetime import datetime
from flask import jsonify, request, send_file, send_from_directory

# Intentar importar reportlab (opcional)
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_DISPONIBLE = True
except ImportError:
    REPORTLAB_DISPONIBLE = False
    print("[WARN] ReportLab no disponible")

# ==================== CONFIGURACIÓN ====================
ARCHIVO_PEDIDOS = None
ARCHIVO_FACTURAS = None
ARCHIVO_PEDIDOS_FACTURACION = None
CARPETA_PDF_FACTURAS = None
ARCHIVO_PERMISOS_FACTURAS = None

_cargar_json = None
_guardar_json = None
_enviar_factura_correo = None
_obtener_empresa = None

CONFIG_FACTURA_PATH = None
CONFIG_CAMPOS_ADICIONALES_PATH = None

# Estados de operación
ESTADO_ESPERA = 'espera'
ESTADO_COMPROBANTE = 'comprobante'
ESTADO_CAMINO = 'camino'
ESTADO_ENTREGADO = 'entregado'
ESTADO_FACTURACION = 'facturacion'

if REPORTLAB_DISPONIBLE:
    try:
        pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
        FUENTE_PRINCIPAL = 'Arial'
    except:
        FUENTE_PRINCIPAL = 'Helvetica'


# ==================== FUNCIONES DE PERSISTENCIA ====================
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


def obtener_empresa(empresa_id):
    if _obtener_empresa:
        return _obtener_empresa(empresa_id)
    return None


# ==================== INICIALIZACIÓN ====================
def inicializar_facturacion(carpeta_pdf, reportlab_disponible, main_funciones=None):
    global CARPETA_PDF_FACTURAS, CONFIG_FACTURA_PATH, CONFIG_CAMPOS_ADICIONALES_PATH
    global _cargar_json, _guardar_json, _enviar_factura_correo, _obtener_empresa
    global ARCHIVO_PERMISOS_FACTURAS
    
    CARPETA_PDF_FACTURAS = carpeta_pdf
    
    if main_funciones:
        _cargar_json = main_funciones.get('cargar_json')
        _guardar_json = main_funciones.get('guardar_json')
        _enviar_factura_correo = main_funciones.get('enviar_factura_correo')
        _obtener_empresa = main_funciones.get('obtener_empresa')
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CONFIG_FACTURA_PATH = os.path.join(base_dir, 'datos', 'config_factura.json')
    CONFIG_CAMPOS_ADICIONALES_PATH = os.path.join(base_dir, 'datos', 'campos_adicionales_factura.json')
    ARCHIVO_PERMISOS_FACTURAS = os.path.join(base_dir, 'datos', 'permisos_facturas.json')
    
    try:
        os.makedirs(os.path.dirname(CONFIG_FACTURA_PATH), exist_ok=True)
    except:
        pass
    
    # Asegurar que el archivo de permisos existe
    if not os.path.exists(ARCHIVO_PERMISOS_FACTURAS):
        guardar_json(ARCHIVO_PERMISOS_FACTURAS, {})
    
    print(f"[INFO] Módulo Facturación inicializado")


def configurar_archivos(pedidos, facturas, pedidos_facturacion):
    global ARCHIVO_PEDIDOS, ARCHIVO_FACTURAS, ARCHIVO_PEDIDOS_FACTURACION
    ARCHIVO_PEDIDOS = pedidos
    ARCHIVO_FACTURAS = facturas
    ARCHIVO_PEDIDOS_FACTURACION = pedidos_facturacion
    print(f"[DEBUG] Archivos configurados en facturación")


# ==================== CONFIGURACIÓN DE FACTURA ====================
def obtener_config_factura():
    config_default = {
        "empresa": {
            "nombre": "GRUPO GSN",
            "ruc": "J0310000012345",
            "telefono": "+505 2278 1234",
            "direccion": "Managua, Nicaragua",
            "email": "info@gruposn.com",
            "slogan": "Sistema de Gestión de Combustible"
        },
        "colores": {
            "primario": "#f59e0b",
            "titulo": "#f59e0b",
            "fondo": "#ffffff",
            "tablaHeader": "#f59e0b"
        },
        "visibles": {
            "mostrarSlogan": True,
            "mostrarRuc": True,
            "mostrarTelefono": True,
            "mostrarEmail": True,
            "mostrarDireccion": True
        },
        "camposAdicionales": []
    }
    try:
        if os.path.exists(CONFIG_FACTURA_PATH):
            with open(CONFIG_FACTURA_PATH, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    for key in config_default:
                        if key in saved:
                            if isinstance(config_default[key], dict) and isinstance(saved[key], dict):
                                config_default[key].update(saved[key])
                            else:
                                config_default[key] = saved[key]
    except Exception as e:
        print(f"Error cargando config factura: {e}")
    
    try:
        if os.path.exists(CONFIG_CAMPOS_ADICIONALES_PATH):
            with open(CONFIG_CAMPOS_ADICIONALES_PATH, 'r', encoding='utf-8') as f:
                campos = json.load(f)
                if isinstance(campos, list):
                    config_default["camposAdicionales"] = campos
    except Exception as e:
        print(f"Error cargando campos adicionales: {e}")
    
    return config_default


def guardar_config_factura(config):
    try:
        campos_adicionales = config.pop("camposAdicionales", [])
        
        with open(CONFIG_FACTURA_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        with open(CONFIG_CAMPOS_ADICIONALES_PATH, 'w', encoding='utf-8') as f:
            json.dump(campos_adicionales, f, indent=2, ensure_ascii=False)
        
        config["camposAdicionales"] = campos_adicionales
        return True
    except Exception as e:
        print(f"Error guardando config factura: {e}")
        return False


def hex_to_rgb(hex_color):
    if not hex_color:
        return colors.HexColor("#f59e0b")
    hex_color = hex_color.lstrip('#')
    return colors.HexColor(f"#{hex_color}")


def obtener_valor_numerico(valor):
    if valor is None:
        return 0
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        if valor.strip() == '':
            return 0
        try:
            limpio = re.sub(r'[^0-9.,-]', '', valor)
            limpio = limpio.replace(',', '.')
            return float(limpio)
        except:
            return 0
    return 0


# ==================== GENERAR PDF CON LAS FILAS GUARDADAS ====================
def generar_pdf_factura(factura_data, config, output_path):
    if not REPORTLAB_DISPONIBLE:
        print("[ERROR] ReportLab no disponible para generar PDF")
        return None
    
    try:
        # Asegurar que la carpeta existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Eliminar PDF antiguo si existe
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                print(f"[DEBUG] PDF antiguo eliminado: {output_path}")
            except PermissionError:
                temp_path = output_path + ".old_" + str(int(time.time()))
                shutil.move(output_path, temp_path)
                print(f"[DEBUG] PDF movido a: {temp_path}")
            except Exception as e:
                print(f"[WARN] No se pudo eliminar PDF: {e}")
        
        empresa = config.get("empresa", {})
        colores = config.get("colores", {})
        visibles = config.get("visibles", {})
        campos_adicionales_config = config.get("camposAdicionales", [])
        
        try:
            color_primario = hex_to_rgb(colores.get("primario", "#f59e0b"))
            color_titulo = hex_to_rgb(colores.get("titulo", "#f59e0b"))
        except:
            color_primario = colors.HexColor("#f59e0b")
            color_titulo = colors.HexColor("#f59e0b")
        
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                topMargin=1.5*cm, bottomMargin=1.5*cm,
                                leftMargin=1.8*cm, rightMargin=1.8*cm)
        
        styles = getSampleStyleSheet()
        
        estilo_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'],
                                        fontSize=20, textColor=color_titulo,
                                        alignment=TA_CENTER, fontName='Helvetica-Bold',
                                        spaceAfter=5)
        
        estilo_subtitulo = ParagraphStyle('Subtitulo', parent=styles['Normal'],
                                           fontSize=9, textColor=colors.gray,
                                           alignment=TA_CENTER, spaceAfter=3)
        
        estilo_normal = ParagraphStyle('Normal', parent=styles['Normal'],
                                        fontSize=9, leading=13)
        
        estilo_bold = ParagraphStyle('Bold', parent=styles['Normal'],
                                      fontSize=10, leading=14, fontName='Helvetica-Bold')
        
        estilo_total = ParagraphStyle('Total', parent=styles['Normal'],
                                       fontSize=14, textColor=color_titulo,
                                       fontName='Helvetica-Bold', alignment=TA_RIGHT,
                                       spaceAfter=10)
        
        # Estilo para campos adicionales - NEGRITA
        estilo_campo = ParagraphStyle('Campo', parent=styles['Normal'],
                                       fontSize=8, leading=11, 
                                       fontName='Helvetica-Bold',
                                       textColor=colors.black)
        
        elementos = []
        
        # Encabezado
        elementos.append(Paragraph(empresa.get("nombre", "GRUPO GSN"), estilo_titulo))
        
        if visibles.get("mostrarSlogan", True) and empresa.get("slogan"):
            elementos.append(Paragraph(empresa.get("slogan", ""), estilo_subtitulo))
        
        contacto = []
        if visibles.get("mostrarRuc", True):
            contacto.append(f"RUC: {empresa.get('ruc', 'J0310000012345')}")
        if visibles.get("mostrarTelefono", True):
            contacto.append(f"Tel: {empresa.get('telefono', '+505 2278 1234')}")
        if contacto:
            elementos.append(Paragraph(" | ".join(contacto), estilo_subtitulo))
        
        if visibles.get("mostrarDireccion", True):
            elementos.append(Paragraph(empresa.get("direccion", "Managua, Nicaragua"), estilo_subtitulo))
        
        if visibles.get("mostrarEmail", True):
            elementos.append(Paragraph(empresa.get("email", "info@gruposn.com"), estilo_subtitulo))
        
        elementos.append(Spacer(1, 0.3*cm))
        elementos.append(Paragraph(f"FACTURA No. {factura_data.get('id', 'N/A')}", estilo_bold))
        elementos.append(Paragraph(f"Fecha: {factura_data.get('fecha_emision_str', datetime.now().strftime('%d/%m/%Y %H:%M'))}", estilo_normal))
        elementos.append(Spacer(1, 0.3*cm))
        elementos.append(Paragraph("-" * 80, estilo_subtitulo))
        elementos.append(Spacer(1, 0.3*cm))
        
        # Datos del cliente
        nombre_cliente = factura_data.get('empresa_nombre', 'Cliente')
        nit_cliente = factura_data.get('empresa_nit', '-')
        
        data_cliente = [
            ["EMISOR", "CLIENTE"],
            [empresa.get("nombre", "GRUPO GSN"), nombre_cliente],
            [empresa.get("direccion", "Managua, Nicaragua"), f"NIT: {nit_cliente}"]
        ]
        
        tabla_cliente = Table(data_cliente, colWidths=[230, 230])
        tabla_cliente.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), FUENTE_PRINCIPAL),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        elementos.append(tabla_cliente)
        elementos.append(Spacer(1, 0.2*cm))
        
        # Conductores y camiones
        datos_flota = []
        if factura_data.get('conductor_asignado') and factura_data.get('conductor_asignado') != '-':
            datos_flota.append(f"Conductor: {factura_data.get('conductor_asignado')}")
        if factura_data.get('conductor2_asignado') and factura_data.get('conductor2_asignado') != '-':
            datos_flota.append(f"Conductor 2: {factura_data.get('conductor2_asignado')}")
        if factura_data.get('camion_asignado') and factura_data.get('camion_asignado') != '-':
            datos_flota.append(f"Placa: {factura_data.get('camion_asignado')}")
        if factura_data.get('camion2_asignado') and factura_data.get('camion2_asignado') != '-':
            datos_flota.append(f"Placa 2: {factura_data.get('camion2_asignado')}")
        
        if datos_flota:
            elementos.append(Paragraph(" | ".join(datos_flota), estilo_normal))
            elementos.append(Spacer(1, 0.2*cm))
        
        elementos.append(Paragraph("-" * 80, estilo_subtitulo))
        elementos.append(Spacer(1, 0.3*cm))
        
        # ==================== CAMPOS ADICIONALES (EN NEGRITA) ====================
        campos_adicionales_data = factura_data.get('campos_adicionales', {})
        campos_visibles = [c for c in campos_adicionales_config if c.get('visible') != False]
        
        if campos_visibles and any(campos_adicionales_data.get(c.get('label')) for c in campos_visibles):
            textos_campos = []
            for campo in campos_visibles:
                label = campo.get('label', '')
                valor = campos_adicionales_data.get(label, '')
                if valor:
                    textos_campos.append(f"{label}: {valor}")
            if textos_campos:
                elementos.append(Paragraph(" | ".join(textos_campos), estilo_campo))
                elementos.append(Spacer(1, 0.2*cm))
        
        # ==================== TABLA DINÁMICA DE PRODUCTOS ====================
        filas = factura_data.get('filas', [])
        
        print(f"[DEBUG] Generando PDF con {len(filas)} filas:")
        for i, fila in enumerate(filas):
            print(f"  Fila {i+1}: {fila.get('descripcion')} - Cantidad: {fila.get('cantidad')} - Precio: {fila.get('precio')}")
        
        if not filas:
            print("[DEBUG] No hay filas, creando una por defecto")
            galones = obtener_valor_numerico(factura_data.get('galones', 0))
            precio = obtener_valor_numerico(factura_data.get('precio_por_galon', 0))
            origen = factura_data.get('origen_editado', factura_data.get('origen', 'Managua')) or 'Managua'
            destino = factura_data.get('destino_editado', factura_data.get('destino', 'León')) or 'León'
            tipo = factura_data.get('tipo_combustible_editado', factura_data.get('tipo_combustible', 'Combustible')) or 'Combustible'
            
            filas = [{
                'descripcion': f"{tipo}\n{origen} → {destino}",
                'cantidad': galones,
                'precio': precio,
                'total': galones * precio
            }]
        
        tabla_data = [['Descripción', 'Cantidad', 'Precio Unitario', 'Total']]
        
        for fila in filas:
            descripcion = fila.get('descripcion', 'Producto')
            cantidad = obtener_valor_numerico(fila.get('cantidad', 0))
            precio = obtener_valor_numerico(fila.get('precio', 0))
            total = cantidad * precio
            
            cantidad_str = str(cantidad)
            if cantidad < 0:
                cantidad_str = f"({abs(cantidad)})"
            
            if len(descripcion) > 50:
                desc_para = Paragraph(descripcion.replace('\n', '<br/>'), estilo_normal)
            else:
                desc_para = descripcion
            
            tabla_data.append([
                desc_para,
                cantidad_str,
                f"C$ {precio:,.2f}",
                f"C$ {total:,.2f}"
            ])
        
        # ============ COSTO DE TRASLADO - OCULTO EN EL PDF ============
        # El costo de traslado NO se muestra como fila en la tabla
        # Solo se usa para calcular el total
        costo_traslado = obtener_valor_numerico(factura_data.get('costo_traslado', 0))
        
        col_widths = [230, 70, 90, 90]
        tabla = Table(tabla_data, colWidths=col_widths, repeatRows=1)
        
        tabla_style = [
            ('BACKGROUND', (0,0), (-1,0), color_primario),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),
            ('VALIGN', (0,1), (-1,-1), 'TOP'),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('TOPPADDING', (0,1), (-1,-1), 6),
            ('BOTTOMPADDING', (0,1), (-1,-1), 6),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
            ('ALIGN', (0,1), (0,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
        ]
        
        tabla.setStyle(TableStyle(tabla_style))
        elementos.append(tabla)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Calcular total general (incluyendo costo de traslado pero sin mostrarlo)
        total_general = 0
        for fila in filas:
            total_general += obtener_valor_numerico(fila.get('cantidad', 0)) * obtener_valor_numerico(fila.get('precio', 0))
        total_general += costo_traslado
        
        elementos.append(Paragraph(f"TOTAL A PAGAR:  C$ {total_general:,.2f}", estilo_total))
        
        # Pie de página
        elementos.append(Spacer(1, 0.5*cm))
        elementos.append(Paragraph("-" * 80, estilo_subtitulo))
        elementos.append(Spacer(1, 0.3*cm))
        elementos.append(Paragraph("Gracias por su preferencia. Este documento es un comprobante de pago.", estilo_normal))
        elementos.append(Paragraph("Grupo GSN - Nicaragua", estilo_normal))
        
        doc.build(elementos)
        
        # Verificar que el PDF se creó correctamente
        if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
            print(f"[DEBUG] ✅ PDF generado: {output_path} (tamaño: {os.path.getsize(output_path)} bytes)")
            return output_path
        else:
            print(f"[ERROR] ❌ PDF no se generó correctamente o está vacío")
            return None
        
    except Exception as e:
        print(f"[ERROR] Error generando PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


# ==================== API ENDPOINTS ====================
def api_guardar_config_factura():
    try:
        data = request.get_json()
        if guardar_config_factura(data):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Error al guardar"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_obtener_config_factura():
    try:
        config = obtener_config_factura()
        return jsonify({"ok": True, "config": config})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_facturar_pedidos():
    try:
        data = request.get_json()
        pedidos_ids = data.get('pedidos_ids', [])
        empresa_nombre_cliente = data.get('empresa_nombre_cliente', '')
        empresa_id = data.get('empresa_id', '')
        empresa_nit = data.get('empresa_nit', '')
        email_cliente = data.get('email_cliente', '')
        total_editado = data.get('total_editado', 0)
        
        filas = data.get('filas', [])
        campos_adicionales = data.get('campos_adicionales', {})
        datos_editados = data.get('datos_editados', {})
        
        print(f"[DEBUG] ===== FACTURANDO PEDIDO =====")
        print(f"[DEBUG] Filas recibidas: {len(filas)}")
        for i, fila in enumerate(filas):
            print(f"  Fila {i+1}: {fila.get('descripcion')} - Cantidad: {fila.get('cantidad')} - Precio: {fila.get('precio')}")
        print(f"[DEBUG] Campos adicionales: {campos_adicionales}")
        
        pedidos_facturacion = cargar_json(ARCHIVO_PEDIDOS_FACTURACION, [])
        pedidos_sel = [p for p in pedidos_facturacion if p.get('id') in pedidos_ids]
        
        if not pedidos_sel:
            pedidos_originales = cargar_json(ARCHIVO_PEDIDOS, [])
            pedidos_sel = [p for p in pedidos_originales if p.get('id') in pedidos_ids]
        
        if not pedidos_sel:
            return jsonify({"ok": False, "error": "No se encontraron pedidos"})
        
        pedido = pedidos_sel[0]
        
        # Usar datos del pedido original para conductores, camiones, bonos, viáticos y costo_traslado
        conductor_asignado = pedido.get('conductor_asignado', '')
        conductor2_asignado = pedido.get('conductor2_asignado', '')
        camion_asignado = pedido.get('camion_asignado', '')
        camion2_asignado = pedido.get('camion2_asignado', '')
        bono1 = pedido.get('bono1', '')
        bono2 = pedido.get('bono2', '')
        viatico1 = pedido.get('viatico1', 0)
        viatico2 = pedido.get('viatico2', 0)
        costo_traslado = pedido.get('costo_traslado', 0)
        
        # Si hay datos_editados con conductores/camiones, usarlos
        if datos_editados.get('conductor_asignado'):
            conductor_asignado = datos_editados.get('conductor_asignado')
        if datos_editados.get('conductor2_asignado'):
            conductor2_asignado = datos_editados.get('conductor2_asignado')
        if datos_editados.get('camion_asignado'):
            camion_asignado = datos_editados.get('camion_asignado')
        if datos_editados.get('camion2_asignado'):
            camion2_asignado = datos_editados.get('camion2_asignado')
        
        # Calcular total
        total_pdf = 0
        for fila in filas:
            cantidad = obtener_valor_numerico(fila.get('cantidad', 0))
            precio = obtener_valor_numerico(fila.get('precio', 0))
            total_pdf += cantidad * precio
        total_pdf += obtener_valor_numerico(costo_traslado)
        
        if total_editado > 0:
            total_pdf = total_editado
        
        factura_id = f"FAC-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"
        config = obtener_config_factura()
        
        factura_data = {
            "id": factura_id,
            "empresa_nombre": empresa_nombre_cliente or pedido.get('nombre', 'Cliente'),
            "empresa_id": empresa_id or pedido.get('empresa_id', ''),
            "empresa_nit": empresa_nit or pedido.get('cedula', ''),
            "empresa_telefono_cliente": email_cliente,
            "pedidos": [pedido],
            "galones": sum(f.get('cantidad', 0) for f in filas if f.get('cantidad', 0) > 0),
            "precio_por_galon": filas[0].get('precio', 0) if filas else 0,
            "costo_traslado": float(costo_traslado),
            "distancia_km": pedido.get('distancia_km', 0),
            "costo_km": pedido.get('costo_km', 0),
            "tipo_combustible": "MÚLTIPLE" if len(filas) > 1 else (filas[0].get('descripcion', 'Producto') if filas else 'Producto'),
            "origen": "",
            "destino": "",
            "conductor_asignado": conductor_asignado,
            "conductor2_asignado": conductor2_asignado,
            "camion_asignado": camion_asignado,
            "camion2_asignado": camion2_asignado,
            "bono1": bono1,
            "bono2": bono2,
            "viatico1": float(viatico1),
            "viatico2": float(viatico2),
            "total": round(total_pdf, 2),
            "total_preview": round(total_editado if total_editado > 0 else total_pdf, 2),
            "fecha_emision": datetime.now().isoformat(),
            "fecha_emision_str": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "pagada": False,
            "campos_adicionales": campos_adicionales,
            "datos_editados": datos_editados,
            "fecha_recepcion": pedido.get('fecha', datetime.now().isoformat()),
            "pedido_id": pedidos_ids[0] if pedidos_ids else None,
            "filas": filas,
            "estado_factura": ESTADO_ENTREGADO,
            "entregado": True
        }
        
        os.makedirs(CARPETA_PDF_FACTURAS, exist_ok=True)
        ruta_pdf = os.path.join(CARPETA_PDF_FACTURAS, f"{factura_id}.pdf")
        
        resultado = generar_pdf_factura(factura_data, config, ruta_pdf)
        
        if resultado and os.path.exists(ruta_pdf) and os.path.getsize(ruta_pdf) > 500:
            facturas = cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
            if isinstance(facturas, list):
                facturas = {"facturas": facturas}
            if "facturas" not in facturas:
                facturas["facturas"] = []
            facturas["facturas"].append(factura_data)
            guardar_json(ARCHIVO_FACTURAS, facturas)
            
            # ============ CORRECCIÓN: Actualizar el pedido original ============
            # 1. Eliminar de pedidos_facturacion
            pedidos_facturacion_actualizados = [p for p in pedidos_facturacion if p.get('id') not in pedidos_ids]
            guardar_json(ARCHIVO_PEDIDOS_FACTURACION, pedidos_facturacion_actualizados)
            
            # 2. ACTUALIZAR el pedido en pedidos.json a estado ENTREGADO
            pedidos_originales = cargar_json(ARCHIVO_PEDIDOS, [])
            pedidos_actualizados = []
            pedido_actualizado = None
            
            for p in pedidos_originales:
                if p.get('id') in pedidos_ids:
                    # Crear una copia actualizada del pedido
                    pedido_actualizado = p.copy()
                    pedido_actualizado['estado_operacion'] = ESTADO_ENTREGADO
                    pedido_actualizado['facturado'] = True
                    pedido_actualizado['fecha_facturacion'] = datetime.now().isoformat()
                    pedido_actualizado['factura_id'] = factura_id
                    pedido_actualizado['factura_total'] = round(total_pdf, 2)
                    pedidos_actualizados.append(pedido_actualizado)
                    print(f"[DEBUG] ✅ Pedido {p.get('id')} actualizado a estado ENTREGADO")
                else:
                    pedidos_actualizados.append(p)
            
            guardar_json(ARCHIVO_PEDIDOS, pedidos_actualizados)
            print(f"[DEBUG] ✅ Pedidos actualizados en archivo principal: {len(pedidos_actualizados)}")
            
            # ============ INICIALIZAR PERMISO DE FACTURA ============
            # Por defecto, la factura es visible (permiso = True)
            try:
                if ARCHIVO_PERMISOS_FACTURAS:
                    permisos = cargar_json(ARCHIVO_PERMISOS_FACTURAS, {})
                    permisos[factura_id] = True
                    guardar_json(ARCHIVO_PERMISOS_FACTURAS, permisos)
                    print(f"[DEBUG] ✅ Permiso inicializado para {factura_id}: True (visible)")
            except Exception as e:
                print(f"[WARN] Error inicializando permiso: {e}")
            
            # ============ FIN CORRECCIÓN ============
            
            # Notificar a Reportes
            try:
                import requests
                requests.post('http://localhost:5000/api/reportes/recargar', json={}, timeout=2)
                print(f"[DEBUG] Notificación enviada a Reportes")
            except Exception as e:
                print(f"[WARN] Error notificando a Reportes: {e}")
            
            print(f"[DEBUG] ✅ Factura {factura_id} generada exitosamente")
            return jsonify({"ok": True, "factura_id": factura_id, "total": total_pdf})
        
        return jsonify({"ok": False, "error": "Error generando factura"})
    except Exception as e:
        print(f"[ERROR] api_facturar_pedidos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


def api_facturas_lista():
    try:
        facturas = cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
        if isinstance(facturas, list):
            facturas = {"facturas": facturas}
        if not isinstance(facturas, dict):
            facturas = {"facturas": []}
        if "facturas" not in facturas:
            facturas["facturas"] = []
        facturas_lista = facturas.get("facturas", [])
        facturas_lista.sort(key=lambda x: x.get('fecha_emision', ''), reverse=True)
        return jsonify({"facturas": facturas_lista})
    except Exception as e:
        print(f"[ERROR] api_facturas_lista: {e}")
        return jsonify({"facturas": []})


def descargar_factura(factura_id):
    try:
        carpeta = CARPETA_PDF_FACTURAS
        print(f"[DEBUG] Buscando PDF para factura: {factura_id} en {carpeta}")
        
        for f in os.listdir(carpeta):
            if factura_id in f and f.endswith('.pdf'):
                ruta_completa = os.path.join(carpeta, f)
                print(f"[DEBUG] PDF encontrado: {ruta_completa}")
                return send_from_directory(carpeta, f, as_attachment=False, download_name=f)
        
        print(f"[WARN] PDF no encontrado para {factura_id}, regenerando...")
        facturas = cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
        factura_data = None
        for f in facturas.get("facturas", []):
            if f.get("id") == factura_id:
                factura_data = f
                break
        
        if factura_data:
            config = obtener_config_factura()
            ruta_pdf = os.path.join(CARPETA_PDF_FACTURAS, f"{factura_id}.pdf")
            resultado = generar_pdf_factura(factura_data, config, ruta_pdf)
            if resultado and os.path.exists(ruta_pdf):
                return send_from_directory(CARPETA_PDF_FACTURAS, f"{factura_id}.pdf", as_attachment=False)
        
        return jsonify({"error": "Factura no encontrada"}), 404
    except Exception as e:
        print(f"[ERROR] descargar_factura: {e}")
        return jsonify({"error": str(e)}), 500


def api_enviar_factura_correo():
    try:
        data = request.get_json()
        factura_id = data.get('factura_id')
        email = data.get('email')
        empresa_nombre = data.get('empresa_nombre', 'Cliente')
        
        facturas = cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
        factura = None
        for f in facturas.get("facturas", []):
            if f.get('id') == factura_id:
                factura = f
                break
        
        if not factura:
            return jsonify({"ok": False, "error": "Factura no encontrada"})
        
        pdf_path = None
        if os.path.exists(CARPETA_PDF_FACTURAS):
            for f in os.listdir(CARPETA_PDF_FACTURAS):
                if factura_id in f and f.endswith('.pdf'):
                    pdf_path = os.path.join(CARPETA_PDF_FACTURAS, f)
                    break
        
        if not pdf_path:
            config = obtener_config_factura()
            pdf_path = os.path.join(CARPETA_PDF_FACTURAS, f"{factura_id}.pdf")
            generar_pdf_factura(factura, config, pdf_path)
        
        if not os.path.exists(pdf_path):
            return jsonify({"ok": False, "error": "PDF no encontrado"})
        
        if _enviar_factura_correo:
            return _enviar_factura_correo(email, empresa_nombre, pdf_path, factura)
        
        return jsonify({"ok": False, "error": "Correo no configurado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_actualizar_pedido():
    try:
        data = request.get_json()
        pedido_id = data.get('id')
        nuevos_datos = data.get('datos', {})
        
        if not pedido_id:
            return jsonify({"ok": False, "error": "ID de pedido no proporcionado"})
        
        pedidos = cargar_json(ARCHIVO_PEDIDOS, [])
        encontrado = False
        
        for p in pedidos:
            if p.get('id') == pedido_id:
                for key, value in nuevos_datos.items():
                    p[key] = value
                encontrado = True
                break
        
        if encontrado:
            guardar_json(ARCHIVO_PEDIDOS, pedidos)
            return jsonify({"ok": True})
        else:
            return jsonify({"ok": False, "error": "Pedido no encontrado"})
    except Exception as e:
        print(f"[ERROR] api_actualizar_pedido: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_eliminar_pedido_facturacion():
    try:
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        
        if not pedido_id:
            return jsonify({"ok": False, "error": "ID de pedido no proporcionado"})
        
        pedidos_facturacion = cargar_json(ARCHIVO_PEDIDOS_FACTURACION, [])
        nuevos_pedidos = [p for p in pedidos_facturacion if p.get('id') != pedido_id]
        
        if len(nuevos_pedidos) != len(pedidos_facturacion):
            guardar_json(ARCHIVO_PEDIDOS_FACTURACION, nuevos_pedidos)
            return jsonify({"ok": True})
        else:
            return jsonify({"ok": False, "error": "Pedido no encontrado en cola"})
    except Exception as e:
        print(f"[ERROR] api_eliminar_pedido_facturacion: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_pedidos_facturacion():
    try:
        pedidos_facturacion = cargar_json(ARCHIVO_PEDIDOS_FACTURACION, [])
        return jsonify({"ok": True, "pedidos": pedidos_facturacion})
    except Exception as e:
        print(f"[ERROR] api_pedidos_facturacion: {e}")
        return jsonify({"ok": False, "error": str(e), "pedidos": []})


def api_limpiar_facturas():
    try:
        data = request.get_json() or {}
        confirmar = data.get('confirmar', False)
        
        if not confirmar:
            return jsonify({"ok": False, "error": "Se requiere confirmación"})
        
        facturas = cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
        if isinstance(facturas, list):
            facturas = {"facturas": facturas}
        
        cantidad = len(facturas.get("facturas", []))
        facturas["facturas"] = []
        guardar_json(ARCHIVO_FACTURAS, facturas)
        
        return jsonify({"ok": True, "limpiadas": cantidad, "mensaje": f"Se limpiaron {cantidad} facturas"})
    except Exception as e:
        print(f"[ERROR] api_limpiar_facturas: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_estado_limpieza():
    try:
        facturas = cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
        if isinstance(facturas, list):
            facturas = {"facturas": facturas}
        
        pdfs = []
        if os.path.exists(CARPETA_PDF_FACTURAS):
            pdfs = [f for f in os.listdir(CARPETA_PDF_FACTURAS) if f.endswith('.pdf')]
        
        return jsonify({
            "ok": True,
            "facturas_en_listado": len(facturas.get("facturas", [])),
            "pdfs_en_carpeta": len(pdfs)
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_factura(factura_id):
    try:
        facturas = cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
        if isinstance(facturas, list):
            facturas = {"facturas": facturas}
        
        for factura in facturas.get("facturas", []):
            if factura.get("id") == factura_id:
                return jsonify({"ok": True, "factura": factura})
        
        return jsonify({"ok": False, "error": "Factura no encontrada"}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


def api_limpieza_automatica():
    try:
        facturas = cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
        if isinstance(facturas, list):
            facturas = {"facturas": facturas}
        
        cantidad = len(facturas.get("facturas", []))
        facturas["facturas"] = []
        guardar_json(ARCHIVO_FACTURAS, facturas)
        
        return jsonify({"ok": True, "limpiadas": cantidad})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_mis_facturas_detalle(empresa_id):
    try:
        facturas = cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
        if isinstance(facturas, list):
            facturas = {"facturas": facturas}
        
        facturas_empresa = []
        for factura in facturas.get("facturas", []):
            if factura.get("empresa_id") == empresa_id or factura.get("empresa_nombre") == empresa_id:
                facturas_empresa.append(factura)
        
        facturas_empresa.sort(key=lambda x: x.get('fecha_emision', ''), reverse=True)
        
        return jsonify({"ok": True, "facturas": facturas_empresa})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "facturas": []}), 500


# ==================== ACTUALIZAR FACTURA EXISTENTE ====================
def api_actualizar_factura():
    """
    Actualiza una factura existente:
    1. ELIMINA la factura anterior del JSON
    2. GUARDA la nueva factura al final del array
    3. Regenera el PDF (sobrescribe el archivo)
    """
    try:
        data = request.get_json()
        factura_id = data.get('factura_id')
        datos_actualizados = data.get('datos', {})
        
        if not factura_id:
            return jsonify({"ok": False, "error": "ID de factura no proporcionado"})
        
        print(f"[DEBUG] ===== ACTUALIZANDO FACTURA: {factura_id} =====")
        
        # 1. Cargar configuración
        config = obtener_config_factura()
        
        # 2. Asegurar que la carpeta PDF existe
        os.makedirs(CARPETA_PDF_FACTURAS, exist_ok=True)
        
        # 3. Cargar facturas actuales
        facturas = cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
        if isinstance(facturas, list):
            facturas = {"facturas": facturas}
        if "facturas" not in facturas:
            facturas["facturas"] = []
        
        # 4. Buscar la factura original para obtener datos base
        factura_original = None
        for f in facturas.get("facturas", []):
            if f.get("id") == factura_id:
                factura_original = f
                break
        
        if not factura_original:
            return jsonify({"ok": False, "error": "Factura no encontrada"})
        
        print(f"[DEBUG] Factura original encontrada")
        
        # 5. Obtener las filas de la tabla
        filas = datos_actualizados.get('filas', factura_original.get('filas', []))
        campos_adicionales = datos_actualizados.get('campos_adicionales', factura_original.get('campos_adicionales', {}))
        
        print(f"[DEBUG] Filas recibidas para actualizar: {len(filas)}")
        print(f"[DEBUG] Campos adicionales: {campos_adicionales}")
        
        # Filtrar filas con cantidad 0
        filas_validas = []
        for fila in filas:
            cantidad = obtener_valor_numerico(fila.get('cantidad', 0))
            if cantidad != 0:
                filas_validas.append({
                    'descripcion': fila.get('descripcion', 'Producto'),
                    'cantidad': cantidad,
                    'precio': obtener_valor_numerico(fila.get('precio', 0)),
                    'total': cantidad * obtener_valor_numerico(fila.get('precio', 0))
                })
        
        if not filas_validas:
            filas_validas = [{
                'descripcion': 'Producto',
                'cantidad': 0,
                'precio': 0,
                'total': 0
            }]
        
        # Usar datos originales de la factura (NO se actualizan desde el frontend)
        costo_traslado = factura_original.get('costo_traslado', 0)
        bono1 = factura_original.get('bono1', '')
        bono2 = factura_original.get('bono2', '')
        viatico1 = factura_original.get('viatico1', 0)
        viatico2 = factura_original.get('viatico2', 0)
        conductor_asignado = factura_original.get('conductor_asignado', '')
        conductor2_asignado = factura_original.get('conductor2_asignado', '')
        camion_asignado = factura_original.get('camion_asignado', '')
        camion2_asignado = factura_original.get('camion2_asignado', '')
        
        # Calcular total
        total_final = 0
        for fila in filas_validas:
            total_final += fila['cantidad'] * fila['precio']
        total_final += costo_traslado
        
        print(f"[DEBUG] Total calculado: {total_final}")
        
        # 6. Construir la NUEVA factura
        nueva_factura = {
            "id": factura_id,
            "empresa_nombre": factura_original.get('empresa_nombre', 'Cliente'),
            "empresa_id": factura_original.get('empresa_id', ''),
            "empresa_nit": factura_original.get('empresa_nit', ''),
            "empresa_telefono_cliente": factura_original.get('empresa_telefono_cliente', ''),
            "pedidos": factura_original.get('pedidos', []),
            "galones": sum(f['cantidad'] for f in filas_validas if f['cantidad'] > 0),
            "precio_por_galon": filas_validas[0]['precio'] if filas_validas else 0,
            "costo_traslado": costo_traslado,
            "distancia_km": factura_original.get('distancia_km', 0),
            "costo_km": factura_original.get('costo_km', 0),
            "tipo_combustible": "MÚLTIPLE" if len(filas_validas) > 1 else (filas_validas[0].get('descripcion', 'Producto') if filas_validas else 'Producto'),
            "origen": "",
            "destino": "",
            "conductor_asignado": conductor_asignado,
            "conductor2_asignado": conductor2_asignado,
            "camion_asignado": camion_asignado,
            "camion2_asignado": camion2_asignado,
            "bono1": bono1,
            "bono2": bono2,
            "viatico1": float(viatico1),
            "viatico2": float(viatico2),
            "total": round(total_final, 2),
            "fecha_emision": factura_original.get('fecha_emision', datetime.now().isoformat()),
            "fecha_emision_str": factura_original.get('fecha_emision_str', datetime.now().strftime("%d/%m/%Y %H:%M")),
            "fecha_actualizacion": datetime.now().isoformat(),
            "pagada": factura_original.get('pagada', False),
            "campos_adicionales": campos_adicionales,
            "datos_editados": datos_actualizados.get('datos_editados', factura_original.get('datos_editados', {})),
            "fecha_recepcion": factura_original.get('fecha_recepcion', datetime.now().isoformat()),
            "pedido_id": factura_original.get('pedido_id'),
            "filas": filas_validas,
            "estado_factura": ESTADO_ENTREGADO,
            "entregado": True
        }
        
        # 7. ELIMINAR la factura anterior del array
        facturas["facturas"] = [f for f in facturas.get("facturas", []) if f.get("id") != factura_id]
        
        # 8. AGREGAR la nueva factura al final
        facturas["facturas"].append(nueva_factura)
        
        # 9. Guardar el JSON actualizado
        guardar_json(ARCHIVO_FACTURAS, facturas)
        print(f"[DEBUG] ✅ Factura {factura_id} ELIMINADA y NUEVA guardada con estado ENTREGADO")
        
        # 10. Regenerar PDF (sobrescribir el archivo)
        ruta_pdf = os.path.join(CARPETA_PDF_FACTURAS, f"{factura_id}.pdf")
        
        # Eliminar PDF antiguo si existe
        if os.path.exists(ruta_pdf):
            try:
                os.remove(ruta_pdf)
                print(f"[DEBUG] PDF antiguo eliminado: {ruta_pdf}")
            except Exception as e:
                print(f"[WARN] No se pudo eliminar PDF: {e}")
        
        # Generar nuevo PDF
        print(f"[DEBUG] Generando nuevo PDF: {ruta_pdf}")
        resultado = generar_pdf_factura(nueva_factura, config, ruta_pdf)
        
        # Verificar que el PDF se generó correctamente
        if resultado and os.path.exists(ruta_pdf) and os.path.getsize(ruta_pdf) > 500:
            print(f"[DEBUG] ✅ PDF regenerado exitosamente: {ruta_pdf}")
            
            # Notificar a Operaciones
            try:
                import requests
                if nueva_factura.get('pedido_id'):
                    requests.post(
                        'http://localhost:5000/api/actualizar_pedido_desde_factura',
                        json={
                            'pedido_id': nueva_factura.get('pedido_id'),
                            'factura_id': factura_id,
                            'nuevo_total': total_final,
                            'galones': nueva_factura.get('galones', 0),
                            'precio': nueva_factura.get('precio_por_galon', 0),
                            'costo_traslado': costo_traslado,
                            'filas': filas_validas
                        },
                        timeout=2
                    )
                    print(f"[DEBUG] Notificación enviada a Operaciones")
            except Exception as e:
                print(f"[WARN] Error notificando a Operaciones: {e}")
            
            # Notificar a Reportes
            try:
                import requests
                requests.post('http://localhost:5000/api/reportes/recargar', json={}, timeout=2)
                print(f"[DEBUG] Notificación enviada a Reportes")
            except Exception as e:
                print(f"[WARN] Error notificando a Reportes: {e}")
            
            return jsonify({"ok": True, "mensaje": "Factura actualizada correctamente", "total": total_final})
        else:
            print(f"[WARN] No se pudo generar el PDF, pero los datos se guardaron")
            return jsonify({"ok": True, "mensaje": "Factura actualizada (datos guardados)", "total": total_final})
        
    except Exception as e:
        print(f"[ERROR] api_actualizar_factura: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


# ==================== FUNCIONES PARA PERMISOS DE FACTURAS (CORREGIDO) ====================

def api_facturas_permitidas_cliente():
    """
    Obtiene las facturas permitidas para un cliente
    SOLO devuelve facturas con permiso EXPLÍCITAMENTE True
    """
    try:
        data = request.get_json() or {}
        empresa_id = data.get('empresa_id')
        
        if not empresa_id:
            return jsonify({"ok": False, "error": "Se requiere empresa_id", "facturas": []})
        
        print(f"[DEBUG] ===== FACTURAS PERMITIDAS =====")
        print(f"[DEBUG] Empresa ID: {empresa_id}")
        
        # 1. Cargar facturas
        facturas_data = cargar_json(ARCHIVO_FACTURAS, {"facturas": []})
        if isinstance(facturas_data, list):
            facturas_data = {"facturas": facturas_data}
        facturas = facturas_data.get("facturas", [])
        
        # 2. Cargar permisos
        if not os.path.exists(ARCHIVO_PERMISOS_FACTURAS):
            guardar_json(ARCHIVO_PERMISOS_FACTURAS, {})
        permisos = cargar_json(ARCHIVO_PERMISOS_FACTURAS, {})
        
        print(f"[DEBUG] Total facturas: {len(facturas)}")
        print(f"[DEBUG] Total permisos: {len(permisos)}")
        
        # 3. Filtrar facturas del cliente CON permiso EXPLÍCITAMENTE True
        facturas_permitidas = []
        facturas_ocultas = []
        
        for f in facturas:
            # Verificar si la factura pertenece al cliente
            es_cliente = (
                f.get("empresa_id") == empresa_id or 
                f.get("empresa_nombre") == empresa_id or
                f.get("cliente_id") == empresa_id or
                f.get("cliente_nombre") == empresa_id or
                (f.get("datos_editados") and f["datos_editados"].get("cliente_nombre") == empresa_id)
            )
            
            if es_cliente:
                factura_id = f.get("id")
                # Obtener permiso (por defecto False si no existe)
                tiene_permiso = permisos.get(factura_id, False)
                
                # Asegurar que sea booleano
                if isinstance(tiene_permiso, bool):
                    permitido = tiene_permiso
                else:
                    permitido = str(tiene_permiso).lower() == 'true'
                
                if permitido:
                    facturas_permitidas.append(f)
                    print(f"[DEBUG] ✅ Factura PERMITIDA: {factura_id}")
                else:
                    facturas_ocultas.append(factura_id)
                    print(f"[DEBUG] ❌ Factura OCULTA: {factura_id}")
        
        # 4. Ordenar por fecha
        facturas_permitidas.sort(key=lambda x: x.get('fecha_emision', ''), reverse=True)
        
        print(f"[DEBUG] Facturas permitidas: {len(facturas_permitidas)}")
        print(f"[DEBUG] Facturas ocultas: {len(facturas_ocultas)}")
        
        return jsonify({
            "ok": True, 
            "facturas": facturas_permitidas,
            "total_permitidas": len(facturas_permitidas),
            "total_ocultas": len(facturas_ocultas)
        })
    except Exception as e:
        print(f"[ERROR] api_facturas_permitidas_cliente: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e), "facturas": []})


def api_obtener_permisos():
    """
    Obtiene todos los permisos de facturas
    """
    try:
        if not os.path.exists(ARCHIVO_PERMISOS_FACTURAS):
            guardar_json(ARCHIVO_PERMISOS_FACTURAS, {})
        permisos = cargar_json(ARCHIVO_PERMISOS_FACTURAS, {})
        print(f"[DEBUG] Permisos cargados: {len(permisos)}")
        return jsonify({"ok": True, "permisos": permisos})
    except Exception as e:
        print(f"[ERROR] api_obtener_permisos: {e}")
        return jsonify({"ok": False, "error": str(e), "permisos": {}})


def api_actualizar_permiso():
    """
    Actualiza el permiso de una factura
    """
    try:
        data = request.get_json()
        factura_id = data.get('factura_id')
        permitido = data.get('permitido', False)
        
        print(f"[DEBUG] ===== ACTUALIZANDO PERMISO =====")
        print(f"[DEBUG] Factura ID: {factura_id}")
        print(f"[DEBUG] Permitido: {permitido}")
        
        if not factura_id:
            return jsonify({"ok": False, "error": "Se requiere factura_id"})
        
        # Asegurar que el archivo existe
        if not os.path.exists(ARCHIVO_PERMISOS_FACTURAS):
            guardar_json(ARCHIVO_PERMISOS_FACTURAS, {})
        
        permisos = cargar_json(ARCHIVO_PERMISOS_FACTURAS, {})
        # Guardar el permiso (asegurar que sea booleano)
        permisos[factura_id] = permitido if isinstance(permitido, bool) else bool(permitido)
        guardar_json(ARCHIVO_PERMISOS_FACTURAS, permisos)
        
        print(f"[DEBUG] ✅ Permiso guardado: {factura_id} = {permisos[factura_id]}")
        print(f"[DEBUG] Permisos totales: {len(permisos)}")
        
        return jsonify({"ok": True, "mensaje": f"Permiso actualizado a {permisos[factura_id]}"})
    except Exception as e:
        print(f"[ERROR] api_actualizar_permiso: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})