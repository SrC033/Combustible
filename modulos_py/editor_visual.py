# ==================== MÓDULO EDITOR VISUAL ====================
import os
import json
from datetime import datetime
from flask import jsonify, request

# Variables globales del editor
_paginas_hijo_module = None
_ruta_json_paginas = None

def inicializar_editor(module):
    """Inicializa el editor con el módulo de páginas hijo"""
    global _paginas_hijo_module, _ruta_json_paginas
    _paginas_hijo_module = module
    
    # Obtener la ruta del JSON desde el módulo paginas_hijo
    if module and hasattr(module, 'ARCHIVO_PAGINAS'):
        _ruta_json_paginas = module.ARCHIVO_PAGINAS
        print(f"[OK] Editor Visual inicializado con JSON: {_ruta_json_paginas}")
    else:
        # Ruta directa a tu archivo (fallback)
        _ruta_json_paginas = r"C:\combustible\datos\paginas.json"
        print(f"[OK] Editor Visual inicializado (ruta directa): {_ruta_json_paginas}")

def obtener_todas_paginas():
    """Obtiene todas las páginas directamente del archivo JSON"""
    global _ruta_json_paginas
    
    if not _ruta_json_paginas:
        print("[ERROR] No hay ruta de JSON configurada")
        return []
    
    try:
        if not os.path.exists(_ruta_json_paginas):
            print(f"[ERROR] No existe el archivo: {_ruta_json_paginas}")
            return []
        
        with open(_ruta_json_paginas, 'r', encoding='utf-8') as f:
            contenido = f.read().strip()
            if not contenido:
                return []
            data = json.loads(contenido)
            
            # El JSON tiene estructura {"paginas": [...]}
            if isinstance(data, dict):
                paginas = data.get("paginas", [])
                print(f"[DEBUG] Cargadas {len(paginas)} páginas desde {_ruta_json_paginas}")
                for p in paginas:
                    print(f"   - {p.get('nombre')} ({p.get('url_id')})")
                return paginas
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[ERROR] Error leyendo paginas.json: {e}")
        return []

def obtener_pagina(id_pagina):
    """Obtiene una página por su ID"""
    paginas = obtener_todas_paginas()
    for pagina in paginas:
        if pagina.get("id") == id_pagina:
            return pagina
    return None

