# ==================== MÓDULO CREAR ID ====================
import random
import string
from flask import jsonify, request
import random
import string
from flask import jsonify, request

def api_crear_empresa_personalizada():
    from main import crear_empresa
    try:
        d = request.get_json()
        emp = crear_empresa(
            d.get('nombre', ''), d.get('contacto', ''), d.get('cedula', ''),
            d.get('telefono', ''), d.get('direccion', ''), d.get('tipo', 'Cliente'),
            d.get('id', None), d.get('placa', ''), d.get('email', '')
        )
        return jsonify({"ok": True, "empresa": emp}) if emp else jsonify({"ok": False, "error": "ID existe"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def api_generar_id_sugerido():
    tipo = request.args.get('tipo', 'Cliente')
    nombre = request.args.get('nombre', '')
    prefijos = {'Cliente': 'CLI', 'Proveedor': 'PRO'}
    prefijo = prefijos.get(tipo, 'EMP')
    iniciales = nombre[:3].upper() if nombre else 'XXX'
    numero = random.randint(100, 999)
    id_sugerido = f"{prefijo}-{iniciales}{numero}"
    return jsonify({"id": id_sugerido})