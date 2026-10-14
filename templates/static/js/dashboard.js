// ==================== VARIABLES GLOBALES ====================
console.log("🚀 Dashboard cargando...");

let publicUrl = '';
let sidebarCollapsed = false;
let reportePeriodoActual = "todos";
let pedidosData = [];
let pedidosFacturar = [];
let pedidoSeleccionado = null;
let paginasLista = [];
let elementosEditorGlobal = [];
let paginaEditandoId = null;
let camionEstadoActual = null;

// Variables para tablas editables
let tablaPedidosData = [];
let tablaEmpresasData = [];
let tablaCostosData = [];
let tablaConductoresData = [];
let tablaCamionesData = [];
let columnasPedidos = ['ID', 'Empresa', 'Fecha', 'Tipo', 'Galones', 'Total'];
let columnasEmpresas = ['ID', 'Nombre', 'Contacto', 'Teléfono', 'Email', 'Tipo'];
let columnasCostos = ['Empresa ID', 'Precio/Galón', 'Distancia (km)', 'Costo/km', 'Traslado'];
let columnasConductores = ['ID', 'Nombre', 'Cédula', 'Licencia', 'Teléfono', 'Dirección'];
let columnasCamiones = ['ID', 'Placa', 'Marca', 'Modelo', 'Capacidad', 'Estado'];

// Gráficas
let costosLineChart, combustiblePieChart, reporteLineChart, reporteBarChart, estadoCamionesChart, funcionCrecimientoChart, rutaPieChart;

// ==================== SIDEBAR TOGGLE ====================
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    sidebarCollapsed = !sidebarCollapsed;
    if (sidebarCollapsed) {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('expanded');
    } else {
        sidebar.classList.remove('collapsed');
        mainContent.classList.remove('expanded');
    }
}

// ==================== UTILIDADES ====================
function mostrarToast(mensaje) {
    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.innerHTML = mensaje;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function copiarTexto(texto) {
    navigator.clipboard.writeText(texto);
    mostrarToast('Copiado: ' + texto);
}

function escapeHtml(s) { 
    if(!s) return ''; 
    return s.replace(/[&<>]/g, function(m) { return m=='&'?'&amp;':m=='<'?'&lt;':'&gt;'; }); 
}

function cerrarModalPedido() { 
    var modal = document.getElementById('modalPedidoManual');
    if(modal) modal.style.display = 'none'; 
}
function cerrarModalConductor() { 
    var modal = document.getElementById('modalConductor');
    if(modal) modal.style.display = 'none'; 
}
function cerrarModalCamion() { 
    var modal = document.getElementById('modalCamion');
    if(modal) modal.style.display = 'none'; 
}
function cerrarModalEstadoCamion() { 
    var modal = document.getElementById('modalEstadoCamion');
    if(modal) modal.style.display = 'none'; 
}

// ==================== FUNCIONES PRINCIPALES ====================
async function obtenerPublicUrl() {
    try {
        const response = await fetch('/api/ngrok_url');
        const data = await response.json();
        if (data.url && data.url !== "") {
            publicUrl = data.url;
        } else {
            publicUrl = window.location.origin;
        }
    } catch(e) {
        publicUrl = window.location.origin;
    }
    const urlDisplay = document.getElementById('urlDisplay');
    if (urlDisplay) urlDisplay.innerHTML = publicUrl;
    return publicUrl;
}

async function cargarPedidosTarjetas() {
    try {
        const r = await fetch('/api/pedidos_combustible');
        const res = (await r.json()).pedidos || [];
        const totalCosto = res.reduce(function(s,v) { return s + (v.costo_total||0); }, 0);
        const totalGalones = res.reduce(function(s,v) { return s + (v.galones||0); }, 0);
        
        var totalPedidosEl = document.getElementById('totalPedidos');
        var totalCostoEl = document.getElementById('totalCosto');
        var totalGalonesEl = document.getElementById('totalGalonesRecepcion');
        var promedioEl = document.getElementById('promedioPedido');
        
        if(totalPedidosEl) totalPedidosEl.innerText = res.length;
        if(totalCostoEl) totalCostoEl.innerText = 'C$' + totalCosto.toLocaleString();
        if(totalGalonesEl) totalGalonesEl.innerText = totalGalones.toFixed(2);
        if(promedioEl) promedioEl.innerText = res.length ? 'C$' + (totalCosto/res.length).toFixed(2) : 'C$0';
        
        const container = document.getElementById('pedidosTarjetas');
        if (container && res.length) {
            let html = '';
            for (var i = 0; i < Math.min(res.length, 20); i++) {
                var v = res[i];
                var fecha = new Date(v.fecha);
                var esHoy = fecha.toLocaleDateString() === new Date().toLocaleDateString();
                var estadoTexto = v.facturado ? '✓ FACTURADO' : '📋 ACTIVO';
                var estadoColor = v.facturado ? '#10b981' : '#f59e0b';
                html += '<div class="pedido-card ' + (v.facturado ? 'facturado' : '') + '" onclick="copiarTexto(\'' + v.id + '\')">' +
                    '<div class="pedido-header">' +
                        '<span class="pedido-empresa"><i class="fas fa-building"></i> ' + escapeHtml(v.nombre || v.empresa_nombre || 'Cliente') + '</span>' +
                        '<span style="background: ' + estadoColor + '20; color: ' + estadoColor + '; padding:4px 12px; border-radius:20px; font-size:11px;">' + estadoTexto + '</span>' +
                    '</div>' +
                    '<div style="margin-bottom:10px;">' +
                        '<div><span style="color:#888;">Ruta:</span> ' + escapeHtml(v.origen) + ' → ' + escapeHtml(v.destino) + '</div>' +
                        '<div><span style="color:#888;">Combustible:</span> ' + escapeHtml(v.tipo_combustible) + '</div>' +
                        '<div><span style="color:#888;">Cantidad:</span> ' + v.galones + ' gal @ C$' + v.precio_por_galon + '</div>' +
                    '</div>' +
                    '<div class="pedido-valor">Total: C$' + (v.costo_total || 0).toLocaleString() + '</div>' +
                    '<div style="font-size:11px; color:#666; margin-top:10px;"><i class="far fa-calendar-alt"></i> ' + fecha.toLocaleDateString() + (esHoy ? ' 📌 Hoy' : '') + '</div>' +
                '</div>';
            }
            container.innerHTML = html;
        } else if(container) {
            container.innerHTML = '<div class="empty-state">📭 No hay pedidos registrados</div>';
        }
    } catch(e) { 
        console.error(e); 
        var container = document.getElementById('pedidosTarjetas');
        if(container) container.innerHTML = '<div class="empty-state">❌ Error cargando datos</div>';
    }
}

async function cargarGraficas() {
    console.log("Cargando gráficas...");
    try {
        const r = await fetch('/api/pedidos_combustible');
        const pedidos = (await r.json()).pedidos || [];
        const costosPorMes = [0,0,0,0,0,0,0,0,0,0,0,0];
        const tipos = {};
        for(var i = 0; i < pedidos.length; i++) {
            var p = pedidos[i];
            try{
                var mes = new Date(p.fecha).getMonth();
                costosPorMes[mes] += (p.costo_total||0);
                var tipo = p.tipo_combustible || 'Otro';
                tipos[tipo] = (tipos[tipo]||0) + (p.costo_total||0);
            } catch(e){}
        }
        
        var ctx1 = document.getElementById('costosLineChart');
        if(ctx1 && costosLineChart) costosLineChart.destroy();
        if(ctx1) {
            costosLineChart = new Chart(ctx1, {
                type:'line',
                data:{labels:['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'], datasets:[{label:'Costo (C$)', data:costosPorMes, borderColor:'#f59e0b', backgroundColor:'rgba(245,158,11,0.1)', borderWidth:3, pointBackgroundColor:'#f59e0b', pointBorderColor:'#fff', pointRadius:4, pointHoverRadius:6, tension:0.3, fill:true}]},
                options:{responsive:true, maintainAspectRatio:true, plugins:{legend:{labels:{color:'#fff',font:{size:11}}}, tooltip:{backgroundColor:'#1a1a2e',titleColor:'#f59e0b',bodyColor:'#fff'}}, scales:{y:{grid:{color:'rgba(255,255,255,0.05)'},ticks:{color:'#aaa'}}, x:{grid:{display:false},ticks:{color:'#aaa'}}}
            });
        }
        
        var ctx2 = document.getElementById('combustiblePieChart');
        if(ctx2 && combustiblePieChart) combustiblePieChart.destroy();
        if(ctx2) {
            combustiblePieChart = new Chart(ctx2, {
                type:'pie',
                data:{labels:Object.keys(tipos), datasets:[{data:Object.values(tipos), backgroundColor:['#f59e0b','#10b981','#8b5cf6','#ef4444','#06b6d4','#ec4899'], borderWidth:0, hoverOffset:10}]},
                options:{responsive:true, maintainAspectRatio:true, plugins:{legend:{position:'right',labels:{color:'#fff',font:{size:11}}}, tooltip:{callbacks:{label:function(ctx) { return ctx.label + ': C$' + ctx.raw.toLocaleString(); }}}}
            });
        }
    } catch(e){ console.error(e); }
}

async function cargarEstadisticas() {
    try {
        const r = await fetch('/api/estadisticas');
        const d = await r.json();
        var totalEmpresas = document.getElementById('totalEmpresas');
        if(totalEmpresas) totalEmpresas.innerText = d.total_empresas || 0;
    } catch(e) {}
}

async function cargarEmpresasSelect() {
    try {
        const r = await fetch('/api/empresas_activas');
        const d = await r.json();
        var select = document.getElementById('empresaSelect');
        if(select) {
            select.innerHTML = '<option>Seleccionar Empresa</option>';
            for(var i = 0; i < (d.empresas||[]).length; i++) {
                var e = d.empresas[i];
                select.innerHTML += '<option value="' + e.id + '">' + e.nombre + '</option>';
            }
        }
        var selectFacturar = document.getElementById('selectEmpresaFacturar');
        if(selectFacturar) {
            selectFacturar.innerHTML = '<option value="">Todas las empresas</option>';
            for(var j = 0; j < (d.empresas||[]).length; j++) {
                var e2 = d.empresas[j];
                selectFacturar.innerHTML += '<option value="' + e2.id + '">' + e2.nombre + '</option>';
            }
        }
    } catch(e) { console.error(e); }
}

async function cargarPaginas() {
    try {
        const r = await fetch('/api/paginas');
        const d = await r.json();
        var paginas = d.paginas || [];
        paginasLista = paginas;
        var container = document.getElementById('paginasList');
        if(container) {
            var html = '';
            for(var i = 0; i < paginas.length; i++) {
                var p = paginas[i];
                var u = publicUrl + '/p/' + p.url_id;
                html += '<div style="background:rgba(255,255,255,0.03); border-radius:16px; padding:15px; margin-bottom:12px;">' +
                    '<div><strong><i class="fas fa-file-alt"></i> ' + p.nombre + '</strong><br><small style="color:#888;">ID: ' + p.url_id + '</small></div>' +
                    '<div style="margin-top:10px;"><button class="btn-outline btn-sm" onclick="copiarTexto(\'' + u + '\')"><i class="fas fa-copy"></i> Copiar</button><button class="btn-primary btn-sm" onclick="window.open(\'' + u + '\', \'_blank\')"><i class="fas fa-external-link-alt"></i> Abrir</button><button class="btn-danger btn-sm" onclick="eliminarPagina(\'' + p.id + '\')"><i class="fas fa-trash"></i> Eliminar</button></div>' +
                    '<div style="margin-top:10px; font-size:12px; color:#10b981; word-break:break-all;">🔗 ' + u + '</div>' +
                '</div>';
            }
            container.innerHTML = html || '<div class="empty-state">No hay páginas creadas</div>';
        }
    } catch(e) { console.error(e); }
}

async function eliminarPagina(id) {
    if(confirm('¿Eliminar esta página?')){
        await fetch('/api/eliminar_pagina',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id})});
        cargarPaginas();
    }
}

