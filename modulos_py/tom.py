# ==================== TOM - ASISTENTE INTELIGENTE ====================
"""
Modulo que proporciona acceso a los datos del sistema para el asistente TOM
Optimizado para Qwen2.5-1.5B-Instruct-Q4_K_M.gguf
RESPUESTAS GENERADAS POR EL MODELO CON DATOS REALES DE LA BITÁCORA
"""

import os
import json
from flask import jsonify, request, session
import re
import sys
import traceback
import time
from datetime import datetime
from collections import deque

print("[TOM] Iniciando módulo con datos de la bitácora...")

# ==================== INTENTAR IMPORTAR LLAMA-CPP-PYTHON ====================
LLAMA_AVAILABLE = False
_llm = None

try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
    print("[TOM] ✅ llama-cpp-python disponible")
except ImportError as e:
    print(f"[TOM] ⚠️ llama-cpp-python no disponible: {e}")

# ==================== CONFIGURACION ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELO = r"C:\Users\PC\Documents\combustible\combustible\modelos\qwen2.5-1.5b-instruct-q4_k_m.gguf"

# Buscar modelo en ubicaciones alternativas
if not os.path.exists(MODELO):
    rutas_busqueda = [
        os.path.join(BASE_DIR, "modelos", "qwen2.5-1.5b-instruct-q4_k_m.gguf"),
        os.path.join(os.getcwd(), "modelos", "qwen2.5-1.5b-instruct-q4_k_m.gguf"),
        os.path.join(os.path.dirname(__file__), "modelos", "qwen2.5-1.5b-instruct-q4_k_m.gguf"),
    ]
    for ruta in rutas_busqueda:
        if os.path.exists(ruta):
            MODELO = ruta
            break

print(f"[TOM] Modelo: {MODELO if os.path.exists(MODELO) else 'No encontrado'}")

# ==================== CARGAR MODELO ====================
def cargar_modelo():
    global _llm, LLAMA_AVAILABLE
    if not LLAMA_AVAILABLE or _llm is not None:
        return True
    if not os.path.exists(MODELO):
        print(f"[TOM] ❌ Modelo no encontrado: {MODELO}")
        return False
    try:
        print("[TOM] 🚀 Cargando modelo...")
        _llm = Llama(model_path=MODELO, n_ctx=8192, n_threads=4, verbose=False)
        print("[TOM] ✅ Modelo cargado correctamente!")
        return True
    except Exception as e:
        print(f"[TOM] ❌ Error cargando modelo: {e}")
        return False

if LLAMA_AVAILABLE:
    cargar_modelo()

# ==================== RUTA DE DATOS ====================
DATOS_DIR = r"C:\Users\PC\Documents\combustible\combustible\datos"
BITACORA_PATH = os.path.join(DATOS_DIR, "bitacora_data.json")
TABLAS_EDITABLES_PATH = os.path.join(DATOS_DIR, "tablas_editables.json")

# ==================== HISTORIAL DE CONVERSACIÓN ====================
HISTORIAL_MAX = 10  # Mantener últimas 10 interacciones
historial_conversacion = deque(maxlen=HISTORIAL_MAX)

def agregar_al_historial(rol, mensaje):
    """Agrega un mensaje al historial de conversación"""
    historial_conversacion.append({
        "rol": rol,
        "mensaje": mensaje,
        "timestamp": datetime.now().isoformat()
    })

def obtener_historial_texto():
    """Obtiene el historial como texto para el contexto"""
    if not historial_conversacion:
        return ""
    
    texto = "\n=== HISTORIAL DE CONVERSACIÓN ===\n"
    for item in historial_conversacion:
        rol = "Usuario" if item["rol"] == "user" else "TOM"
        texto += f"{rol}: {item['mensaje']}\n"
    return texto

# ==================== OBTENER DATOS DE LA BITÁCORA ====================