def actualizar_pagina(id_pagina, datos):
    """Actualiza una página en el archivo JSON"""
    global _ruta_json_paginas
    
    if not _ruta_json_paginas:
        return False
    
    try:
        if not os.path.exists(_ruta_json_paginas):
            return False
        
        with open(_ruta_json_paginas, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        
        # Asegurar estructura correcta
        if isinstance(file_data, dict):
            paginas = file_data.get("paginas", [])
        else:
            paginas = file_data if isinstance(file_data, list) else []
            file_data = {"paginas": paginas}
        
        encontrada = False
        for i, pagina in enumerate(paginas):
            if pagina.get("id") == id_pagina:
                if "estilos" in datos:
                    paginas[i]["estilos"] = datos["estilos"]
                if "elementos" in datos:
                    paginas[i]["elementos"] = datos["elementos"]
                if "nombre" in datos:
                    paginas[i]["nombre"] = datos["nombre"]
                paginas[i]["fecha"] = datetime.now().isoformat()
                encontrada = True
                break
        
        if not encontrada:
            return False
        
        file_data["paginas"] = paginas
        with open(_ruta_json_paginas, 'w', encoding='utf-8') as f:
            json.dump(file_data, f, indent=2, ensure_ascii=False)
        
        print(f"[INFO] Página {id_pagina} guardada correctamente")
        return True
    except Exception as e:
        print(f"[ERROR] Error actualizando página: {e}")
        return False

# ==================== API ENDPOINTS ====================

def api_listar_paginas_editor():
    """Lista todas las páginas para el selector del editor"""
    try:
        print("[DEBUG] api_listar_paginas_editor llamada")
        paginas = obtener_todas_paginas()
        
        lista_paginas = []
        for p in paginas:
            if p.get("activa", True):
                lista_paginas.append({
                    "id": p.get("id"),
                    "nombre": p.get("nombre"),
                    "url_id": p.get("url_id"),
                    "fecha": p.get("fecha")
                })
        
        print(f"[INFO] Editor: {len(lista_paginas)} páginas cargadas")
        return jsonify({"ok": True, "paginas": lista_paginas})
    except Exception as e:
        print(f"[ERROR] api_listar_paginas_editor: {e}")
        return jsonify({"ok": False, "error": str(e), "paginas": []})

def api_obtener_pagina_editor(id_pagina):
    """Obtiene una página para editar"""
    try:
        print(f"[DEBUG] api_obtener_pagina_editor: {id_pagina}")
        pagina = obtener_pagina(id_pagina)
        
        if pagina:
            if "elementos" not in pagina:
                pagina["elementos"] = []
            if "estilos" not in pagina:
                pagina["estilos"] = {
                    "color_primario": "#f59e0b",
                    "color_secundario": "#d97706", 
                    "color_fondo": "#0f0f1a",
                    "titulo": pagina.get("nombre", "Página"),
                    "subtitulo": "Complete el formulario de pedido de combustible"
                }
            print(f"[DEBUG] Página encontrada: {pagina.get('nombre')}")
            return jsonify({"ok": True, "pagina": pagina})
        
        print(f"[DEBUG] Página no encontrada: {id_pagina}")
        return jsonify({"ok": False, "error": "Página no encontrada"})
    except Exception as e:
        print(f"[ERROR] api_obtener_pagina_editor: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_guardar_pagina_editor():
    """Guarda una página editada"""
    try:
        data = request.get_json()
        print(f"[DEBUG] api_guardar_pagina_editor: {data.get('id') if data else 'None'}")
        
        id_pagina = data.get('id')
        if not id_pagina:
            return jsonify({"ok": False, "error": "ID de página no proporcionado"})
        
        estilos = data.get('estilos', {})
        elementos = data.get('elementos', [])
        
        datos_actualizar = {
            "estilos": estilos,
            "elementos": elementos
        }
        
        resultado = actualizar_pagina(id_pagina, datos_actualizar)
        
        if resultado:
            return jsonify({"ok": True, "mensaje": "Página guardada correctamente"})
        else:
            return jsonify({"ok": False, "error": "No se pudo guardar la página"})
    except Exception as e:
        print(f"[ERROR] api_guardar_pagina_editor: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_previsualizar_pagina():
    """Previsualiza una página sin guardar"""
    try:
        data = request.get_json()
        estilos = data.get('estilos', {})
        elementos = data.get('elementos', [])
        
        color_primario = estilos.get("color_primario", "#f59e0b")
        color_fondo = estilos.get("color_fondo", "#0f0f1a")
        titulo = estilos.get("titulo", "Título de la Página")
        subtitulo = estilos.get("subtitulo", "Complete el formulario")
        
        elementos_html = ""
        for elem in elementos:
            if elem.get("tipo") == "select":
                opciones_html = ""
                for opt in elem.get("opciones", []):
                    opciones_html += f'<option value="{opt}">{opt}</option>'
                elementos_html += f'''
                <div style="margin-bottom: 15px;">
                    <label style="display: block; font-size: 12px; color: #a0a0c0; margin-bottom: 5px;">{elem.get("texto", "Seleccione")}</label>
                    <select style="width: 100%; padding: 10px; border-radius: 12px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); color: white;">
                        <option value="">Seleccione...</option>
                        {opciones_html}
                    </select>
                </div>'''
            else:
                elementos_html += f'''
                <div style="margin-bottom: 15px;">
                    <label style="display: block; font-size: 12px; color: #a0a0c0; margin-bottom: 5px;">{elem.get("texto", "Texto")}</label>
                    <input type="text" style="width: 100%; padding: 10px; border-radius: 12px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); color: white;" placeholder="{elem.get('placeholder', '')}">
                </div>'''
        
        html = f'''
        <div style="background: {color_fondo}; padding: 20px; border-radius: 20px;">
            <div style="text-align:center; margin-bottom:25px;">
                <div style="font-size:48px;"><i class="fas fa-gas-pump" style="color: {color_primario};"></i></div>
                <h3 style="color: {color_primario};">{titulo}</h3>
                <p style="color: #aaa;">{subtitulo}</p>
            </div>
            {elementos_html if elementos_html else '<div style="text-align: center; color: #666; padding: 40px;"><i class="fas fa-info-circle"></i> No hay elementos agregados</div>'}
            <div style="margin-top:20px; padding:15px; background:rgba(16,185,129,0.1); border-radius:16px; text-align:center;">
                <div>💰 Precio por galón: C$0.00</div>
                <div style="font-size:18px; font-weight:bold; color:#10b981;">TOTAL: C$0.00</div>
            </div>
            <button style="width:100%; margin-top:15px; padding:12px; background:linear-gradient(135deg,#10b981,#059669); color:white; border:none; border-radius:30px; cursor:pointer;">📤 Enviar Pedido</button>
        </div>
        '''
        return jsonify({"ok": True, "html": html})
    except Exception as e:
        print(f"[ERROR] api_previsualizar_pagina: {e}")
        return jsonify({"ok": False, "error": str(e)})