async function crearPagina() {
    var nombre = prompt('Nombre de la página:');
    if(!nombre) return;
    await fetch('/api/crear_pagina',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nombre:nombre,estilos:{},elementos:[]})});
    cargarPaginas();
    mostrarToast('Página creada');
}

async function cargarReportes(periodo) {
    reportePeriodoActual = periodo;
    try {
        const r = await fetch('/api/reportes?tipo=' + periodo);
        const data = await r.json();
        pedidosData = data.reportes || [];
        var totalCosto = 0, totalGalones = 0;
        for(var i = 0; i < pedidosData.length; i++) {
            totalCosto += pedidosData[i].costo_total || 0;
            totalGalones += pedidosData[i].galones || 0;
        }
        var precioPromedio = totalGalones > 0 ? totalCosto / totalGalones : 0;
        
        var el1 = document.getElementById('reporteTotalPedidos');
        var el2 = document.getElementById('reporteTotalCosto');
        var el3 = document.getElementById('reporteTotalGalones');
        var el4 = document.getElementById('reportePromedioGalon');
        
        if(el1) el1.innerText = pedidosData.length;
        if(el2) el2.innerText = 'C$' + totalCosto.toLocaleString();
        if(el3) el3.innerText = totalGalones.toFixed(2);
        if(el4) el4.innerText = 'C$' + precioPromedio.toFixed(2);
        
        var container = document.getElementById('pedidosLista');
        if(container && pedidosData.length) {
            var html = '<table class="pedidos-table"><thead><tr><th>Fecha</th><th>Empresa</th><th>Ruta</th><th>Combustible</th><th>Galones</th><th>Total</th></tr></thead><tbody>';
            for(var j = 0; j < Math.min(pedidosData.length, 100); j++) {
                var p = pedidosData[j];
                html += '<tr>' +
                    '<td>' + new Date(p.fecha).toLocaleDateString() + '</td>' +
                    '<td>' + escapeHtml(p.nombre) + '</td>' +
                    '<td>' + p.origen + '→' + p.destino + '</td>' +
                    '<td>' + p.tipo_combustible + '</td>' +
                    '<td>' + p.galones + '</td>' +
                    '<td class="table-valor">C$' + (p.costo_total||0).toLocaleString() + '</td>' +
                '</tr>';
            }
            html += '</tbody></table>';
            container.innerHTML = html;
        } else if(container) {
            container.innerHTML = '<div class="empty-state">No hay datos</div>';
        }
    } catch(e){ console.error(e); }
}