def cargar_bitacora():
    """Carga los datos desde la bitácora (bitacora_data.json o tablas_editables.json)"""
    
    # Intentar cargar desde bitacora_data.json primero
    if os.path.exists(BITACORA_PATH):
        try:
            with open(BITACORA_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"[TOM] 📂 Bitácora cargada: {len(data.get('empresas', []))} empresas, {len(data.get('pedidos', []))} pedidos")
                return data
        except Exception as e:
            print(f"[TOM] Error cargando bitacora_data.json: {e}")
    
    # Fallback: cargar desde tablas_editables.json
    if os.path.exists(TABLAS_EDITABLES_PATH):
        try:
            with open(TABLAS_EDITABLES_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"[TOM] 📂 Datos desde tablas_editables.json: {len(data.get('empresas', []))} empresas")
                return data
        except Exception as e:
            print(f"[TOM] Error cargando tablas_editables.json: {e}")
    
    # Intentar cargar desde tablas_editables.py
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("tablas_editables", 
            os.path.join(os.path.dirname(__file__), "tablas_editables.py"))
        if spec and spec.loader:
            tablas = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tablas)
            if hasattr(tablas, 'cargar_tablas_desde_archivo'):
                data = tablas.cargar_tablas_desde_archivo()
                print(f"[TOM] 📂 Datos desde tablas_editables.py: {len(data.get('empresas', []))} empresas")
                return data
    except Exception as e:
        print(f"[TOM] Error importando tablas_editables: {e}")
    
    return {
        "empresas": [],
        "pedidos": [],
        "pedidos_camino": [],
        "pedidos_entregados": [],
        "costos": [],
        "conductores": [],
        "camiones": [],
        "facturas": [],
        "reportes": []
    }

def obtener_todos_los_datos():
    """Obtiene TODOS los datos del sistema desde la bitácora"""
    
    bitacora = cargar_bitacora()
    
    empresas = bitacora.get('empresas', [])
    pedidos = bitacora.get('pedidos', [])
    pedidos_camino = bitacora.get('pedidos_camino', [])
    pedidos_entregados = bitacora.get('pedidos_entregados', [])
    costos = bitacora.get('costos', [])
    conductores = bitacora.get('conductores', [])
    camiones = bitacora.get('camiones', [])
    facturas = bitacora.get('facturas', [])
    reportes = bitacora.get('reportes', [])
    
    # ============================================================
    # 🔥 CALCULAR ESTADÍSTICAS DESDE DATOS REALES DE BITÁCORA
    # ============================================================
    
    # Total de pedidos (todos los estados)
    total_pedidos = len(pedidos) + len(pedidos_camino) + len(pedidos_entregados)
    
    # Total de galones
    total_galones = 0
    for p in pedidos:
        total_galones += float(p.get('galones', 0) or 0)
    for p in pedidos_camino:
        total_galones += float(p.get('galones', 0) or 0)
    for p in pedidos_entregados:
        total_galones += float(p.get('galones', 0) or 0)
    
    # Total de ventas
    total_ventas = 0
    for p in pedidos:
        total_ventas += float(p.get('total', p.get('costo_total', p.get('importe', 0))) or 0)
    for p in pedidos_camino:
        total_ventas += float(p.get('total', p.get('costo_total', 0)) or 0)
    for p in pedidos_entregados:
        total_ventas += float(p.get('total', p.get('costo_total', 0)) or 0)
    
    # Total facturado (desde facturas)
    total_facturado = sum(float(f.get('total', f.get('costo_total', 0)) or 0) for f in facturas)
    
    # Ventas entregadas
    ventas_entregadas = sum(float(p.get('total', p.get('costo_total', 0)) or 0) for p in pedidos_entregados)
    galones_entregados = sum(float(p.get('galones', 0) or 0) for p in pedidos_entregados)
    
    # Pedidos por tipo de combustible
    combustible_stats = {}
    for p in pedidos + pedidos_camino + pedidos_entregados:
        tipo = p.get('tipo_combustible', p.get('Combustible', 'Otro'))
        if tipo:
            combustible_stats[tipo] = combustible_stats.get(tipo, 0) + float(p.get('galones', 0) or 0)
    
    # Top clientes por compras
    compras_por_cliente = {}
    for p in pedidos + pedidos_camino + pedidos_entregados:
        cliente_id = p.get('empresa_id', p.get('cliente_id', p.get('ID', 'desconocido')))
        nombre = p.get('nombre', p.get('Cliente', p.get('empresa_nombre', 'Desconocido')))
        if cliente_id not in compras_por_cliente:
            compras_por_cliente[cliente_id] = {"nombre": nombre, "total": 0, "pedidos": 0}
        compras_por_cliente[cliente_id]["total"] += float(p.get('total', p.get('costo_total', p.get('importe', 0))) or 0)
        compras_por_cliente[cliente_id]["pedidos"] += 1
    
    top_clientes = sorted(
        [{"id": k, **v} for k, v in compras_por_cliente.items()],
        key=lambda x: x["total"],
        reverse=True
    )[:10]
    
    # Clientes con crédito
    clientes_con_credito = [e for e in empresas if e.get('credito', 0) > 0]
    
    # Resumen completo
    resumen = {
        "total_pedidos": total_pedidos,
        "total_galones": total_galones,
        "total_ventas": total_ventas,
        "total_facturado": total_facturado,
        "total_clientes": len(empresas),
        "total_conductores": len(conductores),
        "total_camiones": len(camiones),
        "total_facturas": len(facturas),
        "total_reportes": len(reportes),
        "total_costos": len(costos),
        # Pedidos por estado
        "pedidos_pendientes": len(pedidos),
        "pedidos_camino": len(pedidos_camino),
        "pedidos_entregados": len(pedidos_entregados),
        # 🔥 DATOS DE ENTREGADOS
        "galones_entregados": galones_entregados,
        "ventas_entregadas": ventas_entregadas,
        "combustible_stats": combustible_stats,
        "top_clientes": top_clientes,
        "clientes_con_credito": len(clientes_con_credito),
        "credito_total": sum(e.get('credito', 0) for e in clientes_con_credito),
    }
    
    return {
        "resumen": resumen,
        "empresas": empresas,
        "pedidos": pedidos,
        "pedidos_camino": pedidos_camino,
        "pedidos_entregados": pedidos_entregados,
        "costos": costos,
        "conductores": conductores,
        "camiones": camiones,
        "facturas": facturas,
        "reportes": reportes,
        "bitacora": bitacora
    }

