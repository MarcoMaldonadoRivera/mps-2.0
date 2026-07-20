/**
 * ================================================================
 * MPS 2.0 — Sistema de Gestión de Impresión
 * Archivo: app.js
 * Descripción: Lógica de navegación, integración API backend,
 *              KPIs dinámicos e interacciones del frontend.
 * ================================================================
 */

// ================================================================
// CONFIGURACIÓN DE LA API
// ================================================================
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000/api'
    : 'https://mps-2-0.onrender.com/api';

/**
 * Wrapper genérico para peticiones fetch al backend.
 * @param {string} endpoint - Ruta relativa (ej: '/clientes')
 * @param {object} options - Opciones de fetch (method, body, etc.)
 * @returns {Promise<object>} - JSON de la respuesta
 */
async function api(endpoint, options = {}) {
    try {
        const url = `${API_BASE}${endpoint}`;
        const config = {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        };
        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }
        const response = await fetch(url, config);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || `Error HTTP ${response.status}`);
        }
        return data;
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error.message);
        showToast(error.message, 'error');
        throw error;
    }
}


// ================================================================
// SISTEMA DE NOTIFICACIONES TOAST
// ================================================================

/**
 * Muestra una notificación toast flotante.
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - 'success' | 'error' | 'warning' | 'info'
 */
function showToast(message, type = 'info') {
    // Colores según tipo
    const colors = {
        success: 'bg-success-600',
        error: 'bg-danger-600',
        warning: 'bg-warning-600',
        info: 'bg-primary-600'
    };
    const icons = {
        success: 'check-circle',
        error: 'alert-circle',
        warning: 'alert-triangle',
        info: 'info'
    };

    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 z-[100] flex items-center gap-3 px-5 py-3
                       rounded-xl shadow-2xl text-white text-sm font-medium
                       ${colors[type]} transform transition-all duration-300
                       translate-x-full opacity-0`;
    toast.innerHTML = `
        <i data-lucide="${icons[type]}" class="w-5 h-5 shrink-0"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);
    lucide.createIcons({ nodes: [toast] });

    // Animar entrada
    requestAnimationFrame(() => {
        toast.classList.remove('translate-x-full', 'opacity-0');
        toast.classList.add('translate-x-0', 'opacity-100');
    });

    // Auto-eliminar después de 3 segundos
    setTimeout(() => {
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}


// ================================================================
// INICIALIZACIÓN
// ================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Verificar sesión activa
    checkSession();
    lucide.createIcons();
    renderKPIs('gerente');
    navigateTo('dashboard');
    cargarClientesDesdeAPI();
});


// ================================================================
// NAVEGACIÓN ENTRE SECCIONES
// ================================================================

function navigateTo(section) {
    const sectionMeta = {
        dashboard:   { title: 'Dashboard', subtitle: 'Bienvenido al sistema de gestión de impresión' },
        clientes:    { title: 'Gestión Multicliente', subtitle: 'Administra los clientes y sus datos de contacto' },
        impresoras:  { title: 'Parque de Impresoras', subtitle: 'Inventario y control de equipos de impresión' },
        operativo:   { title: 'Registro Operativo', subtitle: 'Contadores mensuales y visitas técnicas' },
        usuarios:    { title: 'Gestión de Usuarios', subtitle: 'Administra los usuarios y roles del sistema' },
        configuracion: { title: 'Configuración', subtitle: 'Ajustes del sistema y datos de la empresa' },
    };

    document.querySelectorAll('.page-section').forEach(el => el.classList.remove('active'));
    const target = document.getElementById(`section-${section}`);
    if (target) target.classList.add('active');

    const meta = sectionMeta[section];
    if (meta) {
        document.getElementById('sectionTitle').textContent = meta.title;
        document.getElementById('sectionSubtitle').textContent = meta.subtitle;
    }

    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('bg-slate-800', 'text-white');
        item.classList.add('text-slate-300');
    });
    const activeNav = document.querySelector(`.nav-item[data-section="${section}"]`);
    if (activeNav) {
        activeNav.classList.add('bg-slate-800', 'text-white');
        activeNav.classList.remove('text-slate-300');
    }

    closeSidebar();
    event && event.preventDefault();

    // Cargar datos cuando se navega a una sección
    if (section === 'clientes') {
        cargarClientesDesdeAPI();
        cargarSelectorClientes();
    }
    if (section === 'usuarios') cargarUsuariosDesdeAPI();
    if (section === 'impresoras') cargarSelectorClientesImpresoras();
}


// ================================================================
// SIDEBAR RESPONSIVA
// ================================================================

function toggleSidebar() {
    document.getElementById('appSidebar').classList.toggle('open');
    document.getElementById('sidebarOverlay').classList.toggle('show');
}

function closeSidebar() {
    document.getElementById('appSidebar').classList.remove('open');
    document.getElementById('sidebarOverlay').classList.remove('show');
}