async function cargarPedidosFacturar() {
    try {
        var empresaId = document.getElementById('selectEmpresaFacturar') ? document.getElementById('selectEmpresaFacturar').value : '';
        const r = await fetch('/api/pedidos_combustible');
        var todos = (await r.json()).pedidos || [];
        if(empresaId) todos = todos.filter(function(v) { return v.empresa_id === empresaId; });
        pedidosFacturar = todos.filter(function(v) { return !v.facturado; });
        var container = document.getElementById('pedidosTarjetasFacturar');
        if(!container) return;
        if(pedidosFacturar.length === 0){ container.innerHTML='<div class="empty-state">Sin pedidos pendientes</div>'; return; }
        var html='';
        for(var i = 0; i < pedidosFacturar.length; i++) {
            var v = pedidosFacturar[i];
            html+='<div class="pedido-card" onclick="seleccionarPedido(\'' + v.id + '\')">' +
                '<div class="pedido-header"><span class="pedido-empresa">' + escapeHtml(v.nombre) + '</span></div>' +
                '<div>Ruta: ' + v.origen + ' → ' + v.destino + '</div>' +
                '<div>Cantidad: ' + v.galones + ' gal @ C$' + v.precio_por_galon + '</div>' +
                '<div class="pedido-valor">C$' + v.costo_total.toLocaleString() + '</div>' +
            '</div>';
        }
        container.innerHTML=html;
    } catch(e) { console.error(e); }
}

function seleccionarPedido(id){
    var v = null;
    for(var i = 0; i < pedidosFacturar.length; i++) {
        if(pedidosFacturar[i].id === id) {
            v = pedidosFacturar[i];
            break;
        }
    }
    if(!v) return;
    pedidoSeleccionado = v;
    var costoCombustible = v.galones * v.precio_por_galon;
    var costoTraslado = v.costo_traslado || 0;
    var costoTotal = costoCombustible + costoTraslado;
    var iva = costoTotal * 0.19;
    var total = costoTotal + iva;
    var container = document.getElementById('facturaEditableContainer');
    if(container) {
        container.innerHTML = '<div class="factura-header-editable"><h1 contenteditable="true">GRUPO GSN</h1><p contenteditable="true">RUC: 900.123.456-7</p><h3>' + new Date().toISOString().slice(0,10).replace(/-/g,'') + '</h3></div>' +
            '<div class="factura-body-editable">' +
                '<div style="display:flex; gap:20px; margin-bottom:25px;">' +
                    '<div style="flex:1; background:#f8f9fa; padding:15px; border-radius:8px; border-left:4px solid #f59e0b;"><strong>EMISOR</strong><br>GRUPO GSN<br>Managua, Nicaragua</div>' +
                    '<div style="flex:1; background:#f8f9fa; padding:15px; border-radius:8px; border-left:4px solid #f59e0b;"><strong>CLIENTE</strong><br><span contenteditable="true" id="clienteNombreEditable">' + escapeHtml(v.empresa_nombre||v.nombre) + '</span><br><span contenteditable="true" id="clienteNitEditable">' + escapeHtml(v.empresa_id_cliente||'') + '</span></div>' +
                '</div>' +
                '<div class="tabla-editable">' +
                    '<table><thead><tr><th>Producto</th><th>Cantidad</th><th>Precio</th><th>Total</th></tr></thead><tbody>' +
                    '<tr><td contenteditable="true">' + v.tipo_combustible + '</td><td contenteditable="true">' + v.galones + ' gal</td><td contenteditable="true">C$' + v.precio_por_galon + '</td><td contenteditable="true">C$' + costoCombustible.toLocaleString() + '</td></tr>' +
                    (costoTraslado > 0 ? '<tr><td contenteditable="true">Costo de Traslado</td><td contenteditable="true">' + (v.distancia_km || 0) + ' km</td><td contenteditable="true">C$' + (v.costo_km || 0) + '/km</td><td contenteditable="true">C$' + costoTraslado.toLocaleString() + '</td></tr>' : '') +
                    '</tbody></table>' +
                '</div>' +
                '<div style="text-align:right; margin-top:20px; padding:15px; background:#f8f9fa; border-radius:8px;">' +
                    '<p><strong>SUBTOTAL:</strong> C$' + costoTotal.toLocaleString() + '</p>' +
                    '<p><strong>IVA 19%:</strong> C$' + iva.toLocaleString() + '</p>' +
                    '<p><strong>TOTAL:</strong> <span style="color:#f59e0b;">C$' + total.toLocaleString() + '</span></p>' +
                '</div>' +
            '</div>';
    }
}

function imprimirFactura(){
    var contenido = document.getElementById('facturaEditableContainer') ? document.getElementById('facturaEditableContainer').innerHTML : '';
    if(!contenido) return;
    var ventana = window.open('','_blank');
    ventana.document.write('<html><head><title>Factura GSN</title><style>body{font-family:"Times New Roman";padding:20px;}</style></head><body>' + contenido + '<button onclick="window.print()">Imprimir</button></body></html>');
    ventana.document.close();
}

function enviarFacturaAHijo(){
    if(!pedidoSeleccionado){ mostrarToast('Seleccione un pedido primero'); return; }
    var facturaHTML = document.getElementById('facturaEditableContainer') ? document.getElementById('facturaEditableContainer').innerHTML : '';
    if(!facturaHTML) return;
    var ventana = window.open('','_blank');
    ventana.document.write('<html><head><title>Factura GSN - ' + (pedidoSeleccionado.nombre || 'Cliente') + '</title><style>body{font-family:"Times New Roman",serif;padding:40px;background:white;color:black;}@media print{body{padding:0;margin:0;}.no-print{display:none;}}.no-print{text-align:center;margin-top:20px;}.no-print button{margin:5px;padding:10px 20px;cursor:pointer;background:#f59e0b;border:none;border-radius:8px;color:white;font-weight:bold;}</style></head><body>' + facturaHTML + '<div class="no-print"><button onclick="window.print()">🖨️ Imprimir Factura</button><button onclick="window.close()">✖️ Cerrar</button></div></body></html>');
    ventana.document.close();
    mostrarToast('Factura enviada al cliente');
}

async function enviarFactura(){
    if(!pedidoSeleccionado){ mostrarToast('Seleccione pedido'); return; }
    var clienteNombre = document.getElementById('clienteNombreEditable') ? document.getElementById('clienteNombreEditable').innerText : '';
    var clienteNit = document.getElementById('clienteNitEditable') ? document.getElementById('clienteNitEditable').innerText : '';
    const r = await fetch('/api/facturar_pedidos',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
            pedidos_ids:[pedidoSeleccionado.id],
            empresa_nombre:clienteNombre,
            empresa_nit:clienteNit,
            empresa_id:pedidoSeleccionado.empresa_id,
            empresa_nombre_cliente:pedidoSeleccionado.nombre,
            email_cliente: ''
        })
    });
    const d = await r.json();
    if(d.ok){ mostrarToast('Factura generada - Total: C$' + d.total.toLocaleString()); cargarPedidosFacturar(); cargarPedidosTarjetas(); }
}