# ==================== GENERAR RESPUESTA CON EL MODELO ====================

def generar_respuesta(pregunta: str) -> str:
    """Genera respuesta usando el modelo LLM con los datos de la bitácora"""
    try:
        print(f"[TOM] 📝 Procesando: {pregunta[:50]}...")
        
        # Detectar modo
        es_general = "[GENERAL]" in pregunta
        pregunta_limpia = pregunta.replace("[GENERAL]", "").replace("[SISTEMA]", "").strip()
        
        # Si es modo general, añadir indicador
        if es_general:
            print("[TOM] 🌐 Modo GENERAL activado")
        
        # 1. Obtener datos de la bitácora
        datos = obtener_todos_los_datos()
        r = datos["resumen"]
        
        print(f"[TOM] 📊 Datos obtenidos: {r['total_pedidos']} pedidos, {r['total_clientes']} clientes")
        
        # 2. Agregar pregunta al historial
        agregar_al_historial("user", pregunta_limpia)
        
        # 3. Si no hay modelo disponible, usar respuesta de fallback con datos
        if _llm is None:
            print("[TOM] ⚠️ Modelo no disponible, usando fallback")
            respuesta = generar_respuesta_fallback(pregunta_limpia, datos, es_general)
            agregar_al_historial("assistant", respuesta)
            return respuesta
        
        # 4. Construir contexto rico con datos de la bitácora
        context = construir_contexto(datos, r)
        
        # 5. Obtener historial
        historial_texto = obtener_historial_texto()
        
        # 6. Determinar si es modo general o pregunta específica
        if es_general:
            modo_instruccion = """
Estás en MODO GENERAL. El usuario puede preguntar cualquier cosa, no solo sobre los datos del sistema.
Si la pregunta es sobre temas generales (ciencia, historia, cultura, tecnología, etc.), responde con conocimiento general.
Si la pregunta es sobre el sistema o los datos de la bitácora, usa los datos proporcionados.
Sé amable, útil y completo en tus respuestas.
"""
        else:
            modo_instruccion = """
Estás en MODO SISTEMA. El usuario pregunta sobre los datos del sistema.
SOLO usa los datos de la bitácora que se te proporcionan.
NO inventes información que no esté en los datos.
Si no encuentras la información en los datos, dilo honestamente.
"""
        
        # 7. Construir prompt completo
        prompt = f"""<|im_start|>system
Eres TOM, un asistente inteligente del sistema Grupo GSN. 
Tu función es analizar los datos de la bitácora y responder preguntas del usuario de manera clara, útil y precisa.

REGLAS IMPORTANTES:
1. Para preguntas sobre el sistema, SOLO usa los datos que se te proporcionan en el contexto.
2. NO inventes información que no esté en los datos.
3. Si no sabes algo, dilo honestamente.
4. Da respuestas completas y bien estructuradas.
5. Usa formato amigable con emojis para hacer la respuesta más clara.
6. SIEMPRE incluye números y estadísticas precisas de los datos cuando sea relevante.
7. Mantén consistencia con lo que has respondido anteriormente.

{modo_instruccion}

{historial_texto}

CONTEXTO DE DATOS DE LA BITÁCORA:
{context}

Pregunta del usuario: {pregunta_limpia}

Responde de forma clara, útil y coherente:<|im_end|>
<|im_start|>assistant\n"""
        
        print(f"[TOM] 🔮 Generando respuesta con modelo...")
        
        # 8. Generar respuesta con el modelo
        output = _llm(prompt, max_tokens=1024, temperature=0.3, stop=["<|im_end|>", "<|im_start|>"])
        
        if output and 'choices' in output:
            respuesta = output['choices'][0]['text'].strip()
            # Limpiar artefactos
            respuesta = re.sub(r'<\|.*?\|>', '', respuesta)
            respuesta = re.sub(r'\s+', ' ', respuesta).strip()
            if respuesta and len(respuesta) > 5:
                print(f"[TOM] ✅ Respuesta generada por modelo ({len(respuesta)} caracteres)")
                agregar_al_historial("assistant", respuesta)
                return respuesta
            else:
                print(f"[TOM] ⚠️ Respuesta vacía o muy corta: '{respuesta}'")
        
        # 9. Fallback: respuesta con datos
        print("[TOM] ⚠️ Usando fallback por respuesta vacía del modelo")
        respuesta = generar_respuesta_fallback(pregunta_limpia, datos, es_general)
        agregar_al_historial("assistant", respuesta)
        return respuesta
        
    except Exception as e:
        print(f"[TOM] ❌ Error crítico: {e}")
        traceback.print_exc()
        respuesta = "Lo siento, ocurrió un error al procesar tu pregunta. Por favor, intenta de nuevo."
        agregar_al_historial("assistant", respuesta)
        return respuesta