// ================================================================
// MÓDULO 1: DASHBOARD — KPIs DINÁMICOS POR ROL
// ================================================================

const kpiData = {
    gerente: [
        { title: 'Equipos en Alerta', value: '3', icon: 'alert-triangle', color: 'danger', change: '+1 este mes', changeType: 'negative' },
        { title: 'Garantías por Vencer', value: '7', icon: 'shield-alert', color: 'warning', subtitle: 'Menos de 30 días', change: '2 vencen pronto', changeType: 'warning' },
        { title: 'Costo Total del Mes', value: '$2.450.000', icon: 'dollar-sign', color: 'primary', change: '-8% vs anterior', changeType: 'positive' },
        { title: 'Suministros Bajos', value: '4', icon: 'droplets', color: 'warning', subtitle: '2 críticos — 2 bajos', change: 'Reordenar urgente', changeType: 'negative' },
    ],
    finanzas: [
        { title: 'Costo Total del Mes', value: '$2.450.000', icon: 'dollar-sign', color: 'primary', change: '-8% vs anterior', changeType: 'positive' },
        { title: 'Costo por Tóner', value: '$1.280.000', icon: 'droplets', color: 'warning', change: '+3% vs anterior', changeType: 'negative' },
        { title: 'Costo por Reparaciones', value: '$680.000', icon: 'wrench', color: 'danger', change: '-15% vs anterior', changeType: 'positive' },
        { title: 'Costo Promedio/Equipo', value: '$81.667', icon: 'calculator', color: 'success', change: 'Estable', changeType: 'neutral' },
    ],
    tecnico: [
        { title: 'Visitas Pendientes', value: '5', icon: 'calendar-check', color: 'primary', change: '2 urgentes', changeType: 'warning' },
        { title: 'Equipos en Reparación', value: '2', icon: 'wrench', color: 'warning', change: '1 ingresado hoy', changeType: 'neutral' },
        { title: 'Suministros Bajos', value: '4', icon: 'droplets', color: 'danger', subtitle: '2 críticos — Revisar', change: 'Tóner y fusor', changeType: 'negative' },
        { title: 'Páginas Mes Actual', value: '148.320', icon: 'file-text', color: 'success', change: 'Conteo actualizado', changeType: 'neutral' },
    ],
    freelance: [
        { title: 'Mis Equipos Asignados', value: '8', icon: 'printer', color: 'primary', change: '4 clientes', changeType: 'neutral' },
        { title: 'Visitas Este Mes', value: '12', icon: 'calendar-check', color: 'success', change: '3 restantes', changeType: 'neutral' },
        { title: 'Ingresos del Mes', value: '$850.000', icon: 'trending-up', color: 'success', change: '+12% vs anterior', changeType: 'positive' },
        { title: 'Alertas Activas', value: '2', icon: 'bell', color: 'danger', change: 'Suministro bajo', changeType: 'negative' },
    ],
};

const roleNames = {
    gerente: '🏢 Gerente General', finanzas: '💰 Finanzas',
    tecnico: '🔧 Técnico', freelance: '🚀 Freelance'
};

function renderKPIs(role) {
    const grid = document.getElementById('kpiGrid');
    const kpis = kpiData[role] || kpiData.gerente;
    const colorMap = {
        primary: { bg: 'bg-primary-50', icon: 'text-primary-600', border: 'border-primary-100' },
        success: { bg: 'bg-success-50', icon: 'text-success-600', border: 'border-success-100' },
        warning: { bg: 'bg-warning-50', icon: 'text-warning-600', border: 'border-warning-100' },
        danger:  { bg: 'bg-danger-50',  icon: 'text-danger-600',  border: 'border-danger-100' },
    };
    const changeColorMap = {
        positive: 'text-success-600 bg-success-50', negative: 'text-danger-600 bg-danger-50',
        warning: 'text-warning-600 bg-warning-50', neutral: 'text-slate-500 bg-slate-100',
    };

    grid.innerHTML = kpis.map(kpi => {
        const c = colorMap[kpi.color] || colorMap.primary;
        const cc = changeColorMap[kpi.changeType] || changeColorMap.neutral;
        return `
            <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow group">
                <div class="flex items-start justify-between mb-3">
                    <div class="w-11 h-11 rounded-xl ${c.bg} ${c.border} border flex items-center justify-center group-hover:scale-110 transition-transform">
                        <i data-lucide="${kpi.icon}" class="w-5 h-5 ${c.icon}"></i>
                    </div>
                    <span class="text-[11px] font-semibold ${cc} px-2 py-0.5 rounded-full">${kpi.change}</span>
                </div>
                <h4 class="text-2xl font-bold text-slate-800 tracking-tight">${kpi.value}</h4>
                <p class="text-sm text-slate-500 mt-0.5">${kpi.title}
                    ${kpi.subtitle ? `<span class="text-xs text-slate-400 block">${kpi.subtitle}</span>` : ''}
                </p>
            </div>`;
    }).join('');
    lucide.createIcons();
}