async function cargarFacturas(){
    const r = await fetch('/api/facturas_lista');
    var f = (await r.json()).facturas || [];
    var html = '';
    for(var i = 0; i < Math.min(f.length, 20); i++) {
        var fac = f[i];
        html += '<div style="background:rgba(255,255,255,0.03); border-radius:16px; padding:15px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">' +
            '<div><strong>' + fac.id + '</strong><br><small>' + fac.fecha_emision_str + '</small></div>' +
            '<div style="font-size:18px; font-weight:bold; color:#10b981;">C$' + fac.total.toLocaleString() + '</div>' +
            '<button class="btn-primary btn-sm" onclick="window.open(\'/descargar_factura/' + fac.id + '\',\'_blank\')">PDF</button>' +
        '</div>';
    }
    var container = document.getElementById('listaFacturas');
    if(container) container.innerHTML = html || '<div class="empty-state">No hay facturas</div>';
}

// ==================== TABLAS EDITABLES BÁSICAS ====================
function renderTablaPedidos() {
    var container = document.getElementById('tablaPedidosEditable');
    if (!container) return;
    var html = '<table class="editable-table"><thead><tr>';
    for(var c = 0; c < columnasPedidos.length; c++) {
        html += '<th>' + escapeHtml(columnasPedidos[c]) + '</th>';
    }
    html += '<th style="width:50px">Acciones</th></tr></thead><tbody>';
    for(var i = 0; i < tablaPedidosData.length; i++) {
        var row = tablaPedidosData[i];
        html += '<tr>';
        for(var j = 0; j < columnasPedidos.length; j++) {
            var columna = columnasPedidos[j];
            var valor = row[columna] || '';
            html += '<td contenteditable="true" onblur="actualizarCeldaPedidos(' + i + ', \'' + columna + '\', this.innerText)">' + escapeHtml(valor) + '</td>';
        }
        html += '<td><button class="btn-danger btn-sm" onclick="eliminarFilaPedidos(' + i + ')"><i class="fas fa-trash"></i></button></td>';
        html += '</tr>';
    }
    if (tablaPedidosData.length === 0) {
        html += '<tr><td colspan="' + (columnasPedidos.length + 1) + '" style="text-align:center">No hay datos. Presione "Añadir Fila" para comenzar</td></tr>';
    }
    html += '</tbody></table>';
    container.innerHTML = html;
}

function renderTablaEmpresas() {
    var container = document.getElementById('tablaEmpresasEditable');
    if (!container) return;
    var html = '<table class="editable-table"><thead><tr>';
    for(var c = 0; c < columnasEmpresas.length; c++) {
        html += '<th>' + escapeHtml(columnasEmpresas[c]) + '</th>';
    }
    html += '<th style="width:50px">Acciones</th></tr></thead><tbody>';
    for(var i = 0; i < tablaEmpresasData.length; i++) {
        var row = tablaEmpresasData[i];
        html += '<tr>';
        for(var j = 0; j < columnasEmpresas.length; j++) {
            var columna = columnasEmpresas[j];
            var valor = row[columna] || '';
            html += '<td contenteditable="true" onblur="actualizarCeldaEmpresas(' + i + ', \'' + columna + '\', this.innerText)">' + escapeHtml(valor) + '</td>';
        }
        html += '<td><button class="btn-danger btn-sm" onclick="eliminarFilaEmpresas(' + i + ')"><i class="fas fa-trash"></i></button></td>';
        html += '</tr>';
    }
    if (tablaEmpresasData.length === 0) {
        html += '<tr><td colspan="' + (columnasEmpresas.length + 1) + '" style="text-align:center">No hay datos. Presione "Añadir Fila" para comenzar</td></tr>';
    }
    html += '</tbody></table>';
    container.innerHTML = html;
}

function renderTablaCostos() {
    var container = document.getElementById('tablaCostosEditable');
    if (!container) return;
    var html = '<table class="editable-table"><thead><tr>';
    for(var c = 0; c < columnasCostos.length; c++) {
        html += '<th>' + escapeHtml(columnasCostos[c]) + '</th>';
    }
    html += '<th style="width:50px">Acciones</th></tr></thead><tbody>';
    for(var i = 0; i < tablaCostosData.length; i++) {
        var row = tablaCostosData[i];
        html += '<tr>';
        for(var j = 0; j < columnasCostos.length; j++) {
            var columna = columnasCostos[j];
            var valor = row[columna] || '';
            html += '<td contenteditable="true" onblur="actualizarCeldaCostos(' + i + ', \'' + columna + '\', this.innerText)">' + escapeHtml(valor) + '</td>';
        }
        html += '<td><button class="btn-danger btn-sm" onclick="eliminarFilaCostos(' + i + ')"><i class="fas fa-trash"></i></button></td>';
        html += '</tr>';
    }
    if (tablaCostosData.length === 0) {
        html += '<tr><td colspan="' + (columnasCostos.length + 1) + '" style="text-align:center">No hay datos. Presione "Añadir Fila" para comenzar</td></tr>';
    }
    html += '</tbody></table>';
    container.innerHTML = html;
}

function actualizarCeldaPedidos(fila, columna, valor) {
    if (tablaPedidosData[fila]) {
        tablaPedidosData[fila][columna] = valor;
        mostrarToast('Celda actualizada');
    }
}
function actualizarCeldaEmpresas(fila, columna, valor) {
    if (tablaEmpresasData[fila]) {
        tablaEmpresasData[fila][columna] = valor;
        mostrarToast('Celda actualizada');
    }
}
function actualizarCeldaCostos(fila, columna, valor) {
    if (tablaCostosData[fila]) {
        tablaCostosData[fila][columna] = valor;
        mostrarToast('Celda actualizada');
    }
}

function agregarFilaPedidos() { var nuevaFila = {}; for(var c=0; c<columnasPedidos.length; c++) nuevaFila[columnasPedidos[c]] = ''; tablaPedidosData.push(nuevaFila); renderTablaPedidos(); mostrarToast('Fila añadida'); }
function agregarFilaEmpresas() { var nuevaFila = {}; for(var c=0; c<columnasEmpresas.length; c++) nuevaFila[columnasEmpresas[c]] = ''; tablaEmpresasData.push(nuevaFila); renderTablaEmpresas(); mostrarToast('Fila añadida'); }
function agregarFilaCostos() { var nuevaFila = {}; for(var c=0; c<columnasCostos.length; c++) nuevaFila[columnasCostos[c]] = ''; tablaCostosData.push(nuevaFila); renderTablaCostos(); mostrarToast('Fila añadida'); }
function agregarColumnaPedidos() { var nombre = prompt('Nombre de la nueva columna:'); if (nombre && nombre.trim()) { columnasPedidos.push(nombre.trim()); for(var i=0;i<tablaPedidosData.length;i++) tablaPedidosData[i][nombre.trim()] = ''; renderTablaPedidos(); mostrarToast('Columna añadida'); } }
function agregarColumnaEmpresas() { var nombre = prompt('Nombre de la nueva columna:'); if (nombre && nombre.trim()) { columnasEmpresas.push(nombre.trim()); for(var i=0;i<tablaEmpresasData.length;i++) tablaEmpresasData[i][nombre.trim()] = ''; renderTablaEmpresas(); mostrarToast('Columna añadida'); } }
function agregarColumnaCostos() { var nombre = prompt('Nombre de la nueva columna:'); if (nombre && nombre.trim()) { columnasCostos.push(nombre.trim()); for(var i=0;i<tablaCostosData.length;i++) tablaCostosData[i][nombre.trim()] = ''; renderTablaCostos(); mostrarToast('Columna añadida'); } }