def construir_contexto(datos, r):
    """Construye un contexto rico con todos los datos de la bitácora"""
    
    context_parts = []
    
    # ===== RESUMEN GENERAL =====
    context_parts.append(f"""
=== RESUMEN GENERAL ===
• Total de pedidos: {r['total_pedidos']}
• Galones totales: {r['total_galones']:,.0f}
• Ventas totales: C$ {r['total_ventas']:,.2f}
• Facturado total: C$ {r['total_facturado']:,.2f}
• Clientes: {r['total_clientes']}
• Conductores: {r['total_conductores']}
• Camiones: {r['total_camiones']}
• Facturas: {r['total_facturas']}
• Reportes: {r['total_reportes']}
• Costos registrados: {r['total_costos']}
• Clientes con crédito: {r['clientes_con_credito']}
• Crédito total: C$ {r['credito_total']:,.2f}

=== ESTADO DE PEDIDOS ===
• Pendientes: {r['pedidos_pendientes']}
• En camino: {r['pedidos_camino']}
• Entregados: {r['pedidos_entregados']}
• Galones entregados: {r['galones_entregados']:,.0f}
• Ventas entregadas: C$ {r['ventas_entregadas']:,.2f}
""")
    
    # ===== COMBUSTIBLE =====
    if r['combustible_stats']:
        comb_str = "\n".join([f"• {tipo}: {gal:,.0f} galones" for tipo, gal in r['combustible_stats'].items()])
        context_parts.append(f"""
=== COMBUSTIBLE ===
{comb_str}
""")
    
    # ===== TOP CLIENTES =====
    if r['top_clientes']:
        top_str = "\n".join([f"• {c['nombre']}: C$ {c['total']:,.2f} ({c['pedidos']} pedidos)" for c in r['top_clientes'][:5]])
        context_parts.append(f"""
=== TOP 5 CLIENTES ===
{top_str}
""")
    
    # ===== LISTA DE CLIENTES =====
    if datos['empresas']:
        clientes_str = "\n".join([f"• {e.get('nombre', 'Sin nombre')} (ID: {e.get('id', '')}) - Crédito: C$ {e.get('credito', 0):,.2f}" for e in datos['empresas'][:15]])
        if len(datos['empresas']) > 15:
            clientes_str += f"\n• ... y {len(datos['empresas']) - 15} clientes más"
        context_parts.append(f"""
=== CLIENTES REGISTRADOS ===
{clientes_str}
""")
    
    # ===== PEDIDOS RECIENTES =====
    todos_pedidos = datos['pedidos'] + datos['pedidos_camino'] + datos['pedidos_entregados']
    if todos_pedidos:
        # Ordenar por fecha (si existe)
        try:
            pedidos_ordenados = sorted([p for p in todos_pedidos if p], key=lambda x: x.get('fecha', ''), reverse=True)[:8]
        except:
            pedidos_ordenados = [p for p in todos_pedidos if p][:8]
        
        if pedidos_ordenados:
            pedidos_str = "\n".join([
                f"• {p.get('nombre', p.get('Cliente', 'Desconocido'))}: {p.get('galones', 0)} galones, C$ {p.get('total', p.get('costo_total', 0)):,.2f} - Estado: {p.get('estado', p.get('estado_operacion', 'N/A'))}"
                for p in pedidos_ordenados if p
            ])
            context_parts.append(f"""
=== PEDIDOS RECIENTES ===
{pedidos_str}
""")
    
    # ===== CONDUCTORES =====
    if datos['conductores']:
        cond_str = "\n".join([f"• {c.get('nombre', 'Sin nombre')}" for c in datos['conductores'][:10]])
        context_parts.append(f"""
=== CONDUCTORES ===
{cond_str}
""")
    
    # ===== CAMIONES =====
    if datos['camiones']:
        cam_str = "\n".join([f"• {c.get('placa', 'Sin placa')} - {c.get('tipo', 'Sin tipo')}" for c in datos['camiones'][:10]])
        context_parts.append(f"""
=== CAMIONES ===
{cam_str}
""")
    
    # ===== FACTURAS RECIENTES =====
    if datos['facturas']:
        try:
            facturas_ordenadas = sorted([f for f in datos['facturas'] if f], key=lambda x: x.get('fecha_emision', x.get('fecha', '')), reverse=True)[:5]
        except:
            facturas_ordenadas = [f for f in datos['facturas'] if f][:5]
        
        if facturas_ordenadas:
            fact_str = "\n".join([
                f"• {f.get('id', '').split('-')[0] if f.get('id') else 'N/A'}: C$ {f.get('total', 0):,.2f}"
                for f in facturas_ordenadas if f
            ])
            context_parts.append(f"""
=== FACTURAS RECIENTES ===
{fact_str}
""")
    
    # ===== INFORMACIÓN ADICIONAL =====
    # Fecha actual
    context_parts.append(f"""
=== INFORMACIÓN ADICIONAL ===
• Fecha actual: {datetime.now().strftime('%d/%m/%Y %H:%M')}
• Total de registros en bitácora: {len(datos['empresas']) + len(datos['pedidos']) + len(datos['pedidos_camino']) + len(datos['pedidos_entregados']) + len(datos['conductores']) + len(datos['camiones'])}
""")
    
    return "\n".join(context_parts)

