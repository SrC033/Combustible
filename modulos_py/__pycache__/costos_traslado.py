# ==================== MÓDULO COSTOS TRASLADO - CON FÓRMULAS FLEXIBLES ====================
import os
import json
import re
from datetime import datetime
from flask import jsonify, request, send_file

# ==================== CONFIGURACIÓN ====================
ARCHIVO_COSTOS_TRASLADO = None
_cargar_json = None
_guardar_json = None
_registrar_bitacora = None
CARPETA_EXCEL_REPORTES = None
CARPETA_PDF_REPORTES = None

# Columnas que son TEXTO (NO se usan en cálculos)
COLUMNAS_TEXTO = ['empresa_id', 'nombre_empresa', 'origen', 'destino', 'bono1', 'bono2']

# Correspondencia de letras CORRECTA según la tabla:
# A = ID Cliente (TEXTO)
# B = Cliente (TEXTO)
# C = Origen (TEXTO)
# D = Destino (TEXTO)
# E = Diesel (NUMÉRICO)
# F = Diesel Max (NUMÉRICO)
# G = Gasolina (NUMÉRICO)
# H = Gasolina Max (NUMÉRICO)
# I = Bono 1 (TEXTO)
# J = Bono 2 (TEXTO)
# K = Viático 1 (NUMÉRICO)
# L = Viático 2 (NUMÉRICO)
# M = Traslado (NUMÉRICO)
# N = Distancia (NUMÉRICO)  <-- NUEVA COLUMNA PERMANENTE
# O, P, Q, ... = Columnas adicionales (NUMÉRICO)

# Mapeo de letras numéricas fijas a campos
COLUMNAS_NUMERICAS = {
    'E': 'precio_diesel',
    'F': 'precio_diesel_max',
    'G': 'precio_gasolina',
    'H': 'precio_gasolina_max',
    'K': 'viatico1',
    'L': 'viatico2',
    'M': 'costo_traslado',
    'N': 'distancia_km'  # <-- NUEVA COLUMNA PERMANENTE
}

# Letras de TEXTO que NO se pueden usar en fórmulas
LETRAS_TEXTO = ['A', 'B', 'C', 'D', 'I', 'J']

# ==================== INICIALIZACIÓN ====================
def inicializar_costos(main_funciones=None, rutas=None):
    global _cargar_json, _guardar_json, _registrar_bitacora
    global ARCHIVO_COSTOS_TRASLADO, CARPETA_EXCEL_REPORTES, CARPETA_PDF_REPORTES
    
    if main_funciones:
        _cargar_json = main_funciones.get('cargar_json')
        _guardar_json = main_funciones.get('guardar_json')
        _registrar_bitacora = main_funciones.get('registrar_bitacora')
    
    if rutas:
        ARCHIVO_COSTOS_TRASLADO = rutas.get('costos_traslado')
        CARPETA_EXCEL_REPORTES = rutas.get('excel_reportes')
        CARPETA_PDF_REPORTES = rutas.get('pdf_reportes')
    
    print(f"[INFO] Módulo Costos Traslado inicializado")
    print(f"[INFO] Archivo costos: {ARCHIVO_COSTOS_TRASLADO}")


def cargar_json(ruta, default=None):
    if _cargar_json:
        return _cargar_json(ruta, default)
    if os.path.exists(ruta):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read().strip()
                if not contenido:
                    return default if default is not None else {}
                return json.loads(contenido)
        except Exception as e:
            print(f"Error cargando {ruta}: {e}")
            return default if default is not None else {}
    return default if default is not None else {}


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
    if _registrar_bitacora:
        return _registrar_bitacora(usuario, accion, detalles, modulo)


def cargar_costos():
    data = cargar_json(ARCHIVO_COSTOS_TRASLADO, {"costos": [], "columnas_adicionales": []})
    if not isinstance(data, dict):
        return {"costos": [], "columnas_adicionales": []}
    if "costos" not in data:
        data["costos"] = []
    if "columnas_adicionales" not in data:
        data["columnas_adicionales"] = []
    return data


