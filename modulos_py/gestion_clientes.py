# ==================== MÓDULO GESTIÓN CLIENTES (AUTÓNOMO) ====================
# Módulo independiente para gestión de clientes
# Sin dependencias de Empresas o Costos de Traslado
# Soporte para columnas dinámicas, nombres personalizados y fórmulas Excel

import os
import json
import re
from datetime import datetime
from flask import jsonify, request, send_file

# ==================== CONFIGURACIÓN ====================
ARCHIVO_CLIENTES = None
ARCHIVO_CONFIG_CLIENTES = None
_cargar_json = None
_guardar_json = None
_registrar_bitacora = None

# Carpetas para exportación
CARPETA_EXCEL_CLIENTES = None
CARPETA_PDF_CLIENTES = None

# Columnas por defecto
COLUMNAS_DEFAULT = [
    "CLIENTE", "TIPO", "ORIGEN", "DESTINO",
    "DIESEL", "DIESEL MAX", "GASOLINA", "GASOLINA MAX",
    "BONO 1", "BONO 2", "VIATICO 1", "VIATICO 2",
    "TRASLADO", "DISTANCIA", "COSTO TOTAL"
]

NOMBRES_MOSTRADOS_DEFAULT = {
    "CLIENTE": "Cliente",
    "TIPO": "Tipo",
    "ORIGEN": "Origen",
    "DESTINO": "Destino",
    "DIESEL": "Diesel",
    "DIESEL MAX": "Diesel Max",
    "GASOLINA": "Gasolina",
    "GASOLINA MAX": "Gasolina Max",
    "BONO 1": "Bono 1",
    "BONO 2": "Bono 2",
    "VIATICO 1": "Viático 1",
    "VIATICO 2": "Viático 2",
    "TRASLADO": "Traslado",
    "DISTANCIA": "Distancia",
    "COSTO TOTAL": "Costo Total"
}

COLUMNAS_PROTEGIDAS_DEFAULT = [
    "CLIENTE", "TIPO", "ORIGEN", "DESTINO",
    "DIESEL", "DIESEL MAX", "GASOLINA", "GASOLINA MAX",
    "BONO 1", "BONO 2", "VIATICO 1", "VIATICO 2",
    "TRASLADO", "DISTANCIA", "COSTO TOTAL"
]

COLUMNAS_NUMERICAS_DEFAULT = [
    "DIESEL", "DIESEL MAX", "GASOLINA", "GASOLINA MAX",
    "VIATICO 1", "VIATICO 2", "TRASLADO", "DISTANCIA", "COSTO TOTAL"
]

# Mapeo de letras para fórmulas (A-Z)
COLUMNAS_NUMERICAS_MAP = {
    'E': 'DIESEL',
    'F': 'DIESEL MAX',
    'G': 'GASOLINA',
    'H': 'GASOLINA MAX',
    'K': 'VIATICO 1',
    'L': 'VIATICO 2',
    'M': 'TRASLADO',
    'N': 'DISTANCIA'
}


# ==================== INICIALIZACIÓN ====================
def inicializar_gestion_clientes(main_funciones=None, rutas=None):
    global _cargar_json, _guardar_json, _registrar_bitacora
    global ARCHIVO_CLIENTES, ARCHIVO_CONFIG_CLIENTES
    global CARPETA_EXCEL_CLIENTES, CARPETA_PDF_CLIENTES

    if main_funciones:
        _cargar_json = main_funciones.get('cargar_json')
        _guardar_json = main_funciones.get('guardar_json')
        _registrar_bitacora = main_funciones.get('registrar_bitacora')

    if rutas:
        ARCHIVO_CLIENTES = rutas.get('clientes')
        ARCHIVO_CONFIG_CLIENTES = rutas.get('config_clientes')
        
        # Carpetas para exportación
        if ARCHIVO_CLIENTES:
            base_dir = os.path.dirname(ARCHIVO_CLIENTES)
            data_dir = os.path.dirname(base_dir) if base_dir.endswith('datos') else base_dir
            CARPETA_EXCEL_CLIENTES = os.path.join(data_dir, 'excel_clientes')
            CARPETA_PDF_CLIENTES = os.path.join(data_dir, 'pdf_clientes')
            os.makedirs(CARPETA_EXCEL_CLIENTES, exist_ok=True)
            os.makedirs(CARPETA_PDF_CLIENTES, exist_ok=True)
            
            print(f"[INFO] Carpeta Excel Clientes: {CARPETA_EXCEL_CLIENTES}")
            print(f"[INFO] Carpeta PDF Clientes: {CARPETA_PDF_CLIENTES}")
        
        # Si no se pasó config_clientes, usar el mismo directorio
        if not ARCHIVO_CONFIG_CLIENTES and ARCHIVO_CLIENTES:
            base_dir = os.path.dirname(ARCHIVO_CLIENTES)
            ARCHIVO_CONFIG_CLIENTES = os.path.join(base_dir, "config_clientes.json")

    print("[INFO] Módulo Gestión Clientes (autónomo) inicializado")


# ==================== FUNCIONES JSON ====================
def cargar_json(ruta, default=None):
    if _cargar_json:
        return _cargar_json(ruta, default)
    if not ruta:
        return default if default is not None else {}
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
    if not ruta:
        return False
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