def generar_respuesta_fallback(pregunta: str, datos, es_general=False) -> str:
    """Genera una respuesta de fallback usando los datos de la bitácora sin modelo"""
    r = datos["resumen"]
    pl = pregunta.lower().strip()
    
    print(f"[TOM] 📋 Generando respuesta fallback para: {pl[:30]}...")
    
    # Si es modo general y no es una pregunta sobre el sistema
    if es_general:
        # Verificar si la pregunta es sobre el sistema
        palabras_sistema = ['pedido', 'venta', 'cliente', 'empresa', 'conductor', 'camion', 'combustible', 'galon', 'factura', 'credito', 'bitacora']
        if not any(p in pl for p in palabras_sistema):
            return f"""🌐 **Modo General - TOM**

Hola, soy TOM. Puedo ayudarte con información sobre el sistema Grupo GSN.

📊 **Datos actuales del sistema:**
• {r['total_pedidos']} pedidos totales
• {r['total_clientes']} clientes registrados
• {r['total_conductores']} conductores
• {r['total_camiones']} camiones
• Ventas: C$ {r['total_ventas']:,.2f}

💬 **Preguntas que puedo responder:**
• ¿Cuántos pedidos hay?
• ¿Cuántos clientes tenemos?
• Estado de los pedidos
• Ventas y facturación
• Información de conductores y camiones
• Estadísticas de combustible

¿Qué te gustaría saber?"""
    
    # Preguntas específicas del sistema
    if any(p in pl for p in ['resumen', 'general', 'cómo va', 'como va', 'estado']):
        return f"""📊 **Resumen General del Sistema (desde Bitácora)**

📌 **Pedidos:**
• Total: {r['total_pedidos']}
• Pendientes: {r['pedidos_pendientes']}
• En camino: {r['pedidos_camino']}
• Entregados: {r['pedidos_entregados']}

💰 **Ventas:**
• Total: C$ {r['total_ventas']:,.2f}
• Facturado: C$ {r['total_facturado']:,.2f}
• Galones: {r['total_galones']:,.0f}
• Ventas entregadas: C$ {r['ventas_entregadas']:,.2f}

🏢 **Clientes: {r['total_clientes']}** (con crédito: {r['clientes_con_credito']})
🚛 **Conductores: {r['total_conductores']}**
🚚 **Camiones: {r['total_camiones']}**
📄 **Facturas: {r['total_facturas']}**
📋 **Reportes: {r['total_reportes']}**

⛽ **Combustible:**
{chr(10).join([f'• {tipo}: {gal:,.0f} gal' for tipo, gal in r['combustible_stats'].items()]) if r['combustible_stats'] else '• No hay datos de combustible'}

🏆 **Top Clientes:**
{chr(10).join([f'• {c["nombre"]}: C$ {c["total"]:,.2f} ({c["pedidos"]} pedidos)' for c in r['top_clientes'][:3]]) if r['top_clientes'] else '• No hay clientes registrados'}"""
    
    if any(p in pl for p in ['entregados', 'entregado', 'cuántos entregados', 'cuantos entregados']):
        pct = (r['pedidos_entregados'] / r['total_pedidos'] * 100) if r['total_pedidos'] > 0 else 0
        return f"""📦 **Pedidos Entregados: {r['pedidos_entregados']}**

• Total de pedidos: {r['total_pedidos']}
• En camino: {r['pedidos_camino']}
• Pendientes: {r['pedidos_pendientes']}

✅ **Entregados: {r['pedidos_entregados']}** ({pct:.1f}% del total)

💰 **Ventas entregadas: C$ {r['ventas_entregadas']:,.2f}**
⛽ **Galones entregados: {r['galones_entregados']:,.0f}**

🏆 **Top cliente en entregas:**
{chr(10).join([f'• {c["nombre"]}: C$ {c["total"]:,.2f}' for c in r['top_clientes'][:3]]) if r['top_clientes'] else '• No hay clientes registrados'}"""
    
    if any(p in pl for p in ['clientes', 'empresas', 'cuántos clientes', 'cuantos clientes']):
        return f"""🏢 **Clientes Registrados: {r['total_clientes']}**

📋 **Lista de clientes:**
{chr(10).join([f'• {e.get("nombre", "Sin nombre")} (Crédito: C$ {e.get("credito", 0):,.2f})' for e in datos["empresas"][:15]])}
{chr(10).join([f'• ... y {len(datos["empresas"]) - 15} más' if len(datos["empresas"]) > 15 else ""]) if len(datos["empresas"]) > 15 else ""}

💳 **Clientes con crédito: {r['clientes_con_credito']}**
💰 **Crédito total: C$ {r['credito_total']:,.2f}**"""
    
    if any(p in pl for p in ['conductores', 'cuántos conductores', 'cuantos conductores']):
        return f"🚛 **Conductores registrados: {r['total_conductores']}**\n\n📋 Lista de conductores:\n{chr(10).join([f'• {c.get("nombre", "Sin nombre")}' for c in datos["conductores"]]) if datos['conductores'] else '• No hay conductores registrados'}"
    
    if any(p in pl for p in ['camiones', 'cuántos camiones', 'cuantos camiones']):
        return f"🚚 **Camiones registrados: {r['total_camiones']}**\n\n📋 Lista de camiones:\n{chr(10).join([f'• {c.get("placa", "Sin placa")} - {c.get("tipo", "Sin tipo")}' for c in datos["camiones"]]) if datos['camiones'] else '• No hay camiones registrados'}"
    
    if any(p in pl for p in ['ventas', 'vendido', 'facturado', 'monto']):
        return f"""💰 **Resumen de Ventas:**

• Ventas totales: **C$ {r['total_ventas']:,.2f}**
• Facturado total: **C$ {r['total_facturado']:,.2f}**
• Galones vendidos: **{r['total_galones']:,.0f}**
• Ventas entregadas: **C$ {r['ventas_entregadas']:,.2f}**

📋 **Top 3 clientes por compras:**
{chr(10).join([f'• {c["nombre"]}: C$ {c["total"]:,.2f} ({c["pedidos"]} pedidos)' for c in r["top_clientes"][:3]]) if r['top_clientes'] else '• No hay clientes registrados'}"""
    
    if any(p in pl for p in ['credito', 'crédito', 'clientes con credito']):
        clientes_credito = [e for e in datos["empresas"] if e.get('credito', 0) > 0]
        return f"""💳 **Clientes con Crédito: {len(clientes_credito)}**

💰 **Crédito total: C$ {r['credito_total']:,.2f}**

📋 **Lista de clientes con crédito:**
{chr(10).join([f'• {e.get("nombre", "Sin nombre")}: C$ {e.get("credito", 0):,.2f}' for e in clientes_credito[:15]]) if clientes_credito else '• No hay clientes con crédito'}

🔹 **Límite de crédito total: C$ {sum(e.get('limite_credito', 0) for e in clientes_credito):,.2f}**"""
    
    # Pregunta genérica - mostrar resumen
    return f"""📊 **Datos del sistema Grupo GSN (desde Bitácora)**

📌 **Resumen:**
• Pedidos totales: {r['total_pedidos']}
• Galones: {r['total_galones']:,.0f}
• Ventas: C$ {r['total_ventas']:,.2f}
• Clientes: {r['total_clientes']}
• Conductores: {r['total_conductores']}
• Camiones: {r['total_camiones']}
• Facturas: {r['total_facturas']}

📋 **Estados:**
• Pendientes: {r['pedidos_pendientes']}
• En camino: {r['pedidos_camino']}
• Entregados: {r['pedidos_entregados']}

⛽ **Combustible:**
{chr(10).join([f'• {tipo}: {gal:,.0f} gal' for tipo, gal in r['combustible_stats'].items()]) if r['combustible_stats'] else '• No hay datos de combustible'}

🏆 **Top 3 Clientes:**
{chr(10).join([f'• {c["nombre"]}: C$ {c["total"]:,.2f}' for c in r["top_clientes"][:3]]) if r['top_clientes'] else '• No hay clientes registrados'}"""