function eliminarFilaPedidos(idx) { tablaPedidosData.splice(idx, 1); renderTablaPedidos(); mostrarToast('Fila eliminada'); }
function eliminarFilaEmpresas(idx) { tablaEmpresasData.splice(idx, 1); renderTablaEmpresas(); mostrarToast('Fila eliminada'); }
function eliminarFilaCostos(idx) { tablaCostosData.splice(idx, 1); renderTablaCostos(); mostrarToast('Fila eliminada'); }

function exportarTablaPedidos() { var data = JSON.stringify(tablaPedidosData); var blob = new Blob([data], {type: 'application/json'}); var url = URL.createObjectURL(blob); var a = document.createElement('a'); a.href = url; a.download = 'tabla_pedidos.json'; a.click(); URL.revokeObjectURL(url); }
function exportarTablaEmpresas() { var data = JSON.stringify(tablaEmpresasData); var blob = new Blob([data], {type: 'application/json'}); var url = URL.createObjectURL(blob); var a = document.createElement('a'); a.href = url; a.download = 'tabla_empresas.json'; a.click(); URL.revokeObjectURL(url); }
function exportarTablaCostos() { var data = JSON.stringify(tablaCostosData); var blob = new Blob([data], {type: 'application/json'}); var url = URL.createObjectURL(blob); var a = document.createElement('a'); a.href = url; a.download = 'tabla_costos.json'; a.click(); URL.revokeObjectURL(url); }

function importarTablaPedidos() {
    var input = document.createElement('input'); input.type = 'file'; input.accept = 'application/json';
    input.onchange = function(e) {
        var file = e.target.files[0]; var reader = new FileReader();
        reader.onload = function(event) { try {
            tablaPedidosData = JSON.parse(event.target.result);
            renderTablaPedidos(); mostrarToast('Tabla importada');
        } catch(err) { mostrarToast('Error: ' + err.message); } };
        reader.readAsText(file);
    }; input.click();
}
function importarTablaEmpresas() {
    var input = document.createElement('input'); input.type = 'file'; input.accept = 'application/json';
    input.onchange = function(e) {
        var file = e.target.files[0]; var reader = new FileReader();
        reader.onload = function(event) { try {
            tablaEmpresasData = JSON.parse(event.target.result);
            renderTablaEmpresas(); mostrarToast('Tabla importada');
        } catch(err) { mostrarToast('Error: ' + err.message); } };
        reader.readAsText(file);
    }; input.click();
}
function importarTablaCostos() {
    var input = document.createElement('input'); input.type = 'file'; input.accept = 'application/json';
    input.onchange = function(e) {
        var file = e.target.files[0]; var reader = new FileReader();
        reader.onload = function(event) { try {
            tablaCostosData = JSON.parse(event.target.result);
            renderTablaCostos(); mostrarToast('Tabla importada');
        } catch(err) { mostrarToast('Error: ' + err.message); } };
        reader.readAsText(file);
    }; input.click();
}

function cargarDatosATablas() {
    fetch('/api/pedidos_combustible').then(function(r) { return r.json(); }).then(function(data) {
        var pedidos = data.pedidos || [];
        tablaPedidosData = [];
        for(var i = 0; i < Math.min(pedidos.length, 50); i++) {
            var p = pedidos[i];
            tablaPedidosData.push({
                'ID': p.id, 'Empresa': p.nombre || p.empresa_nombre, 'Fecha': new Date(p.fecha).toLocaleDateString(),
                'Tipo': p.tipo_combustible, 'Galones': p.galones, 'Total': 'C$' + p.costo_total
            });
        }
        renderTablaPedidos();
    }).catch(function(err) { console.error(err); });
    
    fetch('/api/empresas_activas').then(function(r) { return r.json(); }).then(function(data) {
        var empresas = data.empresas || [];
        tablaEmpresasData = [];
        for(var i = 0; i < empresas.length; i++) {
            var e = empresas[i];
            tablaEmpresasData.push({
                'ID': e.id, 'Nombre': e.nombre, 'Contacto': e.contacto || '', 'Teléfono': e.telefono || '', 'Email': e.email || '', 'Tipo': e.tipo || 'Cliente'
            });
        }
        renderTablaEmpresas();
    }).catch(function(err) { console.error(err); });
    
    fetch('/api/costos_traslado').then(function(r) { return r.json(); }).then(function(data) {
        var costos = data.costos || [];
        tablaCostosData = [];
        for(var i = 0; i < costos.length; i++) {
            var c = costos[i];
            tablaCostosData.push({
                'Empresa ID': c.empresa_id, 'Precio/Galón': 'C$' + c.precio_galon, 'Distancia (km)': c.distancia_km + ' km', 'Costo/km': 'C$' + c.costo_km, 'Traslado': 'C$' + (c.distancia_km * c.costo_km).toFixed(2)
            });
        }
        renderTablaCostos();
    }).catch(function(err) { console.error(err); });
}

// ==================== CONDUCTORES Y CAMIONES ====================
async function cargarConductores(){
    try {
        const r = await fetch('/api/conductores');
        const data = await r.json();
        var conductores = data.conductores || [];
        var html = '<table style="width:100%"><thead><tr><th>ID</th><th>Nombre</th><th>Cédula</th><th>Teléfono</th><th>Acciones</th></tr></thead><tbody>';
        for(var i = 0; i < conductores.length; i++) {
            var c = conductores[i];
            html += '<tr>' +
                '<td><code>' + c.id + '</code></td>' +
                '<td>' + c.nombre + '</td>' +
                '<td>' + (c.cedula||'-') + '</td>' +
                '<td>' + (c.telefono||'-') + '</td>' +
                '<td><button class="btn-outline btn-sm" onclick="eliminarConductor(\'' + c.id + '\')">Eliminar</button></td>' +
            '</tr>';
        }
        html += '</tbody></table>';
        var lista = document.getElementById('conductoresLista');
        if(lista) lista.innerHTML = html;
        var select = document.getElementById('camionConductor');
        if(select) {
            select.innerHTML = '<option>Sin conductor</option>';
            for(var j = 0; j < conductores.length; j++) {
                select.innerHTML += '<option value="' + conductores[j].nombre + '">' + conductores[j].nombre + '</option>';
            }
        }
    } catch(e) { console.error(e); }
}