# ==================== CONFIGURACIÓN DE COLUMNAS ====================
def obtener_config_clientes():
    """Obtiene la configuración de columnas y nombres personalizados"""
    default = {
        "columnas": COLUMNAS_DEFAULT,
        "nombres_mostrados": NOMBRES_MOSTRADOS_DEFAULT,
        "columnas_protegidas": COLUMNAS_PROTEGIDAS_DEFAULT,
        "columnas_numericas": COLUMNAS_NUMERICAS_DEFAULT,
        "version": "2.0",
        "fecha_actualizacion": datetime.now().isoformat()
    }
    
    if ARCHIVO_CONFIG_CLIENTES and os.path.exists(ARCHIVO_CONFIG_CLIENTES):
        config = cargar_json(ARCHIVO_CONFIG_CLIENTES, default)
        if isinstance(config, dict):
            # Asegurar que todas las claves existan
            for key in default:
                if key not in config:
                    config[key] = default[key]
            return config
    
    # Si no existe el archivo, crear uno con los valores por defecto
    if ARCHIVO_CONFIG_CLIENTES:
        guardar_json(ARCHIVO_CONFIG_CLIENTES, default)
        print(f"[INFO] Configuración de clientes creada en: {ARCHIVO_CONFIG_CLIENTES}")
    
    return default


def guardar_config_clientes(config):
    """Guarda la configuración de columnas"""
    if ARCHIVO_CONFIG_CLIENTES:
        config['fecha_actualizacion'] = datetime.now().isoformat()
        config['version'] = '2.0'
        return guardar_json(ARCHIVO_CONFIG_CLIENTES, config)
    return False


def obtener_columnas():
    config = obtener_config_clientes()
    return config.get('columnas', COLUMNAS_DEFAULT)


def obtener_nombres_mostrados():
    config = obtener_config_clientes()
    return config.get('nombres_mostrados', NOMBRES_MOSTRADOS_DEFAULT)


def obtener_columnas_protegidas():
    config = obtener_config_clientes()
    return config.get('columnas_protegidas', COLUMNAS_PROTEGIDAS_DEFAULT)


def obtener_columnas_numericas():
    config = obtener_config_clientes()
    return config.get('columnas_numericas', COLUMNAS_NUMERICAS_DEFAULT)


# ==================== FUNCIONES CLIENTES ====================
def cargar_clientes():
    """Carga todos los clientes del archivo JSON"""
    if not ARCHIVO_CLIENTES:
        return {"clientes": [], "ultimo_id": 0}
    data = cargar_json(ARCHIVO_CLIENTES, {"clientes": [], "ultimo_id": 0})
    if not isinstance(data, dict):
        return {"clientes": [], "ultimo_id": 0}
    if "clientes" not in data:
        data["clientes"] = []
    if "ultimo_id" not in data:
        data["ultimo_id"] = 0
    return data


def guardar_clientes(data):
    """Guarda los clientes en el archivo JSON"""
    if not ARCHIVO_CLIENTES:
        return False
    return guardar_json(ARCHIVO_CLIENTES, data)


def obtener_cliente(cliente_id):
    """Obtiene un cliente por su ID"""
    data = cargar_clientes()
    for cli in data.get("clientes", []):
        if cli.get("id") == cliente_id:
            return cli
    return None


def crear_cliente(datos):
    """Crea un nuevo cliente con los datos proporcionados"""
    data = cargar_clientes()
    
    # Verificar si el ID ya existe
    cliente_id = datos.get("id", "")
    if cliente_id:
        for cli in data["clientes"]:
            if cli.get("id") == cliente_id:
                return None
    
    # Generar ID si no se proporcionó
    if not cliente_id:
        data["ultimo_id"] = data.get("ultimo_id", 0) + 1
        cliente_id = f"CLI-{data['ultimo_id']:04d}"
    
    nuevo_cliente = {
        "id": cliente_id,
        "nombre": datos.get("nombre", ""),
        "tipo": datos.get("tipo", "Cliente"),
        "contacto": datos.get("contacto", ""),
        "cedula": datos.get("cedula", ""),
        "telefono": datos.get("telefono", ""),
        "email": datos.get("email", ""),
        "direccion": datos.get("direccion", ""),
        "origen": datos.get("origen", ""),
        "destino": datos.get("destino", ""),
        "placa": datos.get("placa", ""),
        "conductor": datos.get("conductor", ""),
        "credito": float(datos.get("credito", 0)),
        "limite_credito": float(datos.get("limite_credito", 0)),
        "limite_original": float(datos.get("limite_credito", 0)),
        "fecha_registro": datetime.now().isoformat(),
        "activo": True,
        "columnas_adicionales": datos.get("columnas_adicionales", {}),
        "formula": datos.get("formula", "=E+F+G+H+K+L+M+N"),
        "costo_total": 0.0,
        # Campos de ruta
        "diesel": float(datos.get("diesel", 0)),
        "diesel_max": float(datos.get("diesel_max", 0)),
        "gasolina": float(datos.get("gasolina", 0)),
        "gasolina_max": float(datos.get("gasolina_max", 0)),
        "bono1": datos.get("bono1", ""),
        "bono2": datos.get("bono2", ""),
        "viatico1": float(datos.get("viatico1", 0)),
        "viatico2": float(datos.get("viatico2", 0)),
        "traslado": float(datos.get("traslado", 0)),
        "distancia": float(datos.get("distancia", 0)),
        "extensiones": []
    }
    
    # Calcular costo total
    nuevo_cliente["costo_total"] = calcular_costo_total(nuevo_cliente)
    
    data["clientes"].append(nuevo_cliente)
    guardar_clientes(data)
    return nuevo_cliente