# ==================== API ENDPOINTS ====================

def api_tom_preguntar():
    try:
        data = request.get_json()
        pregunta = data.get('pregunta', '').strip()
        if not pregunta:
            return jsonify({"ok": False, "error": "Pregunta vacía"})
        
        print(f"[TOM] 📝 Recibido: {pregunta[:80]}...")
        respuesta = generar_respuesta(pregunta)
        print(f"[TOM] ✅ Enviando respuesta ({len(respuesta)} caracteres)")
        
        return jsonify({"ok": True, "respuesta": respuesta})
    except Exception as e:
        print(f"[TOM] ❌ Error en API: {e}")
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})

def api_tom_clear_history():
    """Limpia el historial de conversación"""
    global historial_conversacion
    historial_conversacion.clear()
    return jsonify({"ok": True, "mensaje": "Historial limpiado"})

def api_tom_resumen():
    datos = obtener_todos_los_datos()
    return jsonify(datos["resumen"])

def api_tom_dashboard():
    datos = obtener_todos_los_datos()
    r = datos["resumen"]
    return jsonify({
        "total_pedidos": r['total_pedidos'],
        "total_ventas": r['total_ventas'],
        "total_galones": r['total_galones'],
        "total_clientes": r['total_clientes'],
        "total_conductores": r['total_conductores'],
        "total_camiones": r['total_camiones'],
        "total_facturas": r['total_facturas'],
        "pedidos_pendientes": r['pedidos_pendientes'],
        "pedidos_camino": r['pedidos_camino'],
        "pedidos_entregados": r['pedidos_entregados'],
        "clientes_con_credito": r['clientes_con_credito'],
        "credito_total": r['credito_total'],
        "fuente": "bitacora_data.json"
    })