async function cargarCamiones(){
    try {
        const r = await fetch('/api/camiones');
        const data = await r.json();
        var camiones = data.camiones || [];
        var html = '<table style="width:100%"><thead><tr><th>ID</th><th>Placa</th><th>Modelo</th><th>Conductor</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>';
        for(var i = 0; i < camiones.length; i++) {
            var c = camiones[i];
            var color = c.estado === 'Disponible' ? '#10b981' : (c.estado === 'En Ruta' ? '#f59e0b' : '#ef4444');
            html += '<tr>' +
                '<td><code>' + c.id + '</code></td>' +
                '<td>' + c.placa + '</td>' +
                '<td>' + c.marca + ' ' + c.modelo + '</td>' +
                '<td>' + (c.conductor_asignado||'-') + '</td>' +
                '<td style="color:' + color + ';">' + c.estado + '</td>' +
                '<td><button class="btn-primary btn-sm" onclick="abrirModalEstado(\'' + c.id + '\',\'' + c.placa + '\',\'' + c.estado + '\')">Estado</button><button class="btn-outline btn-sm" onclick="eliminarCamion(\'' + c.id + '\')">Eliminar</button></td>' +
            '</tr>';
        }
        html += '</tbody><table>';
        var lista = document.getElementById('camionesLista');
        if(lista) lista.innerHTML = html;
        
        var disponibles = 0, enRuta = 0, mantenimiento = 0;
        for(var j = 0; j < camiones.length; j++) {
            if(camiones[j].estado === 'Disponible') disponibles++;
            else if(camiones[j].estado === 'En Ruta') enRuta++;
            else if(camiones[j].estado === 'Mantenimiento') mantenimiento++;
        }
        var dispEl = document.getElementById('estadoDisponibles');
        var enRutaEl = document.getElementById('estadoEnRuta');
        var mantEl = document.getElementById('estadoMantenimiento');
        var totalEl = document.getElementById('totalCamiones');
        if(dispEl) dispEl.innerText = disponibles;
        if(enRutaEl) enRutaEl.innerText = enRuta;
        if(mantEl) mantEl.innerText = mantenimiento;
        if(totalEl) totalEl.innerText = camiones.length;
        
        var ctx = document.getElementById('estadoCamionesChart');
        if(ctx && estadoCamionesChart) estadoCamionesChart.destroy();
        if(ctx) {
            estadoCamionesChart = new Chart(ctx, {
                type:'pie',
                data:{labels:['Disponible','En Ruta','Mantenimiento'], datasets:[{data:[disponibles,enRuta,mantenimiento], backgroundColor:['#10b981','#f59e0b','#ef4444'], borderWidth:0, hoverOffset:10}]},
                options:{responsive:true, maintainAspectRatio:true, plugins:{legend:{position:'right',labels:{color:'#fff',font:{size:11}}}, tooltip:{backgroundColor:'#1a1a2e'}}}
            });
        }
    } catch(e) { console.error(e); }
}

async function eliminarConductor(id){
    if(confirm('Eliminar conductor?')){ await fetch('/api/eliminar_conductor',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id})}); cargarConductores(); }
}
async function eliminarCamion(id){
    if(confirm('Eliminar camión?')){ await fetch('/api/eliminar_camion',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id})}); cargarCamiones(); }
}

function abrirModalEstado(id, placa, estado){
    camionEstadoActual = id;
    var info = document.getElementById('estadoCamionInfo');
    if(info) info.innerHTML = 'Cambiando estado de: ' + placa + '<br>Actual: ' + estado;
    var select = document.getElementById('nuevoEstadoCamion');
    if(select) select.value = estado;
    var modal = document.getElementById('modalEstadoCamion');
    if(modal) modal.style.display = 'flex';
}

async function confirmarCambioEstado(){
    if(!camionEstadoActual) return;
    var nuevoEstado = document.getElementById('nuevoEstadoCamion') ? document.getElementById('nuevoEstadoCamion').value : '';
    await fetch('/api/actualizar_estado_camion',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:camionEstadoActual, estado:nuevoEstado})});
    mostrarToast('Estado cambiado a ' + nuevoEstado);
    cerrarModalEstadoCamion();
    cargarCamiones();
}

async function crearConductor(){
    var nombre = document.getElementById('conductorNombre') ? document.getElementById('conductorNombre').value : '';
    if(!nombre){ mostrarToast('Ingrese nombre'); return; }
    var cedula = document.getElementById('conductorCedula') ? document.getElementById('conductorCedula').value : '';
    var licencia = document.getElementById('conductorLicencia') ? document.getElementById('conductorLicencia').value : '';
    var telefono = document.getElementById('conductorTelefono') ? document.getElementById('conductorTelefono').value : '';
    var direccion = document.getElementById('conductorDireccion') ? document.getElementById('conductorDireccion').value : '';
    const r = await fetch('/api/crear_conductor',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ nombre:nombre, cedula:cedula, licencia:licencia, telefono:telefono, direccion:direccion })});
    const d = await r.json();
    if(d.ok){ mostrarToast('Conductor creado'); cerrarModalConductor(); cargarConductores(); }
}

async function crearCamion(){
    var placa = document.getElementById('camionPlaca') ? document.getElementById('camionPlaca').value : '';
    if(!placa){ mostrarToast('Ingrese placa'); return; }
    var marca = document.getElementById('camionMarca') ? document.getElementById('camionMarca').value : '';
    var modelo = document.getElementById('camionModelo') ? document.getElementById('camionModelo').value : '';
    var anio = document.getElementById('camionAnio') ? document.getElementById('camionAnio').value : '';
    var capacidad = parseFloat(document.getElementById('camionCapacidad') ? document.getElementById('camionCapacidad').value : 0) || 0;
    var conductor = document.getElementById('camionConductor') ? document.getElementById('camionConductor').value : '';
    var estado = document.getElementById('camionEstado') ? document.getElementById('camionEstado').value : '';
    const r = await fetch('/api/crear_camion',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ placa:placa, marca:marca, modelo:modelo, anio:anio, capacidad_galones:capacidad, tipo:'Cisterna', conductor_asignado:conductor, estado:estado })});
    const d = await r.json();
    if(d.ok){ mostrarToast('Camión creado'); cerrarModalCamion(); cargarCamiones(); }
}

function cambiarSubpanel(tipo){
    var subC = document.getElementById('subpanelConductores');
    var subM = document.getElementById('subpanelCamiones');
    var subE = document.getElementById('subpanelEstado');
    if(subC) subC.style.display = tipo === 'conductores' ? 'block' : 'none';
    if(subM) subM.style.display = tipo === 'camiones' ? 'block' : 'none';
    if(subE) subE.style.display = tipo === 'estado' ? 'block' : 'none';
    var btnC = document.getElementById('tabConductoresBtn');
    var btnM = document.getElementById('tabCamionesBtn');
    var btnE = document.getElementById('tabEstadoBtn');
    if(btnC) btnC.style.background = tipo === 'conductores' ? 'linear-gradient(135deg,#f59e0b,#d97706)' : 'transparent';
    if(btnM) btnM.style.background = tipo === 'camiones' ? 'linear-gradient(135deg,#f59e0b,#d97706)' : 'transparent';
    if(btnE) btnE.style.background = tipo === 'estado' ? 'linear-gradient(135deg,#f59e0b,#d97706)' : 'transparent';
    if(tipo === 'estado') cargarCamiones();
}