def actualizar_cliente(cliente_id, datos):
    """Actualiza un cliente existente con soporte para campos antiguos"""
    data = cargar_clientes()
    
    # Mapeo de campos antiguos a nuevos (compatibilidad con versión anterior)
    mapeo_campos = {
        'precio_diesel': 'diesel',
        'precio_diesel_max': 'diesel_max',
        'precio_gasolina': 'gasolina',
        'precio_gasolina_max': 'gasolina_max',
        'costo_traslado': 'traslado',
        'distancia_km': 'distancia',
        'formula_calculos': 'formula',
        'destino_ruta': 'destino',
        'empresa_id': 'id',
        'nombre_empresa': 'nombre'
    }
    
    for i, cli in enumerate(data["clientes"]):
        if cli.get("id") == cliente_id:
            # Campos permitidos para actualizar en la raíz del objeto
            campos_permitidos = [
                'id', 'nombre', 'tipo', 'contacto', 'cedula', 'telefono', 'email',
                'direccion', 'origen', 'destino', 'placa', 'conductor',
                'diesel', 'diesel_max', 'gasolina', 'gasolina_max',
                'bono1', 'bono2', 'viatico1', 'viatico2', 'traslado', 'distancia',
                'credito', 'limite_credito', 'activo', 'columnas_adicionales', 
                'costo_total', 'formula'
            ]
            
            # Procesar campos directos
            for campo in campos_permitidos:
                valor = None
                if campo in datos:
                    valor = datos[campo]
                elif campo in mapeo_campos and mapeo_campos[campo] in datos:
                    valor = datos[mapeo_campos[campo]]
                
                if valor is not None:
                    if campo in ['diesel', 'diesel_max', 'gasolina', 'gasolina_max',
                                 'viatico1', 'viatico2', 'traslado', 'distancia',
                                 'credito', 'limite_credito', 'costo_total']:
                        try:
                            data["clientes"][i][campo] = float(valor)
                        except (ValueError, TypeError):
                            data["clientes"][i][campo] = 0.0
                    else:
                        data["clientes"][i][campo] = valor
            
            # Procesar campos adicionales que no están en la lista permitida
            for key, value in datos.items():
                if key not in campos_permitidos and key not in mapeo_campos:
                    if key not in ['usuario', 'id_personalizado']:
                        if "columnas_adicionales" not in data["clientes"][i]:
                            data["clientes"][i]["columnas_adicionales"] = {}
                        # Guardamos con la clave tal cual viene del HTML (minúsculas/mayúsculas)
                        data["clientes"][i]["columnas_adicionales"][key] = value
            
            # Recalcular costo total (si no se proporcionó uno específico)
            if 'costo_total' not in datos:
                data["clientes"][i]["costo_total"] = calcular_costo_total(data["clientes"][i])
            
            print(f"[DEBUG] Cliente actualizado: {data['clientes'][i]['id']}")
            guardar_clientes(data)
            return True
    return False


def eliminar_cliente(cliente_id):
    """Elimina un cliente por su ID"""
    data = cargar_clientes()
    data["clientes"] = [c for c in data["clientes"] if c.get("id") != cliente_id]
    guardar_clientes(data)
    return True


# ==================== FUNCIONES DE CRÉDITO ====================
def actualizar_credito(cliente_id, monto, es_abono=False):
    """Actualiza el crédito de un cliente (cargo o abono)"""
    data = cargar_clientes()
    for i, cli in enumerate(data["clientes"]):
        if cli.get("id") == cliente_id:
            if es_abono:
                nuevo_credito = max(0, cli.get("credito", 0) - monto)
                mensaje = f"Abono de C${monto:,.2f} applied"
            else:
                nuevo_credito = cli.get("credito", 0) + monto
                mensaje = f"Cargo de C${monto:,.2f} applied"
            
            data["clientes"][i]["credito"] = round(nuevo_credito, 2)
            guardar_clientes(data)
            return {"ok": True, "credito": nuevo_credito, "mensaje": mensaje}
    return {"ok": False, "error": "Cliente no encontrado"}


def extender_limite(cliente_id, monto_adicional, motivo=""):
    """Extiende el límite de crédito de un cliente"""
    data = cargar_clientes()
    for i, cli in enumerate(data["clientes"]):
        if cli.get("id") == cliente_id:
            nuevo_limite = cli.get("limite_credito", 0) + monto_adicional
            extension = {
                "monto": monto_adicional,
                "nuevo_limite": nuevo_limite,
                "fecha": datetime.now().isoformat(),
                "motivo": motivo
            }
            data["clientes"][i]["limite_credito"] = nuevo_limite
            if "extensiones" not in data["clientes"][i]:
                data["clientes"][i]["extensiones"] = []
            data["clientes"][i]["extensiones"].append(extension)
            guardar_clientes(data)
            return {"ok": True, "nuevo_limite": nuevo_limite}
    return {"ok": False, "error": "Cliente no encontrado"}


# ==================== FUNCIONES DE FÓRMULAS ====================
def obtener_valores_columnas(cliente_data):
    """Obtiene los valores numéricos de las columnas para evaluar fórmulas"""
    valores = {}
    
    # Mapeo de letras a campos
    for letra, campo in COLUMNAS_NUMERICAS_MAP.items():
        valor = cliente_data.get(campo.lower(), 0)
        try:
            valores[letra] = float(valor)
        except (ValueError, TypeError):
            valores[letra] = 0
    
    # Columnas adicionales (O, P, Q, ...)
    col_adicionales = cliente_data.get("columnas_adicionales", {})
    for i, (key, value) in enumerate(col_adicionales.items()):
        letra = chr(79 + i)  # O, P, Q, ...
        try:
            valores[letra] = float(value)
        except (ValueError, TypeError):
            valores[letra] = 0
    
    return valores