def api_tom_clientes():
    datos = obtener_todos_los_datos()
    return jsonify({"total": len(datos["empresas"]), "clientes": datos["empresas"]})

def api_tom_empresas():
    datos = obtener_todos_los_datos()
    return jsonify({"total": len(datos["empresas"]), "empresas": datos["empresas"]})

def api_tom_empresa(empresa_id):
    datos = obtener_todos_los_datos()
    empresa = None
    for c in datos["empresas"]:
        if str(c.get("id")) == str(empresa_id):
            empresa = c
            break
    if not empresa:
        return jsonify({"ok": False, "error": "Cliente no encontrado"}), 404
    return jsonify({"ok": True, "empresa": empresa})

def api_tom_pedidos():
    datos = obtener_todos_los_datos()
    limit = request.args.get('limit', 50, type=int)
    todos_pedidos = datos['pedidos'] + datos['pedidos_camino'] + datos['pedidos_entregados']
    try:
        pedidos_ordenados = sorted([p for p in todos_pedidos if p], key=lambda x: x.get('fecha', ''), reverse=True)
    except:
        pedidos_ordenados = [p for p in todos_pedidos if p]
    return jsonify({"total": len(pedidos_ordenados), "pedidos": pedidos_ordenados[:limit]})

def api_tom_facturas():
    datos = obtener_todos_los_datos()
    facturas = sorted([f for f in datos["facturas"] if f], key=lambda x: x.get('fecha_emision', ''), reverse=True)
    return jsonify({
        "total_facturas": len(facturas),
        "total_facturado": datos["resumen"]["total_facturado"],
        "facturas": facturas[:100]
    })