// ==================== CONFIGURACION IA/CORREO ====================
async function cargarConfigIA(){
    const r = await fetch('/api/config_ia');
    const d = await r.json();
    if(d.ok && d.config){
        var urlEl = document.getElementById('iaWebhookUrl');
        var keyEl = document.getElementById('iaApiKey');
        var enabledEl = document.getElementById('iaEnabled');
        if(urlEl) urlEl.value = d.config.webhook_url || '';
        if(keyEl) keyEl.value = d.config.api_key || '';
        if(enabledEl) enabledEl.checked = d.config.enabled || false;
    }
}
async function guardarConfigIA(){
    var url = document.getElementById('iaWebhookUrl') ? document.getElementById('iaWebhookUrl').value : '';
    var key = document.getElementById('iaApiKey') ? document.getElementById('iaApiKey').value : '';
    var enabled = document.getElementById('iaEnabled') ? document.getElementById('iaEnabled').checked : false;
    var config = { webhook_url: url, api_key: key, enabled: enabled, auto_send: false };
    await fetch('/api/config_ia',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(config)});
    mostrarToast('Configuración guardada');
}
async function probarIA(){
    mostrarToast('Enviando a IA...');
    const r = await fetch('/api/enviar_ia_ahora',{method:'POST'});
    const d = await r.json();
    if(d.ok) mostrarToast('Datos enviados');
    else mostrarToast('Error: '+d.error);
}
async function cargarConfigCorreo(){
    const r = await fetch('/api/config_correo');
    const d = await r.json();
    if(d.ok && d.config){
        var serverEl = document.getElementById('smtpServer');
        var portEl = document.getElementById('smtpPort');
        var emailEl = document.getElementById('emailRemitente');
        var passEl = document.getElementById('emailPassword');
        var enabledEl = document.getElementById('emailEnabled');
        if(serverEl) serverEl.value = d.config.smtp_server || 'smtp.gmail.com';
        if(portEl) portEl.value = d.config.smtp_port || 587;
        if(emailEl) emailEl.value = d.config.email_remitente || '';
        if(passEl) passEl.value = d.config.email_password || '';
        if(enabledEl) enabledEl.checked = d.config.enabled || false;
    }
}
async function guardarConfigCorreo(){
    var server = document.getElementById('smtpServer') ? document.getElementById('smtpServer').value : '';
    var port = parseInt(document.getElementById('smtpPort') ? document.getElementById('smtpPort').value : 587);
    var email = document.getElementById('emailRemitente') ? document.getElementById('emailRemitente').value : '';
    var pass = document.getElementById('emailPassword') ? document.getElementById('emailPassword').value : '';
    var enabled = document.getElementById('emailEnabled') ? document.getElementById('emailEnabled').checked : false;
    var config = { smtp_server: server, smtp_port: port, email_remitente: email, email_password: pass, enabled: enabled };
    await fetch('/api/config_correo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(config)});
    mostrarToast('Configuración de correo guardada');
}
async function probarCorreo(){
    var email = prompt('Ingrese su correo para prueba:');
    if(email){
        mostrarToast('Enviando correo de prueba...');
        const r = await fetch('/api/probar_correo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:email})});
        const d = await r.json();
        if(d.ok) mostrarToast('Correo de prueba enviado');
        else mostrarToast('Error: ' + d.error);
    }
}

// ==================== NAVEGACION ====================
function cambiarTab(tab) {
    var items = document.querySelectorAll('.nav-item');
    for(var i = 0; i < items.length; i++) items[i].classList.remove('active');
    var activeItem = document.querySelector('.nav-item[data-tab="' + tab + '"]');
    if(activeItem) activeItem.classList.add('active');
    
    var panels = ['recepcion', 'empresas', 'crear_id', 'paginas', 'editor', 'costos', 'facturacion', 'reportes', 'tablas', 'conductores', 'ia'];
    for(var p = 0; p < panels.length; p++) {
        var panel = document.getElementById(panels[p] + 'Panel');
        if(panel) panel.style.display = panels[p] === tab ? 'block' : 'none';
    }
    
    if(tab === 'conductores'){ cargarConductores(); cargarCamiones(); }
    if(tab === 'facturacion'){ cargarPedidosFacturar(); cargarFacturas(); }
    if(tab === 'reportes') cargarReportes(reportePeriodoActual);
    if(tab === 'ia'){ cargarConfigIA(); cargarConfigCorreo(); }
    if(tab === 'paginas') cargarPaginas();
    if(tab === 'costos' || tab === 'tablas'){ cargarDatosATablas(); }
}

async function crearEmpresa() {
    var nombre = document.getElementById('newNombre') ? document.getElementById('newNombre').value : '';
    if(!nombre){ mostrarToast('Ingrese nombre'); return; }
    var email = document.getElementById('newEmail') ? document.getElementById('newEmail').value : '';
    var contacto = document.getElementById('newContacto') ? document.getElementById('newContacto').value : '';
    var cedula = document.getElementById('newCedula') ? document.getElementById('newCedula').value : '';
    var telefono = document.getElementById('newTelefono') ? document.getElementById('newTelefono').value : '';
    var direccion = document.getElementById('newDireccion') ? document.getElementById('newDireccion').value : '';
    var tipo = document.getElementById('newTipo') ? document.getElementById('newTipo').value : '';
    var placa = document.getElementById('newPlaca') ? document.getElementById('newPlaca').value : '';
    var idPersonalizado = document.getElementById('newIdPersonalizado') ? document.getElementById('newIdPersonalizado').value : undefined;
    const r = await fetch('/api/crear_empresa',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        nombre:nombre, contacto:contacto, cedula:cedula, telefono:telefono, direccion:direccion,
        tipo:tipo, placa:placa, id:idPersonalizado, email:email
    })});
    const d = await r.json();
    if(d.ok){
        mostrarToast('Creado: ' + d.empresa.id);
        cargarDatosATablas();
        var idDisplay = document.getElementById('idGeneradoDisplay');
        if(idDisplay) idDisplay.innerText = d.empresa.id;
        var creadoDisplay = document.getElementById('idCreadoDisplay');
        if(creadoDisplay) creadoDisplay.style.display = 'block';
        setTimeout(function(){ if(creadoDisplay) creadoDisplay.style.display = 'none'; }, 3000);
        var nombreInput = document.getElementById('newNombre');
        var emailInput = document.getElementById('newEmail');
        if(nombreInput) nombreInput.value = '';
        if(emailInput) emailInput.value = '';
    } else { mostrarToast(d.error); }
}

function generarIdSugerido() {
    var tipo = document.getElementById('newTipo') ? document.getElementById('newTipo').value : '';
    var nombre = document.getElementById('newNombre') ? document.getElementById('newNombre').value : '';
    var prefijos = {Cliente:'CLI',Proveedor:'PRO'};
    var prefijo = prefijos[tipo] || 'EMP';
    var iniciales = nombre ? nombre.substring(0,3).toUpperCase() : 'XXX';
    var idInput = document.getElementById('newIdPersonalizado');
    if(idInput) idInput.value = prefijo + '-' + iniciales + Math.floor(Math.random() * 900 + 100);
}