def evaluar_formula(formula, valores_columnas):
    """Evalúa una fórmula con valores de columnas"""
    if not formula:
        return 0
    
    formula = formula.strip()
    if formula.startswith('='):
        formula = formula[1:]
    
    if not formula:
        return 0
    
    formula_upper = formula.upper()
    
    # Reemplazar letras por valores
    for letra, valor in valores_columnas.items():
        pattern = r'\b' + letra + r'\b'
        formula_upper = re.sub(pattern, f'({valor})', formula_upper)
        pattern_minus = r'\b' + letra.lower() + r'\b'
        formula_upper = re.sub(pattern_minus, f'({valor})', formula_upper)
    
    # Limpiar caracteres no permitidos
    formula_upper = re.sub(r'[^0-9+\-*/()\. ]', '', formula_upper)
    
    if not formula_upper or formula_upper.strip() == '':
        return 0
    
    try:
        resultado = eval(formula_upper, {"__builtins__": {}})
        return float(resultado) if isinstance(resultado, (int, float)) else 0
    except Exception as e:
        print(f"[ERROR] Evaluando fórmula: {formula_upper} -> {e}")
        return 0


def calcular_costo_total(cliente_data):
    """Calcula el costo total de un cliente según su fórmula"""
    formula = cliente_data.get('formula', '=E+F+G+H+K+L+M+N')
    if not formula or formula.strip() == '':
        formula = '=E+F+G+H+K+L+M+N'
    
    if not formula.startswith('='):
        formula = '=' + formula
    
    valores = obtener_valores_columnas(cliente_data)
    return evaluar_formula(formula, valores)


def resolver_valor_celda(cli, col):
    """Mapea de forma inteligente el nombre de la columna al valor real del JSON sin importar mayúsculas"""
    col_upper = col.upper()
    
    # 1. Resolver campos nativos mapeados
    if col_upper == "CLIENTE":
        return cli.get("nombre", "")
    if col_upper == "TIPO":
        return cli.get("tipo", "")
    if col_upper == "ORIGEN":
        return cli.get("origen", "")
    if col_upper == "DESTINO":
        return cli.get("destino", "")
    if col_upper == "COSTO TOTAL":
        return cli.get("costo_total", 0)
    if col_upper in ["BONO 1", "BONO1"]:
        return cli.get("bono1", "")
    if col_upper in ["BONO 2", "BONO2"]:
        return cli.get("bono2", "")
    if col_upper in ["VIATICO 1", "VIATICO1"]:
        return cli.get("viatico1", 0)
    if col_upper in ["VIATICO 2", "VIATICO2"]:
        return cli.get("viatico2", 0)
    if col_upper == "DIESEL MAX":
        return cli.get("diesel_max", 0)
    if col_upper == "GASOLINA MAX":
        return cli.get("gasolina_max", 0)
        
    # 2. Intentar por clave directa en minúsculas en la raíz (ej: 'diesel', 'traslado', 'distancia')
    clave_directa = col.lower().replace(" ", "_")
    if clave_directa in cli:
        return cli[clave_directa]
    if col.lower() in cli:
        return cli[col.lower()]
        
    # 3. Buscar en columnas_adicionales (Insensible a mayúsculas/minúsculas y espacios)
    col_adicionales = cli.get("columnas_adicionales", {})
    if col_adicionales:
        # Búsqueda directa
        if col in col_adicionales:
            return col_adicionales[col]
        if col.lower() in col_adicionales:
            return col_adicionales[col.lower()]
        if col_upper in col_adicionales:
            return col_adicionales[col_upper]
            
        # Búsqueda por normalización (ignorando mayúsculas y espacios)
        norm_col = col_upper.replace(" ", "").strip()
        for k, v in col_adicionales.items():
            if k.upper().replace(" ", "").strip() == norm_col:
                return v
                
    return ""