def api_tom_estadisticas():
    datos = obtener_todos_los_datos()
    r = datos["resumen"]
    return jsonify({
        "combustibles": r['combustible_stats'],
        "flota": {
            "total_conductores": r['total_conductores'],
            "total_camiones": r['total_camiones']
        },
        "total_clientes": r['total_clientes'],
        "top_clientes": r['top_clientes'],
        "entregados": {
            "total": r['pedidos_entregados'],
            "galones": r['galones_entregados'],
            "ventas": r['ventas_entregadas']
        },
        "credito": {
            "clientes_con_credito": r['clientes_con_credito'],
            "credito_total": r['credito_total']
        },
        "fuente": "bitacora_data.json"
    })

def api_tom_conductores():
    datos = obtener_todos_los_datos()
    return jsonify({"total": len(datos["conductores"]), "conductores": datos["conductores"]})

def api_tom_camiones():
    datos = obtener_todos_los_datos()
    return jsonify({"total": len(datos["camiones"]), "camiones": datos["camiones"]})

def api_tom_buscar():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({"ok": True, "resultados": []})
    
    resultados = []
    datos = obtener_todos_los_datos()
    for c in datos["empresas"]:
        if query.lower() in c.get("nombre", "").lower():
            resultados.append({"tipo": "cliente", "id": c.get("id"), "nombre": c.get("nombre")})
    return jsonify({"ok": True, "resultados": resultados[:20]})

def api_tom_costos_traslado():
    datos = obtener_todos_los_datos()
    return jsonify({"ok": True, "costos": datos.get("costos", [])})

def api_tom_bitacora():
    """Obtiene todos los datos de la bitácora"""
    datos = obtener_todos_los_datos()
    return jsonify({"ok": True, "datos": datos["bitacora"]})

def api_tom_usuarios():
    """Obtiene la lista de usuarios (sin contraseñas)"""
    try:
        usuarios_path = os.path.join(DATOS_DIR, "usuarios.json")
        if os.path.exists(usuarios_path):
            with open(usuarios_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                usuarios = data.get('usuarios', [])
                for u in usuarios:
                    u.pop('password', None)
                    u.pop('clave', None)
                return jsonify({"ok": True, "usuarios": usuarios})
        else:
            return jsonify({"ok": True, "usuarios": [
                {"id": "admin", "nombre": "Administrador", "email": "admin@gruposn.com", "rol": "admin"},
                {"id": "user", "nombre": "Usuario", "email": "user@gruposn.com", "rol": "user"}
            ]})
    except Exception as e:
        print(f"[TOM] Error en api_tom_usuarios: {e}")
        return jsonify({"ok": False, "error": str(e)})

def api_tom_sistema_archivos():
    archivos = []
    if os.path.exists(DATOS_DIR):
        for archivo in os.listdir(DATOS_DIR):
            if archivo.endswith('.json'):
                archivos.append({"nombre": archivo})
    return jsonify({"ok": True, "archivos": archivos, "ruta": DATOS_DIR})

def api_tom_sistema_leer():
    archivo = request.args.get('archivo', '')
    ruta = os.path.join(DATOS_DIR, archivo)
    if os.path.exists(ruta) and archivo.endswith('.json'):
        with open(ruta, 'r', encoding='utf-8') as f:
            return jsonify({"ok": True, "contenido": f.read()})
    return jsonify({"ok": False, "error": "Archivo no encontrado"})

def api_tom_sistema_buscar():
    return jsonify({"ok": True, "resultados": []})

def api_tom_sistema_estructura():
    return jsonify({
        "ok": True,
        "estructura": {
            "datos_existe": os.path.exists(DATOS_DIR),
            "ruta": DATOS_DIR,
            "archivos_json": [f for f in os.listdir(DATOS_DIR) if f.endswith('.json')] if os.path.exists(DATOS_DIR) else []
        }
    })

def api_tom_soporte():
    return jsonify({"ok": True, "respuesta": "TOM funcionando correctamente con datos de bitacora_data.json"})

def api_tom_hablar():
    return jsonify({"ok": True})

# ==================== INICIO ====================
print("[TOM] ✅ Módulo cargado correctamente!")
print(f"[TOM] 🤖 IA: {'Activada' if _llm is not None else 'Desactivada'}")
print(f"[TOM] 📦 Modelo: {os.path.basename(MODELO) if os.path.exists(MODELO) else 'No disponible'}")
print(f"[TOM] 📁 Bitácora en: {BITACORA_PATH if os.path.exists(BITACORA_PATH) else 'No encontrada'}")
print(f"[TOM] 📁 Fallback en: {TABLAS_EDITABLES_PATH if os.path.exists(TABLAS_EDITABLES_PATH) else 'No encontrada'}")
print(f"[TOM] 📊 Fuente de datos: bitacora_data.json")
print(f"[TOM] 💬 Historial: {HISTORIAL_MAX} mensajes")