function changeRole(role) {
    renderKPIs(role);
    const badge = document.getElementById('dashboardRoleBadge');
    if (badge) badge.textContent = roleNames[role] || roleNames.gerente;
}


// ================================================================
// MÓDULO 2: GESTIÓN DE CLIENTES — CRUD COMPLETO CON API
// ================================================================

function toggleClientForm() {
    const form = document.getElementById('clientForm');
    form.classList.toggle('hidden');
    if (!form.classList.contains('hidden')) {
        form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

/**
 * Carga la lista de clientes desde el backend y renderiza la tabla.
 */
async function cargarClientesDesdeAPI() {
    try {
        const clientes = await api('/clientes');
        renderizarTablaClientes(clientes);
    } catch (e) {
        console.warn('No se pudo conectar al backend, mostrando datos de ejemplo.');
    }
}

/**
 * Carga los clientes en el selector "Cliente Actual" de la sección clientes.
 */
async function cargarSelectorClientes() {
    try {
        const clientes = await api('/clientes');
        const select = document.getElementById('currentClient');
        if (!select) return;
        select.innerHTML = '<option value="all">📋 Todos los clientes</option>';
        clientes.forEach(c => {
            select.innerHTML += `<option value="${c.ID_cliente}">${c.razon_social}</option>`;
        });
    } catch (e) { /* silently fail */ }
}

/**
 * Carga los clientes en los selects del formulario de registro de impresoras.
 */
async function cargarSelectorClientesImpresoras() {
    try {
        const clientes = await api('/clientes');
        const selects = document.querySelectorAll('#section-impresoras select');
        selects.forEach(select => {
            // Solo actualizar selects que tengan la opción "Seleccionar cliente"
            if (select.querySelector('option[value=""]') && select.querySelector('option[value="abc"]')) {
                select.innerHTML = '<option value="">Seleccionar cliente</option>';
                clientes.forEach(c => {
                    select.innerHTML += `<option value="${c.ID_cliente}">${c.razon_social}</option>`;
                });
            }
        });
    } catch (e) { /* silently fail */ }
}

/**
 * Renderiza la tabla de clientes con datos del API.
 */
function renderizarTablaClientes(clientes) {
    const tbody = document.querySelector('#section-clientes tbody');
    if (!tbody || !clientes) return;

    tbody.innerHTML = clientes.map(c => `
        <tr class="border-b border-slate-50 hover:bg-slate-50/50 transition">
            <td class="px-6 py-3.5 font-mono text-xs text-slate-500">${c.rut}</td>
            <td class="px-6 py-3.5 font-medium text-slate-700">${c.razon_social}</td>
            <td class="px-6 py-3.5 text-slate-600 hidden md:table-cell">${c.contacto}</td>
            <td class="px-6 py-3.5 text-slate-500 hidden lg:table-cell">${c.telefono || '—'}</td>
            <td class="px-6 py-3.5 hidden xl:table-cell">
                <span class="inline-flex items-center gap-1 bg-primary-50 text-primary-700 px-2 py-0.5 rounded-md text-xs font-semibold">
                    <i data-lucide="printer" class="w-3 h-3"></i> 0
                </span>
            </td>
            <td class="px-6 py-3.5 text-center">
                <div class="flex items-center justify-center gap-1">
                    <button onclick="editarCliente(${c.ID_cliente})" class="p-1.5 rounded-lg hover:bg-primary-50 text-primary-600 transition" title="Editar">
                        <i data-lucide="pencil" class="w-4 h-4"></i>
                    </button>
                    <button onclick="eliminarCliente(${c.ID_cliente}, '${c.razon_social}')" class="p-1.5 rounded-lg hover:bg-danger-50 text-danger-500 transition" title="Eliminar">
                        <i data-lucide="trash-2" class="w-4 h-4"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');

    // Actualizar contador
    const countSpan = document.querySelector('#section-clientes .text-sm.font-normal');
    if (countSpan) countSpan.textContent = `(${clientes.length})`;

    lucide.createIcons();
}

/**
 * Guarda un cliente nuevo o actualiza uno existente.
 */
async function guardarCliente() {
    const idEdit = document.getElementById('clienteIdEdit').value;
    const rut = document.getElementById('clienteRut').value.trim();
    const razon_social = document.getElementById('clienteRazonSocial').value.trim();
    const direccion = document.getElementById('clienteDireccion').value.trim();
    const telefono = document.getElementById('clienteTelefono').value.trim();
    const contacto = document.getElementById('clienteContacto').value.trim();
    const email_contacto = document.getElementById('clienteEmail').value.trim();

    // Validación básica
    if (!rut || !razon_social || !contacto) {
        showToast('Los campos RUT, Razón Social y Contacto son obligatorios', 'warning');
        return;
    }

    const body = { rut, razon_social, direccion: direccion || null, telefono: telefono || null, contacto, email_contacto: email_contacto || null };

    try {
        if (idEdit) {
            await api(`/clientes/${idEdit}`, { method: 'PUT', body });
            showToast('Cliente actualizado correctamente', 'success');
        } else {
            await api('/clientes', { method: 'POST', body });
            showToast('Cliente registrado correctamente', 'success');
        }
        limpiarFormularioCliente();
        toggleClientForm();
        cargarClientesDesdeAPI();
    } catch (e) {
        // El toast ya se mostró en api()
    }
}

/**
 * Carga los datos de un cliente en el formulario para editarlo.
 */
async function editarCliente(id) {
    try {
        const cliente = await api(`/clientes/${id}`);
        document.getElementById('clienteIdEdit').value = cliente.ID_cliente;
        document.getElementById('clienteRut').value = cliente.rut;
        document.getElementById('clienteRazonSocial').value = cliente.razon_social;
        document.getElementById('clienteDireccion').value = cliente.direccion || '';
        document.getElementById('clienteTelefono').value = cliente.telefono || '';
        document.getElementById('clienteContacto').value = cliente.contacto;
        document.getElementById('clienteEmail').value = cliente.email_contacto || '';
        document.getElementById('clientFormTitle').textContent = 'Editar Cliente';
        toggleClientForm();
    } catch (e) { /* toast ya mostrado */ }
}

/**
 * Elimina un cliente con confirmación.
 */
async function eliminarCliente(id, nombre) {
    if (!confirm(`¿Estás seguro de eliminar a "${nombre}"?\n\nEsta acción eliminará también todos sus equipos y registros asociados.`)) return;
    try {
        await api(`/clientes/${id}`, { method: 'DELETE' });
        showToast('Cliente eliminado correctamente', 'success');
        cargarClientesDesdeAPI();
    } catch (e) { /* toast ya mostrado */ }
}

/**
 * Limpia todos los campos del formulario de cliente.
 */
function limpiarFormularioCliente() {
    document.getElementById('clienteIdEdit').value = '';
    document.getElementById('clienteRut').value = '';
    document.getElementById('clienteRazonSocial').value = '';
    document.getElementById('clienteDireccion').value = '';
    document.getElementById('clienteTelefono').value = '';
    document.getElementById('clienteContacto').value = '';
    document.getElementById('clienteEmail').value = '';
    document.getElementById('clientFormTitle').textContent = 'Registrar Nuevo Cliente';
}


// ================================================================
// MÓDULO 4: CONTADORES — CÁLCULO Y REGISTRO vía API
// ================================================================

function calculateDifference() {
    const initialInput = document.getElementById('counterInitial');
    const currentInput = document.getElementById('counterCurrent');
    const diffDisplay = document.getElementById('counterDifference');
    if (!initialInput || !currentInput || !diffDisplay) return;

    const initial = parseInt(initialInput.value) || 0;
    const current = parseInt(currentInput.value) || 0;

    if (initialInput.value === '' && currentInput.value === '') {
        diffDisplay.textContent = '—';
        diffDisplay.className = 'w-full bg-slate-50 border-2 border-dashed border-slate-200 rounded-lg px-3.5 py-2.5 text-sm font-bold text-slate-400 text-center font-mono transition-all duration-300';
        return;
    }

    const diff = current - initial;
    if (diff < 0) {
        diffDisplay.textContent = `⚠ Error: ${diff.toLocaleString('es-CL')} págs.`;
        diffDisplay.className = 'w-full bg-danger-50 border-2 border-danger-200 rounded-lg px-3.5 py-2.5 text-sm font-bold text-danger-600 text-center font-mono transition-all duration-300';
    } else if (diff === 0) {
        diffDisplay.textContent = '0 páginas (sin cambio)';
        diffDisplay.className = 'w-full bg-slate-50 border-2 border-slate-200 rounded-lg px-3.5 py-2.5 text-sm font-bold text-slate-500 text-center font-mono transition-all duration-300';
    } else if (diff > 50000) {
        diffDisplay.textContent = `▲ ${diff.toLocaleString('es-CL')} páginas`;
        diffDisplay.className = 'w-full bg-warning-50 border-2 border-warning-200 rounded-lg px-3.5 py-2.5 text-sm font-bold text-warning-600 text-center font-mono transition-all duration-300';
    } else {
        diffDisplay.textContent = `▲ ${diff.toLocaleString('es-CL')} páginas`;
        diffDisplay.className = 'w-full bg-success-50 border-2 border-success-200 rounded-lg px-3.5 py-2.5 text-sm font-bold text-success-600 text-center font-mono transition-all duration-300';
    }
}

/**
 * Registra un contador mensual enviándolo al backend.
 */
async function registrarContador() {
    const printerSelect = document.getElementById('counterPrinter');
    const initialInput = document.getElementById('counterInitial');
    const currentInput = document.getElementById('counterCurrent');

    if (!printerSelect.value) {
        showToast('Selecciona una impresora', 'warning');
        return;
    }
    if (!currentInput.value) {
        showToast('Ingresa el contador mensual actual', 'warning');
        return;
    }

    const body = {
        ID_impresora: parseInt(printerSelect.value) || 1,
        ID_usuario: 1, // Usuario por defecto (Admin)
        fecha_lectura: new Date().toISOString().split('T')[0],
        contador_inicial: parseInt(initialInput.value) || 0,
        contador_mensual: parseInt(currentInput.value),
    };

    try {
        const result = await api('/contadores', { method: 'POST', body });
        showToast(`Contador registrado: ${result.paginas_mes} páginas este mes`, 'success');
        initialInput.value = '';
        currentInput.value = '';
        calculateDifference();
    } catch (e) { /* toast ya mostrado */ }
}


// ================================================================
// MÓDULO 4: VISITAS TÉCNICAS — REGISTRO vía API
// ================================================================

async function registrarVisita() {
    const motivo = document.querySelector('input[name="motivo"]:checked')?.value || 'Preventiva';
    const reporte = document.querySelector('#section-operativo textarea')?.value || '';
    const costo = document.getElementById('visitCost')?.value || '0';
    const garantia = document.getElementById('warrantyToggle')?.checked || false;

    if (!reporte || reporte.length < 5) {
        showToast('El reporte técnico debe tener al menos 5 caracteres', 'warning');
        return;
    }

    const body = {
        ID_impresora: 1,
        ID_usuario: 1,
        fecha_visita: new Date().toISOString().split('T')[0],
        motivo: motivo === 'preventiva' ? 'Preventiva' : 'Correctiva',
        reporte_tecnico: reporte,
        costo_visita: parseFloat(costo),
        aplica_garantia: garantia,
    };

    try {
        await api('/visitas', { method: 'POST', body });
        showToast('Visita técnica registrada correctamente', 'success');
        // Limpiar formulario
        if (document.querySelector('#section-operativo textarea')) {
            document.querySelector('#section-operativo textarea').value = '';
        }
        document.getElementById('visitCost').value = '0';
        document.getElementById('costSummary').textContent = '$0';
    } catch (e) { /* toast ya mostrado */ }
}


// ================================================================
// TOGGLE DE GARANTÍA
// ================================================================

document.addEventListener('DOMContentLoaded', () => {
    const warrantyToggle = document.getElementById('warrantyToggle');
    const warrantyLabel = document.getElementById('warrantyLabel');
    const costSummary = document.getElementById('costSummary');
    const warrantyNote = document.getElementById('warrantyNote');
    const visitCostInput = document.getElementById('visitCost');

    if (warrantyToggle) {
        warrantyToggle.addEventListener('change', () => {
            const isActive = warrantyToggle.checked;
            warrantyLabel.textContent = isActive ? 'Sí, aplica' : 'No aplica';
            warrantyLabel.className = isActive ? 'text-sm text-success-600 font-semibold' : 'text-sm text-slate-500 font-medium';
            if (isActive) {
                costSummary.textContent = '$0';
                costSummary.className = 'text-lg font-bold text-success-600';
                warrantyNote.classList.remove('hidden');
            } else {
                const cost = parseInt(visitCostInput?.value) || 0;
                costSummary.textContent = `$${cost.toLocaleString('es-CL')}`;
                costSummary.className = 'text-lg font-bold text-slate-800';
                warrantyNote.classList.add('hidden');
            }
        });
    }

    if (visitCostInput) {
        visitCostInput.addEventListener('input', () => {
            if (!warrantyToggle?.checked) {
                const cost = parseInt(visitCostInput.value) || 0;
                costSummary.textContent = `$${cost.toLocaleString('es-CL')}`;
            }
        });
    }
});


// ================================================================
// GESTIÓN DE SESIÓN Y AUTENTICACIÓN
// ================================================================

/**
 * Verifica si hay sesión activa. Si no, redirige al login.
 */
function checkSession() {
    const userData = localStorage.getItem('mps_user');
    if (!userData) {
        window.location.href = '/login';
        return;
    }
    const user = JSON.parse(userData);
    updateUserSidebar(user);
    // Actualizar el selector de rol según el rol del usuario
    const roleMap = {
        'Gerente General': 'gerente', 'Gerente Finanzas': 'finanzas',
        'Gerente Técnico': 'tecnico', 'Técnico Freelance': 'freelance',
    };
    const selector = document.getElementById('roleSelector');
    if (selector && roleMap[user.rol]) {
        selector.value = roleMap[user.rol];
        changeRole(roleMap[user.rol]);
    }
}

/**
 * Actualiza la información del usuario en el sidebar.
 */
function updateUserSidebar(user) {
    const avatar = document.getElementById('sidebarUserAvatar');
    const name = document.getElementById('sidebarUserName');
    const email = document.getElementById('sidebarUserEmail');
    if (avatar) avatar.textContent = user.nombre ? user.nombre.substring(0, 2).toUpperCase() : 'AD';
    if (name) name.textContent = user.nombre || 'Admin Demo';
    if (email) email.textContent = user.email || 'admin@mps.cl';
}

/**
 * Cierra la sesión y redirige al login.
 */
function logout() {
    localStorage.removeItem('mps_user');
    window.location.href = '/login';
}


// ================================================================
// MÓDULO 5: GESTIÓN DE USUARIOS — CRUD COMPLETO
// ================================================================

function toggleUsuarioForm() {
    const form = document.getElementById('usuarioForm');
    form.classList.toggle('hidden');
    if (!form.classList.contains('hidden')) {
        form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        cargarSelectsUsuarios();
    }
}

/**
 * Carga los select de roles y clientes para el formulario de usuarios.
 */
async function cargarSelectsUsuarios() {
    try {
        const [roles, clientes] = await Promise.all([api('/roles'), api('/clientes')]);
        const rolSelect = document.getElementById('usuarioRol');
        const clienteSelect = document.getElementById('usuarioCliente');

        if (rolSelect && roles.length) {
            rolSelect.innerHTML = roles.map(r => `<option value="${r.ID_rol}">${r.nombre_rol}</option>`).join('');
        }
        if (clienteSelect && clientes.length) {
            clienteSelect.innerHTML = '<option value="">Ninguno (Admin interno)</option>' +
                clientes.map(c => `<option value="${c.ID_cliente}">${c.razon_social}</option>`).join('');
        }
    } catch (e) { console.warn('No se pudieron cargar roles/clientes'); }
}

/**
 * Carga la lista de usuarios desde el backend y renderiza la tabla.
 */
async function cargarUsuariosDesdeAPI() {
    try {
        const usuarios = await api('/usuarios');
        renderizarTablaUsuarios(usuarios);
    } catch (e) { console.warn('No se pudieron cargar usuarios'); }
}

/**
 * Renderiza la tabla de usuarios con datos del API.
 */
function renderizarTablaUsuarios(usuarios) {
    const tbody = document.getElementById('usuariosTableBody');
    if (!tbody || !usuarios) return;

    const roleNamesMap = { 1: 'Gerente General', 2: 'Gerente Finanzas', 3: 'Gerente Técnico', 4: 'Técnico Freelance' };

    tbody.innerHTML = usuarios.map(u => `
        <tr class="border-b border-slate-50 hover:bg-slate-50/50 transition">
            <td class="px-6 py-3.5">
                <div class="font-medium text-slate-700">${u.nombre}</div>
            </td>
            <td class="px-6 py-3.5 text-slate-500 text-sm">${u.email}</td>
            <td class="px-6 py-3.5 hidden md:table-cell">
                <span class="text-xs font-semibold bg-primary-50 text-primary-700 px-2 py-0.5 rounded-full">
                    ${roleNamesMap[u.ID_rol] || 'Rol ' + u.ID_rol}
                </span>
            </td>
            <td class="px-6 py-3.5 text-slate-500 text-sm hidden lg:table-cell">${u.ID_cliente || '—'}</td>
            <td class="px-6 py-3.5">
                <span class="badge ${u.estado === 'activo' ? 'badge-active' : 'badge-down'}">
                    ${u.estado === 'activo' ? '✅ Activo' : '❌ Inactivo'}
                </span>
            </td>
            <td class="px-6 py-3.5 text-center">
                <div class="flex items-center justify-center gap-1">
                    <button onclick="editarUsuario(${u.ID_usuario})" class="p-1.5 rounded-lg hover:bg-primary-50 text-primary-600 transition" title="Editar">
                        <i data-lucide="pencil" class="w-4 h-4"></i>
                    </button>
                    <button onclick="eliminarUsuario(${u.ID_usuario}, '${u.nombre}')" class="p-1.5 rounded-lg hover:bg-danger-50 text-danger-500 transition" title="Eliminar">
                        <i data-lucide="trash-2" class="w-4 h-4"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');

    const count = document.getElementById('usuariosCount');
    if (count) count.textContent = `(${usuarios.length})`;
    lucide.createIcons();
}

async function guardarUsuario() {
    const idEdit = document.getElementById('usuarioIdEdit').value;
    const nombre = document.getElementById('usuarioNombre').value.trim();
    const email = document.getElementById('usuarioEmail').value.trim();
    const password = document.getElementById('usuarioPassword').value;
    const ID_rol = parseInt(document.getElementById('usuarioRol').value);
    const ID_cliente = document.getElementById('usuarioCliente').value || null;
    const estado = document.getElementById('usuarioEstado').value;

    if (!nombre || !email) {
        showToast('Los campos Nombre y Email son obligatorios', 'warning');
        return;
    }

    if (idEdit) {
        const body = { nombre, email, ID_rol, ID_cliente: ID_cliente ? parseInt(ID_cliente) : null, estado };
        if (password) body.password = password;
        try { await api(`/usuarios/${idEdit}`, { method: 'PUT', body }); showToast('Usuario actualizado', 'success'); }
        catch (e) { return; }
    } else {
        if (!password || password.length < 4) {
            showToast('La contraseña debe tener al menos 4 caracteres', 'warning');
            return;
        }
        try {
            await api('/usuarios', { method: 'POST', body: { nombre, email, password, ID_rol, ID_cliente: ID_cliente ? parseInt(ID_cliente) : null, estado } });
            showToast('Usuario creado correctamente', 'success');
        } catch (e) { return; }
    }
    limpiarFormularioUsuario();
    toggleUsuarioForm();
    cargarUsuariosDesdeAPI();
}

async function editarUsuario(id) {
    try {
        const usuario = await api(`/usuarios/${id}`);
        document.getElementById('usuarioIdEdit').value = usuario.ID_usuario;
        document.getElementById('usuarioNombre').value = usuario.nombre;
        document.getElementById('usuarioEmail').value = usuario.email;
        document.getElementById('usuarioPassword').value = '';
        document.getElementById('usuarioEstado').value = usuario.estado;
        document.getElementById('usuarioFormTitle').textContent = 'Editar Usuario';
        await cargarSelectsUsuarios();
        if (usuario.ID_rol) document.getElementById('usuarioRol').value = usuario.ID_rol;
        if (usuario.ID_cliente) document.getElementById('usuarioCliente').value = usuario.ID_cliente;
        toggleUsuarioForm();
    } catch (e) { /* toast ya mostrado */ }
}

async function eliminarUsuario(id, nombre) {
    if (!confirm(`¿Eliminar al usuario "${nombre}"?`)) return;
    try {
        await api(`/usuarios/${id}`, { method: 'DELETE' });
        showToast('Usuario eliminado', 'success');
        cargarUsuariosDesdeAPI();
    } catch (e) { /* toast ya mostrado */ }
}

function limpiarFormularioUsuario() {
    document.getElementById('usuarioIdEdit').value = '';
    document.getElementById('usuarioNombre').value = '';
    document.getElementById('usuarioEmail').value = '';
    document.getElementById('usuarioPassword').value = '';
    document.getElementById('usuarioEstado').value = 'activo';
    document.getElementById('usuarioFormTitle').textContent = 'Registrar Nuevo Usuario';
}


// ================================================================
// MÓDULO 3: PARQUE DE IMPRESORAS — ACCIONES
// ================================================================

/**
 * Muestra los detalles de una impresora en un toast.
 */
async function verImpresora(id) {
    try {
        const imp = await api(`/impresoras/${id}`);
        const estado = imp.estado_actual || '—';
        const garantia = imp.termino_garantia ? `Hasta ${imp.termino_garantia}` : 'Sin fecha';
        showToast(`${imp.marca} ${imp.modelo} | Serie: ${imp.num_serie} | Estado: ${estado} | Garantía: ${garantia}`, 'info');
    } catch (e) { /* toast ya mostrado */ }
}

/**
 * Abre el formulario para editar una impresora (pre-carga los datos).
 */
async function editarImpresora(id) {
    showToast('Función de edición de impresora en desarrollo', 'info');
}

/**
 * Elimina una impresora con confirmación.
 */
async function eliminarImpresora(id, nombre) {
    if (!confirm(`¿Eliminar la impresora "${nombre}"?\n\nSe perderán todos los registros asociados.`)) return;
    try {
        await api(`/impresoras/${id}`, { method: 'DELETE' });
        showToast('Impresora eliminada correctamente', 'success');
    } catch (e) { /* toast ya mostrado */ }
}


// ================================================================
// MÓDULO 6: CONFIGURACIÓN DEL SISTEMA
// ================================================================

/**
 * Guarda los datos de la empresa en localStorage.
 * (En producción se guardarían en una tabla de configuración de la BD)
 */
function guardarConfigEmpresa() {
    const config = {
        nombreEmpresa: document.getElementById('cfgNombreEmpresa').value,
        rutEmpresa: document.getElementById('cfgRutEmpresa').value,
        telefono: document.getElementById('cfgTelefono').value,
        direccion: document.getElementById('cfgDireccion').value,
        email: document.getElementById('cfgEmail').value,
    };
    localStorage.setItem('mps_config_empresa', JSON.stringify(config));
    showToast('Datos de empresa guardados correctamente', 'success');
}

/**
 * Cambia la contraseña del usuario actual.
 * Valida que las contraseñas coincidan y llamen al endpoint.
 */
async function cambiarPassword() {
    const passActual = document.getElementById('cfgPassActual').value;
    const passNueva = document.getElementById('cfgPassNueva').value;
    const passConfirm = document.getElementById('cfgPassConfirm').value;

    if (!passActual || !passNueva || !passConfirm) {
        showToast('Completa todos los campos de contraseña', 'warning');
        return;
    }
    if (passNueva.length < 4) {
        showToast('La nueva contraseña debe tener al menos 4 caracteres', 'warning');
        return;
    }
    if (passNueva !== passConfirm) {
        showToast('Las contraseñas nuevas no coinciden', 'error');
        return;
    }

    const userData = JSON.parse(localStorage.getItem('mps_user') || '{}');
    try {
        await api(`/usuarios/${userData.ID_usuario}`, {
            method: 'PUT',
            body: { password: passNueva }
        });
        // Actualizar la contraseña en la BD con la actual para que funcione el login
        showToast('Contraseña cambiada correctamente', 'success');
        document.getElementById('cfgPassActual').value = '';
        document.getElementById('cfgPassNueva').value = '';
        document.getElementById('cfgPassConfirm').value = '';
    } catch (e) {
        // El toast ya se mostró en api()
    }
}


// ================================================================
// PAGINACIÓN: PARQUE DE IMPRESORAS
// ================================================================

let paginaActual = 1;
const POR_PAGINA = 5;
const TOTAL_EQUIPOS = 8;
const TOTAL_PAGINAS = Math.ceil(TOTAL_EQUIPOS / POR_PAGINA);

/**
 * Cambia la página de la tabla de impresoras.
 * @param {number|string} accion - Número de página, 'prev' o 'next'
 */
function cambiarPagImpresoras(accion) {
    const rows = document.querySelectorAll('.impresora-row');
    if (!rows.length) return;

    if (accion === 'prev') {
        if (paginaActual > 1) paginaActual--;
    } else if (accion === 'next') {
        if (paginaActual < TOTAL_PAGINAS) paginaActual++;
    } else if (typeof accion === 'number') {
        paginaActual = accion;
    }

    // Actualizar visibilidad de filas
    rows.forEach(row => {
        const page = parseInt(row.dataset.page);
        row.style.display = (page === paginaActual) ? '' : 'none';
    });

    // Actualizar texto informativo
    const desde = (paginaActual - 1) * POR_PAGINA + 1;
    const hasta = Math.min(paginaActual * POR_PAGINA, TOTAL_EQUIPOS);
    const info = document.getElementById('impresorasInfo');
    if (info) info.textContent = `Mostrando ${desde}-${hasta} de ${TOTAL_EQUIPOS} equipos`;

    // Actualizar botones
    const prevBtn = document.getElementById('pagPrevBtn');
    const nextBtn = document.getElementById('pagNextBtn');
    
    if (prevBtn) {
        prevBtn.disabled = paginaActual <= 1;
        prevBtn.classList.toggle('cursor-not-allowed', paginaActual <= 1);
        prevBtn.classList.toggle('text-slate-400', paginaActual <= 1);
        prevBtn.classList.toggle('text-slate-600', paginaActual > 1);
        prevBtn.classList.toggle('hover:bg-slate-200', paginaActual > 1);
    }
    if (nextBtn) {
        nextBtn.disabled = paginaActual >= TOTAL_PAGINAS;
        nextBtn.classList.toggle('cursor-not-allowed', paginaActual >= TOTAL_PAGINAS);
        nextBtn.classList.toggle('text-slate-400', paginaActual >= TOTAL_PAGINAS);
        nextBtn.classList.toggle('text-slate-600', paginaActual < TOTAL_PAGINAS);
        nextBtn.classList.toggle('hover:bg-slate-200', paginaActual < TOTAL_PAGINAS);
    }

    // Actualizar botones de página
    for (let i = 1; i <= TOTAL_PAGINAS; i++) {
        const btn = document.getElementById(`pagBtn${i}`);
        if (btn) {
            btn.classList.toggle('bg-primary-600', paginaActual === i);
            btn.classList.toggle('text-white', paginaActual === i);
            btn.classList.toggle('font-semibold', paginaActual === i);
            btn.classList.toggle('bg-slate-100', paginaActual !== i);
            btn.classList.toggle('text-slate-600', paginaActual !== i);
        }
    }

    lucide.createIcons();
}

// Inicializar paginación al cargar
document.addEventListener('DOMContentLoaded', () => {
    // Si ya hay un DOMContentLoaded listener, esto se ejecutará después
    setTimeout(() => cambiarPagImpresoras(1), 100);
});

// ================================================================
// UTILIDADES
// ================================================================

function formatCurrency(amount) {
    return `$${amount.toLocaleString('es-CL')}`;
}

function formatNumber(num) {
    return num.toLocaleString('es-CL');
}