# ==================== API ENDPOINTS ====================
def api_clientes_completos():
    """Obtiene todos los clientes con su configuración"""
    try:
        data = cargar_clientes()
        clientes = data.get("clientes", [])
        
        # Calcular costo total para cada cliente
        for cli in clientes:
            cli['costo_total'] = calcular_costo_total(cli)
        
        config = obtener_config_clientes()
        
        return jsonify({
            "ok": True,
            "clientes": clientes,
            "config": config
        })
    except Exception as e:
        print(f"[ERROR] api_clientes_completos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e), "clientes": []})


def api_obtener_cliente(cliente_id):
    """Obtiene un cliente específico"""
    try:
        cli = obtener_cliente(cliente_id)
        if not cli:
            return jsonify({"ok": False, "error": "Cliente no encontrado"})
        
        cli['costo_total'] = calcular_costo_total(cli)
        return jsonify({"ok": True, "cliente": cli})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_guardar_cliente():
    """Guarda un cliente (crea o actualiza)"""
    try:
        data = request.get_json()
        print(f"[DEBUG] Datos recibidos en api_guardar_cliente: {data}")
        
        cliente_id = data.get("id")
        
        if not cliente_id:
            # Nuevo cliente
            if not data.get("nombre"):
                return jsonify({"ok": False, "error": "Nombre requerido"})
            
            nuevo = crear_cliente(data)
            if not nuevo:
                return jsonify({"ok": False, "error": "ID ya existe"})
            
            registrar_bitacora(
                data.get('usuario', 'sistema'),
                "Crear Cliente",
                f"ID: {nuevo.get('id')} - {nuevo.get('nombre')}",
                "Gestión Clientes"
            )
            
            print(f"[DEBUG] Cliente creado: {nuevo}")
            return jsonify({"ok": True, "cliente": nuevo})
        else:
            # Actualizar cliente existente
            existente = obtener_cliente(cliente_id)
            if not existente:
                return jsonify({"ok": False, "error": "Cliente no encontrado"})
            
            resultado = actualizar_cliente(cliente_id, data)
            if not resultado:
                return jsonify({"ok": False, "error": "Error al actualizar cliente"})
            
            cliente_actualizado = obtener_cliente(cliente_id)
            if cliente_actualizado:
                cliente_actualizado['costo_total'] = calcular_costo_total(cliente_actualizado)
            
            registrar_bitacora(
                data.get('usuario', 'sistema'),
                "Actualizar Cliente",
                f"ID: {cliente_id}",
                "Gestión Clientes"
            )
            
            print(f"[DEBUG] Cliente actualizado: {cliente_actualizado}")
            return jsonify({"ok": True, "cliente": cliente_actualizado})
            
    except Exception as e:
        print(f"[ERROR] api_guardar_cliente: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


def api_eliminar_cliente():
    """Elimina un cliente"""
    try:
        data = request.get_json()
        cliente_id = data.get("id")
        
        if not cliente_id:
            return jsonify({"ok": False, "error": "Se requiere id"})
        
        resultado = eliminar_cliente(cliente_id)
        if resultado:
            registrar_bitacora(
                data.get('usuario', 'sistema'),
                "Eliminar Cliente",
                f"ID: {cliente_id}",
                "Gestión Clientes"
            )
        return jsonify({"ok": resultado})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_actualizar_credito():
    """Actualiza el crédito de un cliente"""
    try:
        data = request.get_json()
        cliente_id = data.get("cliente_id")
        monto = float(data.get("monto", 0))
        es_abono = data.get("es_abono", False)
        
        resultado = actualizar_credito(cliente_id, monto, es_abono)
        if resultado.get("ok"):
            registrar_bitacora(
                data.get('usuario', 'sistema'),
                "Actualizar Crédito",
                f"Cliente: {cliente_id} - {resultado.get('mensaje')}",
                "Gestión Clientes"
            )
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_extender_limite():
    """Extiende el límite de crédito de un cliente"""
    try:
        data = request.get_json()
        cliente_id = data.get("cliente_id")
        monto = float(data.get("monto", 0))
        motivo = data.get("motivo", "")
        
        resultado = extender_limite(cliente_id, monto, motivo)
        if resultado.get("ok"):
            registrar_bitacora(
                data.get('usuario', 'sistema'),
                "Extender Límite",
                f"Cliente: {cliente_id} - +C${monto:,.2f}",
                "Gestión Clientes"
            )
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_alertas_credito():
    """Obtiene alertas de crédito de todos los clientes"""
    try:
        data = cargar_clientes()
        alertas = []
        for cli in data.get("clientes", []):
            credito = cli.get("credito", 0)
            limite = cli.get("limite_credito", 0)
            if limite > 0:
                if credito >= limite:
                    alertas.append({
                        "cliente_id": cli.get("id"),
                        "cliente_nombre": cli.get("nombre"),
                        "tipo": "BLOQUEADO",
                        "mensaje": f"CRÉDITO AGOTADO: {cli.get('nombre')} - Limite: C${limite:,.2f}",
                        "urgente": True
                    })
                elif credito >= limite * 0.9:
                    alertas.append({
                        "cliente_id": cli.get("id"),
                        "cliente_nombre": cli.get("nombre"),
                        "tipo": "CRITICO",
                        "mensaje": f"CRÉDITO CRÍTICO: {cli.get('nombre')} - {credito/limite*100:.0f}% usado",
                        "urgente": False
                    })
                elif credito >= limite * 0.7:
                    alertas.append({
                        "cliente_id": cli.get("id"),
                        "cliente_nombre": cli.get("nombre"),
                        "tipo": "ALERTA",
                        "mensaje": f"ALERTA: {cli.get('nombre')} - {credito/limite*100:.0f}% de crédito usado",
                        "urgente": False
                    })
        return jsonify({"alertas": alertas})
    except Exception as e:
        return jsonify({"alertas": [], "error": str(e)})


def api_estado_credito(cliente_id):
    """Obtiene el estado de crédito de un cliente"""
    try:
        cli = obtener_cliente(cliente_id)
        if not cli:
            return jsonify({"ok": False, "error": "Cliente no encontrado"})
        
        credito = cli.get("credito", 0)
        limite = cli.get("limite_credito", 0)
        disponible = limite - credito if limite > 0 else float('inf')
        porcentaje = (credito / limite * 100) if limite > 0 else 0
        
        estado = "disponible"
        if limite > 0 and credito >= limite:
            estado = "bloqueado"
        elif limite > 0 and credito > limite * 0.9:
            estado = "critico"
        elif limite > 0 and credito > limite * 0.7:
            estado = "alto"
        
        return jsonify({
            "ok": True,
            "estado": {
                "credito": credito,
                "limite": limite,
                "disponible": disponible if limite > 0 else float('inf'),
                "porcentaje": porcentaje,
                "estado": estado
            }
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def api_validar_cliente():
    """Valida la existencia de un cliente por ID"""
    try:
        data = request.get_json()
        cliente_id = data.get('id', '').strip().upper()
        cli = obtener_cliente(cliente_id)
        if cli:
            return jsonify({
                "valido": True,
                "nombre": cli.get('nombre', ''),
                "tipo": cli.get('tipo', 'Cliente'),
                "ruc": cli.get('cedula', ''),
                "email": cli.get('email', ''),
                "telefono": cli.get('telefono', ''),
                "direccion": cli.get('direccion', ''),
                "destino": cli.get('destino', ''),
                "placa": cli.get('placa', ''),
                "contacto": cli.get('contacto', ''),
                "conductor": cli.get('conductor', ''),
                "credito": cli.get('credito', 0),
                "limite_credito": cli.get('limite_credito', 0),
                "costo_total": cli.get('costo_total', 0)
            })
        return jsonify({"valido": False})
    except Exception as e:
        return jsonify({"valido": False})


# ==================== API GUARDAR CONFIGURACIÓN ====================
def api_guardar_config():
    """Guarda la configuración de columnas"""
    try:
        data = request.get_json()
        config = obtener_config_clientes()
        
        if 'columnas' in data:
            config['columnas'] = data['columnas']
        if 'nombres_mostrados' in data:
            config['nombres_mostrados'] = data['nombres_mostrados']
        if 'columnas_protegidas' in data:
            config['columnas_protegidas'] = data['columnas_protegidas']
        if 'columnas_numericas' in data:
            config['columnas_numericas'] = data['columnas_numericas']
        
        if guardar_config_clientes(config):
            registrar_bitacora(
                data.get('usuario', 'sistema'),
                "Guardar Configuración Clientes",
                "Configuración de columnas actualizada",
                "Gestión Clientes"
            )
            return jsonify({"ok": True, "config": config})
        return jsonify({"ok": False, "error": "Error al guardar configuración"})
    except Exception as e:
        print(f"[ERROR] api_guardar_config: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


def api_obtener_config():
    """Obtiene la configuración de columnas"""
    try:
        config = obtener_config_clientes()
        return jsonify({"ok": True, "config": config})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ==================== EXPORTAR EXCEL ====================
def api_exportar_excel():
    """Exporta todos los clientes a Excel (soporta GET y POST)"""
    try:
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        except ImportError:
            return jsonify({"ok": False, "error": "openpyxl no instalado. Ejecute: pip install openpyxl"})
        
        if request.method == 'GET':
            incluir_rutas = request.args.get('rutas', '1') == '1'
            incluir_saldo = request.args.get('saldo', '1') == '1'
        else:
            data = request.get_json() or {}
            incluir_rutas = data.get('rutas', True)
            incluir_saldo = data.get('saldo', True)
        
        data = cargar_clientes()
        clientes = data.get("clientes", [])
        config = obtener_config_clientes()
        columnas = config.get("columnas", COLUMNAS_DEFAULT)
        nombres_mostrados = config.get("nombres_mostrados", NOMBRES_MOSTRADOS_DEFAULT)
        columnas_numericas = config.get("columnas_numericas", COLUMNAS_NUMERICAS_DEFAULT)
        
        if not clientes:
            return jsonify({"ok": False, "error": "No hay datos para exportar"})
        
        for cli in clientes:
            cli['costo_total'] = calcular_costo_total(cli)
        
        if not CARPETA_EXCEL_CLIENTES:
            return jsonify({"ok": False, "error": "Carpeta de exportación no configurada"})
        
        os.makedirs(CARPETA_EXCEL_CLIENTES, exist_ok=True)
        wb = Workbook()
        
        # ===== HOJA 1: RUTAS =====
        if incluir_rutas:
            ws_rutas = wb.create_sheet("Rutas")
            headers = [nombres_mostrados.get(col, col) for col in columnas]
            
            header_font = Font(bold=True, color="FFFFFF", size=10)
            header_fill = PatternFill(start_color="0D9488", end_color="0D9488", fill_type="solid")
            center_alignment = Alignment(horizontal="center", vertical="center")
            thin_border = Border(
                left=Side(style='thin', color='CCCCCC'), right=Side(style='thin', color='CCCCCC'),
                top=Side(style='thin', color='CCCCCC'), bottom=Side(style='thin', color='CCCCCC')
            )
            
            for col_idx, header in enumerate(headers, 1):
                cell = ws_rutas.cell(row=1, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
                cell.border = thin_border
            
            for row_idx, cli in enumerate(clientes, 2):
                for col_idx, col in enumerate(columnas, 1):
                    valor = resolver_valor_celda(cli, col)
                    
                    es_numerica = col in columnas_numericas or col.upper() == "COSTO TOTAL"
                    if es_numerica:
                        try:
                            valor = float(valor) if valor != "" else 0
                            ws_rutas.cell(row=row_idx, column=col_idx, value=round(valor, 2))
                        except (ValueError, TypeError):
                            ws_rutas.cell(row=row_idx, column=col_idx, value=0)
                    else:
                        ws_rutas.cell(row=row_idx, column=col_idx, value=str(valor) if valor is not None else "")
                    
                    ws_rutas.cell(row=row_idx, column=col_idx).alignment = center_alignment
                    ws_rutas.cell(row=row_idx, column=col_idx).border = thin_border
            
            for col_idx in range(1, len(headers) + 1):
                max_length = 0
                for row_idx in range(1, len(clientes) + 2):
                    cell = ws_rutas.cell(row=row_idx, column=col_idx)
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                ws_rutas.column_dimensions[chr(64 + col_idx)].width = min(max_length + 3, 35)
        
        # ===== HOJA 2: SALDO =====
        if incluir_saldo:
            ws_saldo = wb.create_sheet("Saldo")
            saldo_headers = ['ID', 'Cliente', 'Límite', 'Gastado', 'Disponible', '% Uso', 'Estado']
            
            header_font = Font(bold=True, color="FFFFFF", size=10)
            header_fill = PatternFill(start_color="0D9488", end_color="0D9488", fill_type="solid")
            center_alignment = Alignment(horizontal="center", vertical="center")
            thin_border = Border(
                left=Side(style='thin', color='CCCCCC'), right=Side(style='thin', color='CCCCCC'),
                top=Side(style='thin', color='CCCCCC'), bottom=Side(style='thin', color='CCCCCC')
            )
            
            for col_idx, header in enumerate(saldo_headers, 1):
                cell = ws_saldo.cell(row=1, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
                cell.border = thin_border
            
            for row_idx, cli in enumerate(clientes, 2):
                cred = float(cli.get('credito', 0))
                lim = float(cli.get('limite_credito', 0))
                disponible = max(0, lim - cred)
                pct = (cred / lim * 100) if lim > 0 else 0
                
                if lim > 0 and cred >= lim:
                    estado = 'BLOQUEADO'
                elif pct >= 90:
                    estado = 'CRITICO'
                elif pct >= 70:
                    estado = 'ALERTA'
                elif cred > 0:
                    estado = 'DEBE'
                else:
                    estado = 'DISPONIBLE'
                
                ws_saldo.cell(row=row_idx, column=1, value=cli.get('id', ''))
                ws_saldo.cell(row=row_idx, column=2, value=cli.get('nombre', ''))
                ws_saldo.cell(row=row_idx, column=3, value=round(lim, 2))
                ws_saldo.cell(row=row_idx, column=4, value=round(cred, 2))
                ws_saldo.cell(row=row_idx, column=5, value=round(disponible, 2))
                ws_saldo.cell(row=row_idx, column=6, value=round(pct))
                ws_saldo.cell(row=row_idx, column=7, value=estado)
                
                for col_idx in range(1, 8):
                    ws_saldo.cell(row=row_idx, column=col_idx).alignment = center_alignment
                    ws_saldo.cell(row=row_idx, column=col_idx).border = thin_border
            
            for col_idx in range(1, len(saldo_headers) + 1):
                max_length = 0
                for row_idx in range(1, len(clientes) + 2):
                    cell = ws_saldo.cell(row=row_idx, column=col_idx)
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                ws_saldo.column_dimensions[chr(64 + col_idx)].width = min(max_length + 3, 30)
        
        if len(wb.sheetnames) > 1 and 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"clientes_{timestamp}.xlsx"
        filepath = os.path.join(CARPETA_EXCEL_CLIENTES, filename)
        wb.save(filepath)
        
        registrar_bitacora(
            'sistema', "Exportar Excel Clientes",
            f"Archivo: {filename} - {len(clientes)} clientes", "Gestión Clientes"
        )
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"[ERROR] api_exportar_excel: {e}")
        return jsonify({"ok": False, "error": str(e)})


# ==================== EXPORTAR PDF ADAPTATIVO ====================
def api_exportar_pdf():
    """Exporta clientes a PDF con páginas calculadas dinámicamente según el ancho de la tabla"""
    try:
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.units import cm
        
        if request.method == 'GET':
            incluir_rutas = request.args.get('rutas', '1') == '1'
            incluir_saldo = request.args.get('saldo', '1') == '1'
        else:
            data = request.get_json() or {}
            incluir_rutas = data.get('rutas', True)
            incluir_saldo = data.get('saldo', True)
        
        data = cargar_clientes()
        clientes = data.get("clientes", [])
        config = obtener_config_clientes()
        columnas = config.get("columnas", COLUMNAS_DEFAULT)
        nombres_mostrados = config.get("nombres_mostrados", NOMBRES_MOSTRADOS_DEFAULT)
        columnas_numericas = config.get("columnas_numericas", COLUMNAS_NUMERICAS_DEFAULT)
        
        if not clientes:
            return jsonify({"ok": False, "error": "No hay datos para exportar"})
        
        for cli in clientes:
            cli['costo_total'] = calcular_costo_total(cli)
        
        if not CARPETA_PDF_CLIENTES:
            return jsonify({"ok": False, "error": "Carpeta de exportación no configurada"})
        
        os.makedirs(CARPETA_PDF_CLIENTES, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"clientes_{timestamp}.pdf"
        filepath = os.path.join(CARPETA_PDF_CLIENTES, filename)
        
        # 1. CÁLCULO INTELIGENTE DEL ANCHO DE COLUMNAS (Evita desbordes)
        col_widths = []
        for col in columnas:
            nombre = nombres_mostrados.get(col, col)
            # El Cliente y Destinos necesitan más aire, las numéricas menos
            if col.upper() == "CLIENTE":
                w = 4.2 * cm
            elif col.upper() in ["ORIGEN", "DESTINO"]:
                w = 2.5 * cm
            else:
                w = max(len(nombre) * 0.22, 1.2) * cm
            col_widths.append(w)
            
        # 2. DEFINICIÓN ADAPTATIVA DE LA PÁGINA (Estira la hoja si hay más columnas)
        margen = 1.0 * cm
        ancho_tabla = sum(col_widths)
        ancho_pagina = ancho_tabla + (margen * 2)
        alto_pagina = 21.0 * cm  # Proporción horizontal estándar (similar a A4 horizontal)
        
        # Si la tabla es muy pequeña, fijamos un tamaño mínimo para mantener estética
        if ancho_pagina < 29.7 * cm:
            ancho_pagina = 29.7 * cm  # Ancho base de un A4 Horizontal
        
        # Crear plantilla con dimensiones dinámicas calculadas en caliente
        doc = SimpleDocTemplate(filepath, pagesize=(ancho_pagina, alto_pagina),
                               topMargin=margen, bottomMargin=margen,
                               leftMargin=margen, rightMargin=margen)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=14, textColor=colors.HexColor("#0D9488"))
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9, textColor=colors.HexColor("#666666"))
        
        elements = []
        elements.append(Paragraph("Lista de Clientes", title_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 10))
        
        # ===== SECCIÓN RUTAS =====
        if incluir_rutas:
            headers = [nombres_mostrados.get(col, col) for col in columnas]
            table_data = [headers]
            
            for cli in clientes[:200]:
                row = []
                for col in columnas:
                    valor = resolver_valor_celda(cli, col)
                    
                    if col in columnas_numericas or col.upper() == "COSTO TOTAL":
                        try:
                            valor = float(valor) if valor != "" else 0
                            row.append(f"C${valor:,.2f}")
                        except (ValueError, TypeError):
                            row.append("C$0.00")
                    else:
                        row.append(str(valor) if valor is not None else "")
                table_data.append(row)
            
            tabla_rutas = Table(table_data, colWidths=col_widths, repeatRows=1)
            tabla_rutas.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0D9488")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 7.5),
                ('FONTSIZE', (0,1), (-1,-1), 6.5),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
            ]))
            
            elements.append(Paragraph("📊 Tabla de Rutas y Costos", ParagraphStyle('SecTitle', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor("#0D9488"), spaceAfter=5)))
            elements.append(tabla_rutas)
            elements.append(Spacer(1, 15))
        
        # ===== SECCIÓN SALDO =====
        if incluir_saldo:
            saldo_headers = ['ID', 'Cliente', 'Límite', 'Gastado', 'Disponible', '% Uso', 'Estado']
            saldo_data = [saldo_headers]
            
            for cli in clientes[:200]:
                cred = float(cli.get('credito', 0))
                lim = float(cli.get('limite_credito', 0))
                disponible = max(0, lim - cred)
                pct = (cred / lim * 100) if lim > 0 else 0
                
                if lim > 0 and cred >= lim:
                    estado = 'BLOQUEADO'
                elif pct >= 90:
                    estado = 'CRITICO'
                elif pct >= 70:
                    estado = 'ALERTA'
                elif cred > 0:
                    estado = 'DEBE'
                else:
                    estado = 'DISPONIBLE'
                
                saldo_data.append([
                    cli.get('id', ''),
                    cli.get('nombre', ''),
                    f"C${lim:,.2f}",
                    f"C${cred:,.2f}",
                    f"C${disponible:,.2f}",
                    f"{pct:.0f}%",
                    estado
                ])
            
            # Anchos equilibrados para la tabla de saldos de modo que use el espacio correspondiente
            ancho_restante = max(29.7 * cm, ancho_pagina) - (margen * 2)
            w_id = 2.2 * cm
            w_lim = w_gas = w_disp = w_pct = w_est = 2.5 * cm
            w_cli = max(4.5 * cm, ancho_restante - (w_id + w_lim + w_gas + w_disp + w_pct + w_est))
            
            col_widths_saldo = [w_id, w_cli, w_lim, w_gas, w_disp, w_pct, w_est]
            tabla_saldo = Table(saldo_data, colWidths=col_widths_saldo, repeatRows=1)
            tabla_saldo.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0D9488")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 8),
                ('FONTSIZE', (0,1), (-1,-1), 7),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
            ]))
            
            elements.append(Paragraph("💰 Tabla de Saldo y Crédito", ParagraphStyle('SecTitle2', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor("#0D9488"), spaceAfter=5)))
            elements.append(tabla_saldo)
            elements.append(Spacer(1, 15))
        
        elements.append(Paragraph("Grupo GSN - Sistema de Gestión de Combustible", ParagraphStyle('Foot', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, textColor=colors.HexColor("#999999"))))
        doc.build(elements)
        
        registrar_bitacora('sistema', "Exportar PDF Clientes", f"Archivo: {filename}", "Gestión Clientes")
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except ImportError as e:
        return jsonify({"ok": False, "error": f"ReportLab no instalado: {str(e)}"})
    except Exception as e:
        print(f"[ERROR] api_exportar_pdf: {e}")
        return jsonify({"ok": False, "error": str(e)})