def guardar_costos(data):
    if "costos" not in data:
        data["costos"] = []
    if "columnas_adicionales" not in data:
        data["columnas_adicionales"] = []
    return guardar_json(ARCHIVO_COSTOS_TRASLADO, data)


def detectar_columnas_adicionales(costos):
    """Detecta automáticamente las columnas adicionales en los costos"""
    columnas_extra = set()
    for costo in costos:
        for key in costo.keys():
            # Excluir columnas fijas y campos especiales
            if key not in ['empresa_id', 'nombre_empresa', 'origen', 'destino', 
                          'precio_diesel', 'precio_diesel_max', 'precio_gasolina', 
                          'precio_gasolina_max', 'bono1', 'bono2', 'viatico1', 
                          'viatico2', 'costo_traslado', 'distancia_km', 'formula_calculos', 
                          'costo_total', 'fecha_actualizacion']:
                columnas_extra.add(key)
    return list(columnas_extra)


# ==================== EVALUADOR DE FÓRMULAS ====================

def obtener_valores_columnas(empresa_data, columnas_adicionales):
    """
    Retorna un diccionario con todas las columnas numéricas disponibles
    y su valor correspondiente según la correspondencia CORRECTA.
    
    E = precio_diesel
    F = precio_diesel_max
    G = precio_gasolina
    H = precio_gasolina_max
    K = viatico1
    L = viatico2
    M = costo_traslado
    N = distancia_km
    O, P, Q, ... = columnas adicionales
    """
    valores = {}
    
    # Columnas numéricas fijas
    for letra, campo in COLUMNAS_NUMERICAS.items():
        valor = empresa_data.get(campo, 0)
        try:
            valores[letra] = float(valor)
        except (ValueError, TypeError):
            valores[letra] = 0
    
    # Columnas adicionales (O, P, Q, ...)
    # Nota: N ya está ocupada por distancia_km, por eso empezamos en O (79)
    for i, col_extra in enumerate(columnas_adicionales):
        letra = chr(79 + i)  # O = 79, P = 80, ...
        valor = empresa_data.get(col_extra, 0)
        try:
            valores[letra] = float(valor)
        except (ValueError, TypeError):
            valores[letra] = 0
    
    return valores


def evaluar_formula(formula, valores_columnas):
    """
    Evalúa una fórmula con soporte para:
    - Mayúsculas y minúsculas (e+f, K*L, etc.)
    - Cualquier combinación de columnas numéricas
    - NO permite columnas de texto (A, B, C, D, I, J)
    - Operadores: +, -, *, /, ()
    """
    if not formula:
        return 0
    
    formula = formula.strip()
    
    # Si empieza con '=', removerlo
    if formula.startswith('='):
        formula = formula[1:]
    
    # Si la fórmula está vacía después de remover '='
    if not formula:
        return 0
    
    # Convertir a mayúsculas para estandarizar
    formula_upper = formula.upper()
    
    # VERIFICAR si contiene columnas de texto (A, B, C, D, I, J)
    for letra in LETRAS_TEXTO:
        pattern = r'\b' + letra + r'\b'
        if re.search(pattern, formula_upper):
            print(f"[ERROR] Fórmula contiene columna de texto: {letra}")
            return 0
    
    # Reemplazar todas las letras de columnas con sus valores numéricos
    for letra, valor in valores_columnas.items():
        pattern = r'\b' + letra + r'\b'
        formula_upper = re.sub(pattern, f'({valor})', formula_upper)
    
    # Eliminar caracteres no permitidos (solo números, operadores y paréntesis)
    formula_upper = re.sub(r'[^0-9+\-*/()\. ]', '', formula_upper)
    
    # Si la fórmula quedó vacía, retornar 0
    if not formula_upper or formula_upper.strip() == '':
        return 0
    
    try:
        # Evaluar la expresión de forma segura
        resultado = eval(formula_upper, {"__builtins__": {}})
        return float(resultado) if isinstance(resultado, (int, float)) else 0
    except Exception as e:
        print(f"[ERROR] Evaluando fórmula: {formula_upper} -> {e}")
        return 0