async function crearPedidoManual() {
    var empresaId = document.getElementById('empresaSelect') ? document.getElementById('empresaSelect').value : '';
    if(!empresaId){ mostrarToast('Seleccione empresa'); return; }
    var empresaNombre = document.getElementById('empresaNombreManual') ? document.getElementById('empresaNombreManual').value : '';
    var empresaIdCliente = document.getElementById('empresaIdManual') ? document.getElementById('empresaIdManual').value : '';
    var origen = document.getElementById('origenManual') ? document.getElementById('origenManual').value : '';
    var destino = document.getElementById('destinoManual') ? document.getElementById('destinoManual').value : '';
    var galones = parseFloat(document.getElementById('galonesManual') ? document.getElementById('galonesManual').value : 0) || 0;
    var precio = parseFloat(document.getElementById('precioManual') ? document.getElementById('precioManual').value : 0) || 0;
    var tipoCombustible = document.getElementById('tipoCombustibleManual') ? document.getElementById('tipoCombustibleManual').value : '';
    const r = await fetch('/api/crear_pedido_combustible',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        empresa_id:empresaId, nombre:'Pedido Manual',
        empresa_nombre:empresaNombre, empresa_id_cliente:empresaIdCliente,
        origen:origen, destino:destino, galones:galones, precio_por_galon:precio, tipo_combustible:tipoCombustible
    })});
    const d = await r.json();
    if(d.ok){ mostrarToast('Pedido creado'); cerrarModalPedido(); cargarPedidosTarjetas(); cargarReportes(reportePeriodoActual); cargarDatosATablas(); }
    else { mostrarToast('Error'); }
}

async function generarReporteExcel() { mostrarToast('Función disponible en versión completa'); }
async function generarReportePDF() { mostrarToast('Función disponible en versión completa'); }

// ==================== INICIALIZACION ====================
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM cargado, iniciando dashboard...");
    
    setTimeout(function(){ 
        var splash = document.getElementById('splashScreen'); 
        if(splash) splash.style.display = 'none'; 
    }, 1500);
    
    // Inicializar todo
    obtenerPublicUrl().then(function() {
        cargarPedidosTarjetas();
        cargarEstadisticas();
        cargarPaginas();
        cargarGraficas();
        cargarReportes('todos');
        cargarFacturas();
        cargarEmpresasSelect();
        cargarDatosATablas();
        cargarConductores();
        cargarCamiones();
    });
    
    // Intervalos
    setInterval(function(){ cargarPedidosTarjetas(); cargarEstadisticas(); }, 30000);
    setInterval(obtenerPublicUrl, 60000);
    
    // Eventos de navegación
    var navItems = document.querySelectorAll('.nav-item');
    for(var i = 0; i < navItems.length; i++) {
        navItems[i].onclick = function() {
            var tab = this.getAttribute('data-tab');
            if(tab) cambiarTab(tab);
        };
    }
    
    // Eventos de botones
    var crearIdBtn = document.getElementById('crearIdBtn');
    if(crearIdBtn) crearIdBtn.addEventListener('click', crearEmpresa);
    
    var generarIdBtn = document.getElementById('generarIdSugeridoBtn');
    if(generarIdBtn) generarIdBtn.addEventListener('click', generarIdSugerido);
    
    var crearPaginaBtn = document.getElementById('crearPaginaBtn');
    if(crearPaginaBtn) crearPaginaBtn.addEventListener('click', crearPagina);
    
    var crearPedidoBtn = document.getElementById('crearPedidoManualBtn');
    if(crearPedidoBtn) crearPedidoBtn.addEventListener('click', function(){ cargarEmpresasSelect(); var modal = document.getElementById('modalPedidoManual'); if(modal) modal.style.display = 'flex'; });
    
    var guardarPedidoBtn = document.getElementById('guardarPedidoManualBtn');
    if(guardarPedidoBtn) guardarPedidoBtn.addEventListener('click', crearPedidoManual);
    
    var cargarFacturarBtn = document.getElementById('cargarPedidosFacturarBtn');
    if(cargarFacturarBtn) cargarFacturarBtn.addEventListener('click', cargarPedidosFacturar);
    
    var refrescarFacturasBtn = document.getElementById('refrescarFacturasBtn');
    if(refrescarFacturasBtn) refrescarFacturasBtn.addEventListener('click', cargarFacturas);
    
    var enviarFacturaBtn = document.getElementById('enviarFacturaHijoBtn');
    if(enviarFacturaBtn) enviarFacturaBtn.addEventListener('click', enviarFactura);
    
    var excelBtn = document.getElementById('generarExcelReporteBtn');
    if(excelBtn) excelBtn.addEventListener('click', generarReporteExcel);
    
    var pdfBtn = document.getElementById('generarPDFReporteBtn');
    if(pdfBtn) pdfBtn.addEventListener('click', generarReportePDF);
    
    var urlCard = document.getElementById('urlCard');
    if(urlCard) urlCard.addEventListener('click', function(){ if(publicUrl) copiarTexto(publicUrl); });
    
    var guardarIaBtn = document.getElementById('guardarIaConfigBtn');
    if(guardarIaBtn) guardarIaBtn.addEventListener('click', guardarConfigIA);
    
    var probarIaBtn = document.getElementById('probarIaBtn');
    if(probarIaBtn) probarIaBtn.addEventListener('click', probarIA);
    
    var guardarCorreoBtn = document.getElementById('guardarCorreoBtn');
    if(guardarCorreoBtn) guardarCorreoBtn.addEventListener('click', guardarConfigCorreo);
    
    var probarCorreoBtn = document.getElementById('probarCorreoBtn');
    if(probarCorreoBtn) probarCorreoBtn.addEventListener('click', probarCorreo);
    
    var nuevoConductorBtn = document.getElementById('nuevoConductorBtn');
    if(nuevoConductorBtn) nuevoConductorBtn.addEventListener('click', function(){ var modal = document.getElementById('modalConductor'); if(modal) modal.style.display = 'flex'; });
    
    var nuevoCamionBtn = document.getElementById('nuevoCamionBtn');
    if(nuevoCamionBtn) nuevoCamionBtn.addEventListener('click', function(){ var modal = document.getElementById('modalCamion'); if(modal) modal.style.display = 'flex'; });
    
    var guardarConductorBtn = document.getElementById('guardarConductorBtn');
    if(guardarConductorBtn) guardarConductorBtn.addEventListener('click', crearConductor);
    
    var guardarCamionBtn = document.getElementById('guardarCamionBtn');
    if(guardarCamionBtn) guardarCamionBtn.addEventListener('click', crearCamion);
    
    var confirmarEstadoBtn = document.getElementById('confirmarCambioEstadoBtn');
    if(confirmarEstadoBtn) confirmarEstadoBtn.addEventListener('click', confirmarCambioEstado);
    
    var tabConductores = document.getElementById('tabConductoresBtn');
    if(tabConductores) tabConductores.addEventListener('click', function(){ cambiarSubpanel('conductores'); });
    
    var tabCamiones = document.getElementById('tabCamionesBtn');
    if(tabCamiones) tabCamiones.addEventListener('click', function(){ cambiarSubpanel('camiones'); });
    
    var tabEstado = document.getElementById('tabEstadoBtn');
    if(tabEstado) tabEstado.addEventListener('click', function(){ cambiarSubpanel('estado'); });
    
    // Periodo chips
    var chips = document.querySelectorAll('.periodo-chip');
    for(var i = 0; i < chips.length; i++) {
        chips[i].onclick = function() {
            var allChips = document.querySelectorAll('.periodo-chip');
            for(var j = 0; j < allChips.length; j++) allChips[j].classList.remove('active');
            this.classList.add('active');
            cargarReportes(this.getAttribute('data-periodo'));
        };
    }
    
    console.log("🚀 Dashboard inicializado correctamente");
});