# ==================== REGISTRO DE RUTAS ====================
def registrar_rutas(app):
    if not app:
        return
    
    @app.route('/api/clientes', methods=['GET'])
    def clientes_route():
        return api_clientes_completos()
    
    @app.route('/api/cliente/<cliente_id>', methods=['GET'])
    def cliente_route(cliente_id):
        return api_obtener_cliente(cliente_id)
    
    @app.route('/api/guardar_cliente', methods=['POST'])
    def guardar_cliente_route():
        return api_guardar_cliente()
    
    @app.route('/api/eliminar_cliente', methods=['POST'])
    def eliminar_cliente_route():
        return api_eliminar_cliente()
    
    @app.route('/api/actualizar_credito', methods=['POST'])
    def actualizar_credito_route():
        return api_actualizar_credito()
    
    @app.route('/api/extender_limite', methods=['POST'])
    def extender_limite_route():
        return api_extender_limite()
    
    @app.route('/api/alertas_credito', methods=['GET'])
    def alertas_credito_route():
        return api_alertas_credito()
    
    @app.route('/api/estado_credito/<cliente_id>', methods=['GET'])
    def estado_credito_route(cliente_id):
        return api_estado_credito(cliente_id)
    
    @app.route('/api/validar_cliente', methods=['POST'])
    def validar_cliente_route():
        return api_validar_cliente()
    
    @app.route('/api/exportar_clientes_excel', methods=['GET', 'POST'])
    def exportar_excel_route():
        return api_exportar_excel()
    
    @app.route('/api/exportar_clientes_pdf', methods=['GET', 'POST'])
    def exportar_pdf_route():
        return api_exportar_pdf()
    
    @app.route('/api/guardar_config_clientes', methods=['POST'])
    def guardar_config_route():
        return api_guardar_config()
    
    @app.route('/api/obtener_config_clientes', methods=['GET'])
    def obtener_config_route():
        return api_obtener_config()
    
    print("[INFO] Rutas de Gestión Clientes registradas")


# ==================== INICIALIZACIÓN ====================
def inicializar_gestion(main_funciones=None, rutas=None):
    inicializar_gestion_clientes(main_funciones, rutas)
    
    return {
        'clientes': api_clientes_completos,
        'obtener_cliente': api_obtener_cliente,
        'guardar_cliente': api_guardar_cliente,
        'eliminar_cliente': api_eliminar_cliente,
        'actualizar_credito': api_actualizar_credito,
        'extender_limite': api_extender_limite,
        'alertas': api_alertas_credito,
        'estado_credito': api_estado_credito,
        'validar': api_validar_cliente,
        'exportar_excel': api_exportar_excel,
        'exportar_pdf': api_exportar_pdf,
        'guardar_config': api_guardar_config,
        'obtener_config': api_obtener_config,
    }