def calcular_total(empresa_data, columnas_adicionales):
    """
    Calcula el total de una empresa usando su fórmula
    """
    formula = empresa_data.get('formula_calculos', '')
    
    # Si no hay fórmula, usar default: E+F+G+H+K+L+M+N
    if not formula or formula.strip() == '':
        formula = 'E+F+G+H+K+L+M+N'
    
    # Si no empieza con '=', agregarlo
    if not formula.startswith('='):
        formula = '=' + formula
    
    # Obtener valores de todas las columnas
    valores = obtener_valores_columnas(empresa_data, columnas_adicionales)
    
    # Evaluar la fórmula
    total = evaluar_formula(formula, valores)
    
    return total


def limpiar_formula_para_excel(formula):
    """
    Limpia la fórmula para mostrarla en Excel:
    - Mantiene los operadores (+, -, *, /)
    - Elimina el signo '=' inicial
    - Elimina espacios extra
    - Ejemplo: "= k + e" -> "k + e"
              "=E+F+G" -> "E+F+G"
    """
    if not formula:
        return ""
    
    formula_limpia = formula.strip()
    
    if formula_limpia.startswith('='):
        formula_limpia = formula_limpia[1:]
    
    formula_limpia = re.sub(r'\s+', ' ', formula_limpia).strip()
    
    if not formula_limpia:
        return formula.strip().lstrip('=').strip()
    
    return formula_limpia


# ==================== API ENDPOINTS ====================

def api_costos_traslado():
    try:
        data = cargar_costos()
        costos = data.get("costos", [])
        columnas_adicionales = data.get("columnas_adicionales", [])
        
        # Si no hay columnas adicionales guardadas, detectarlas automáticamente
        if not columnas_adicionales and costos:
            columnas_adicionales = detectar_columnas_adicionales(costos)
            data["columnas_adicionales"] = columnas_adicionales
            guardar_costos(data)
            print(f"[INFO] Columnas adicionales detectadas: {columnas_adicionales}")
        
        # Calcular el total para cada costo usando su fórmula
        for costo in costos:
            if costo.get('formula_calculos'):
                total = calcular_total(costo, columnas_adicionales)
                costo['costo_total'] = total
        
        return jsonify({
            "ok": True,
            "costos": costos,
            "columnas_adicionales": columnas_adicionales
        })
    except Exception as e:
        print(f"[ERROR] api_costos_traslado: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e), "costos": []})


def api_costo_empresa(empresa_id):
    try:
        data = cargar_costos()
        columnas_adicionales = data.get("columnas_adicionales", [])
        
        for c in data.get("costos", []):
            if c.get("empresa_id") == empresa_id:
                if c.get('formula_calculos'):
                    total = calcular_total(c, columnas_adicionales)
                    c['costo_total'] = total
                return jsonify({"ok": True, "costo": c})
        return jsonify({"ok": False, "costo": None})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_guardar_costo_empresa():
    try:
        data = request.get_json()
        empresa_id = data.get("empresa_id")
        
        if not empresa_id:
            return jsonify({"ok": False, "error": "Se requiere empresa_id"})
        
        costos_data = cargar_costos()
        costos = costos_data.get("costos", [])
        columnas_adicionales = costos_data.get("columnas_adicionales", [])
        
        # Verificar si hay nuevas columnas adicionales en la data
        if "columnas_adicionales" in data:
            columnas_adicionales = data["columnas_adicionales"]
            costos_data["columnas_adicionales"] = columnas_adicionales
        else:
            # Detectar columnas adicionales de la data recibida
            for key in data.keys():
                if key not in ['empresa_id', 'nombre_empresa', 'origen', 'destino', 
                              'precio_diesel', 'precio_diesel_max', 'precio_gasolina', 
                              'precio_gasolina_max', 'bono1', 'bono2', 'viatico1', 
                              'viatico2', 'costo_traslado', 'distancia_km', 'formula_calculos', 
                              'costo_total', 'fecha_actualizacion']:
                    if key not in columnas_adicionales:
                        columnas_adicionales.append(key)
                        print(f"[INFO] Nueva columna detectada: {key}")
            costos_data["columnas_adicionales"] = columnas_adicionales
        
        # Si no hay fórmula, usar la default
        if not data.get('formula_calculos'):
            data['formula_calculos'] = '=E+F+G+H+K+L+M+N'
        
        # Calcular el total usando la fórmula
        total = calcular_total(data, columnas_adicionales)
        data['costo_total'] = total
        
        # Verificar si ya existe
        encontrado = False
        for i, c in enumerate(costos):
            if c.get("empresa_id") == empresa_id:
                costos[i] = data
                encontrado = True
                break
        
        if not encontrado:
            costos.append(data)
        
        costos_data["costos"] = costos
        
        if guardar_costos(costos_data):
            registrar_bitacora(
                data.get('usuario', 'sistema'),
                "Guardar Costo Traslado",
                f"Empresa: {empresa_id} - Total: {total:.2f}",
                "Costos Traslado"
            )
            return jsonify({"ok": True, "costo_total": total})
        return jsonify({"ok": False, "error": "Error al guardar"})
    except Exception as e:
        print(f"[ERROR] api_guardar_costo_empresa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


def api_eliminar_costo_empresa():
    try:
        data = request.get_json()
        empresa_id = data.get("empresa_id")
        
        if not empresa_id:
            return jsonify({"ok": False, "error": "Se requiere empresa_id"})
        
        costos_data = cargar_costos()
        costos_data["costos"] = [c for c in costos_data.get("costos", []) if c.get("empresa_id") != empresa_id]
        
        if guardar_costos(costos_data):
            registrar_bitacora(
                data.get('usuario', 'sistema'),
                "Eliminar Costo Traslado",
                f"Empresa: {empresa_id}",
                "Costos Traslado"
            )
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Error al eliminar"})
    except Exception as e:
        print(f"[ERROR] api_eliminar_costo_empresa: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_eliminar_columna_adicional():
    try:
        data = request.get_json()
        nombre_columna = data.get("nombre_columna")
        
        if not nombre_columna:
            return jsonify({"ok": False, "error": "Se requiere nombre_columna"})
        
        costos_data = cargar_costos()
        columnas = costos_data.get("columnas_adicionales", [])
        
        if nombre_columna in columnas:
            columnas.remove(nombre_columna)
        
        # Eliminar la columna de cada costo
        for c in costos_data.get("costos", []):
            if nombre_columna in c:
                del c[nombre_columna]
        
        costos_data["columnas_adicionales"] = columnas
        
        if guardar_costos(costos_data):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Error al eliminar columna"})
    except Exception as e:
        print(f"[ERROR] api_eliminar_columna_adicional: {e}")
        return jsonify({"ok": False, "error": str(e)})


def api_exportar_excel():
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        
        data = cargar_costos()
        costos = data.get("costos", [])
        columnas_adicionales = data.get("columnas_adicionales", [])
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Costos de Traslado"
        
        # ============ ORDEN DE COLUMNAS ============
        # A, B, C, D, E, F, G, H, I, J, K, L, M, N (Distancia), [adicionales], O (Fórmula), Costo Total
        
        columnas_fijas = [
            "ID Cliente (A)", "Cliente (B)", "Origen (C)", "Destino (D)",
            "Diesel (E)", "Diesel Max (F)", "Gasolina (G)", "Gasolina Max (H)",
            "Bono 1 (I)", "Bono 2 (J)", "Viático 1 (K)", "Viático 2 (L)",
            "Traslado (M)", "Distancia (N)"
        ]
        
        # Columnas adicionales (O, P, Q, ...) van ANTES de la columna Fórmula
        columnas_extra = [f"{col} ({chr(79+i)})" for i, col in enumerate(columnas_adicionales)]
        
        headers = columnas_fijas + columnas_extra + ["Fórmula (O)", "Costo Total"]
        
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
        center_alignment = Alignment(horizontal="center", vertical="center")
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment
        
        # Campos en el orden correcto
        campos_fijos = [
            "empresa_id", "nombre_empresa", "origen", "destino",
            "precio_diesel", "precio_diesel_max", "precio_gasolina", "precio_gasolina_max",
            "bono1", "bono2", "viatico1", "viatico2",
            "costo_traslado", "distancia_km"
        ]
        
        for row_idx, costo in enumerate(costos, 2):
            # Calcular total con la fórmula (para el Costo Total)
            total = calcular_total(costo, columnas_adicionales)
            costo['costo_total'] = total
            
            # Columnas fijas (A-N)
            for col_idx, campo in enumerate(campos_fijos, 1):
                valor = costo.get(campo, "")
                if isinstance(valor, (int, float)):
                    ws.cell(row=row_idx, column=col_idx, value=float(valor))
                else:
                    ws.cell(row=row_idx, column=col_idx, value=valor)
                ws.cell(row=row_idx, column=col_idx).alignment = center_alignment
            
            # Columnas adicionales (O, P, Q, ...)
            col_offset = len(campos_fijos) + 1
            for col_idx, col_extra in enumerate(columnas_adicionales):
                valor = costo.get(col_extra, "")
                if isinstance(valor, (int, float)):
                    ws.cell(row=row_idx, column=col_offset + col_idx, value=float(valor))
                else:
                    ws.cell(row=row_idx, column=col_offset + col_idx, value=valor)
                ws.cell(row=row_idx, column=col_offset + col_idx).alignment = center_alignment
            
            # Fórmula (O) - CON OPERADORES (+ - * /)
            formula_col = col_offset + len(columnas_adicionales)
            formula_original = costo.get('formula_calculos', '=E+F+G+H+K+L+M+N')
            formula_limpia = limpiar_formula_para_excel(formula_original)
            ws.cell(row=row_idx, column=formula_col, value=formula_limpia)
            ws.cell(row=row_idx, column=formula_col).alignment = center_alignment
            
            # Costo Total
            total_col = formula_col + 1
            ws.cell(row=row_idx, column=total_col, value=float(total))
            ws.cell(row=row_idx, column=total_col).alignment = center_alignment
        
        # Ajustar ancho de columnas
        for col in ws.columns:
            max_length = 0
            column_letter = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 35)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        if CARPETA_EXCEL_REPORTES:
            os.makedirs(CARPETA_EXCEL_REPORTES, exist_ok=True)
            filename = f"costos_traslado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join(CARPETA_EXCEL_REPORTES, filename)
            wb.save(filepath)
            return send_file(filepath, as_attachment=True, download_name=filename)
        
        return jsonify({"ok": False, "error": "Carpeta de reportes no configurada"})
    except ImportError:
        return jsonify({"ok": False, "error": "openpyxl no instalado"})
    except Exception as e:
        print(f"[ERROR] api_exportar_excel: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


def api_exportar_pdf():
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.units import cm
        
        data = cargar_costos()
        costos = data.get("costos", [])
        columnas_adicionales = data.get("columnas_adicionales", [])
        
        if not CARPETA_PDF_REPORTES:
            return jsonify({"ok": False, "error": "Carpeta de reportes no configurada"})
        
        os.makedirs(CARPETA_PDF_REPORTES, exist_ok=True)
        filename = f"costos_traslado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(CARPETA_PDF_REPORTES, filename)
        
        # ============ ANCHOS DE COLUMNAS POR CONTENIDO ============
        # Cada columna con su ancho específico según el contenido que debe mostrar
        
        # Mapeo de columnas: (nombre_header, ancho_cm, campo_json, tipo)
        columnas_config = [
            {"header": "ID(A)", "ancho": 2.5, "campo": "empresa_id", "tipo": "texto"},
            {"header": "Cliente(B)", "ancho": 4.0, "campo": "nombre_empresa", "tipo": "texto"},
            {"header": "Origen(C)", "ancho": 2.8, "campo": "origen", "tipo": "texto"},
            {"header": "Destino(D)", "ancho": 2.8, "campo": "destino", "tipo": "texto"},
            {"header": "Diesel(E)", "ancho": 2.2, "campo": "precio_diesel", "tipo": "numero"},
            {"header": "Diesel Max(F)", "ancho": 2.5, "campo": "precio_diesel_max", "tipo": "numero"},
            {"header": "Gasolina(G)", "ancho": 2.2, "campo": "precio_gasolina", "tipo": "numero"},
            {"header": "Gasolina Max(H)", "ancho": 2.5, "campo": "precio_gasolina_max", "tipo": "numero"},
            {"header": "Bono1(I)", "ancho": 2.2, "campo": "bono1", "tipo": "texto"},
            {"header": "Bono2(J)", "ancho": 2.2, "campo": "bono2", "tipo": "texto"},
            {"header": "Viático1(K)", "ancho": 2.5, "campo": "viatico1", "tipo": "numero"},
            {"header": "Viático2(L)", "ancho": 2.5, "campo": "viatico2", "tipo": "numero"},
            {"header": "Traslado(M)", "ancho": 2.5, "campo": "costo_traslado", "tipo": "numero"},
            {"header": "Distancia(N)", "ancho": 2.5, "campo": "distancia_km", "tipo": "numero"},
        ]
        
        # Columnas adicionales (O, P, Q, ...)
        for i, col in enumerate(columnas_adicionales):
            ancho = max(2.0, min(3.5, len(col) * 0.3 + 0.8))
            columnas_config.append({
                "header": f"{col}({chr(79+i)})",
                "ancho": ancho,
                "campo": col,
                "tipo": "texto"
            })
        
        # Columna: Fórmula (más ancha)
        columnas_config.append({
            "header": "Fórmula(O)",
            "ancho": 4.5,
            "campo": "formula_calculos",
            "tipo": "texto"
        })
        
        # Columna: Costo Total
        columnas_config.append({
            "header": "Costo Total",
            "ancho": 3.0,
            "campo": "costo_total",
            "tipo": "numero"
        })
        
        # Crear lista de headers y anchos
        headers = [col["header"] for col in columnas_config]
        col_widths = [col["ancho"] * cm for col in columnas_config]
        
        # Calcular ancho total
        ancho_total = sum(col["ancho"] for col in columnas_config)
        ancho_maximo_pagina = 27.0  # cm (landscape A4)
        
        if ancho_total > ancho_maximo_pagina:
            factor = ancho_maximo_pagina / ancho_total
            col_widths = [(col["ancho"] * factor) * cm for col in columnas_config]
        
        doc = SimpleDocTemplate(filepath, pagesize=landscape(A4),
                               topMargin=1.5*cm, bottomMargin=1.5*cm,
                               leftMargin=1.5*cm, rightMargin=1.5*cm)
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'Title', parent=styles['Heading1'],
            alignment=TA_CENTER, fontSize=14,
            textColor=colors.HexColor("#10b981")
        )
        
        table_data = [headers]
        
        for costo in costos[:100]:
            total = calcular_total(costo, columnas_adicionales)
            costo['costo_total'] = total
            
            row = []
            for col in columnas_config:
                campo = col["campo"]
                valor = costo.get(campo, "")
                tipo = col["tipo"]
                
                if tipo == "numero":
                    try:
                        row.append(f"{float(valor):.2f}")
                    except (ValueError, TypeError):
                        row.append(str(valor))
                else:
                    texto = str(valor)
                    max_len = int(col["ancho"] * 4)
                    if len(texto) > max_len:
                        texto = texto[:max_len-2] + ".."
                    row.append(texto)
            
            table_data.append(row)
        
        tabla = Table(table_data, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#10b981")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,1), (-1,-1), 7),
            ('TOPPADDING', (0,1), (-1,-1), 4),
            ('BOTTOMPADDING', (0,1), (-1,-1), 4),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ]))
        
        elements = []
        elements.append(Paragraph("Costos de Traslado", title_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Total de registros: {len(costos)}", styles['Normal']))
        elements.append(Spacer(1, 12))
        elements.append(tabla)
        
        doc.build(elements)
        return send_file(filepath, as_attachment=True, download_name=filename)
    except ImportError:
        return jsonify({"ok": False, "error": "ReportLab no instalado"})
    except Exception as e:
        print(f"[ERROR] api_exportar_pdf: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})