/**
 * Aplicación de chat con Agentes IA
 */

// Estado de la aplicación
const appState = {
    conversations: [],
    currentConversationId: null,
    messages: [],
    isProcessing: false,
    documents: [],
    darkMode: localStorage.getItem('darkMode') === 'true',
    activeAgents: {
        supervisor: false,
        researcher: false,
        analyst: false,
        communicator: false
    },
    sidebarVisible: false,
    processingSteps: {
        retrieveContext: { status: 'pending', content: '' },
        supervisor: { status: 'pending', content: '' },
        researcher: { status: 'pending', content: '' },
        analyst: { status: 'pending', content: '' },
        communicator: { status: 'pending', content: '' }
    }
};

// Elementos DOM
const elements = {
    chatMessages: document.getElementById('chatMessages'),
    messageForm: document.getElementById('messageForm'),
    userInput: document.getElementById('userInput'),
    newChatBtn: document.getElementById('newChatBtn'),
    uploadDocBtn: document.getElementById('uploadDocBtn'),
    browseDocsBtn: document.getElementById('browseDocsBtn'),
    saveDocBtn: document.getElementById('saveDocBtn'),
    docSearchBtn: document.getElementById('docSearchBtn'),
    conversationList: document.getElementById('conversationList'),
    workflowContainer: document.getElementById('workflowContainer'),
    agentDetailsPanel: document.getElementById('agentDetailsPanel'),
    documentContextPanel: document.getElementById('documentContextPanel'),
    contextDocumentsContainer: document.getElementById('contextDocumentsContainer'),
    hideContextBtn: document.getElementById('hideContextBtn'),
    themeToggle: document.getElementById('themeToggle'),
    sidebar: document.getElementById('sidebar'),
    mobileNavToggle: document.getElementById('mobileNavToggle'),
    documentsList: document.getElementById('documentsList'),
    deleteDocBtn: document.getElementById('deleteDocBtn'),
    mainContent: document.getElementById('mainContent'),
    agentSidebar: document.getElementById('agentSidebar'),
    closeSidebarBtn: document.getElementById('closeSidebarBtn'),
    agentToggle: document.getElementById('agentToggle'),
    toggleDetailsBtn: document.getElementById('toggleDetailsBtn'),
    timelineItems: {
        retrieveContext: document.getElementById('timelineRetrieveContext'),
        supervisor: document.getElementById('timelineSupervisor'),
        researcher: document.getElementById('timelineResearcher'),
        analyst: document.getElementById('timelineAnalyst'),
        communicator: document.getElementById('timelineCommunicator')
    },
    timelineContents: {
        retrieveContext: document.getElementById('retrieveContextContent'),
        supervisor: document.getElementById('supervisorTimelineContent'),
        researcher: document.getElementById('researcherTimelineContent'),
        analyst: document.getElementById('analystTimelineContent'),
        communicator: document.getElementById('communicatorTimelineContent')
    },
    agentBadges: {
        supervisor: document.getElementById('supervisorBadge'),
        researcher: document.getElementById('researcherBadge'),
        analyst: document.getElementById('analystBadge'),
        communicator: document.getElementById('communicatorBadge')
    },
    agentPanels: {
        supervisor: document.getElementById('supervisorContent'),
        researcher: document.getElementById('researcherContent'),
        analyst: document.getElementById('analystContent'),
        communicator: document.getElementById('communicatorContent')
    }
};

// Modales
const modals = {
    uploadDoc: new bootstrap.Modal(document.getElementById('uploadDocModal')),
    browseDocs: new bootstrap.Modal(document.getElementById('browseDocsModal')),
    viewDoc: new bootstrap.Modal(document.getElementById('viewDocModal'))
};

/**
 * Inicializa la aplicación.
 */
function initApp() {
    // Inicializar tema
    if (appState.darkMode) {
        document.documentElement.setAttribute('data-theme', 'dark');
        elements.themeToggle.innerHTML = '<i class="bi bi-sun"></i>';
    }
    
    // Crear una nueva conversación al iniciar
    createNewConversation();
    
    // Añadir event listeners
    elements.messageForm.addEventListener('submit', handleMessageSubmit);
    elements.newChatBtn.addEventListener('click', createNewConversation);
    elements.uploadDocBtn.addEventListener('click', () => modals.uploadDoc.show());
    elements.browseDocsBtn.addEventListener('click', () => {
        loadDocuments();
        modals.browseDocs.show();
    });
    elements.saveDocBtn.addEventListener('click', handleDocumentUpload);
    elements.docSearchBtn.addEventListener('click', handleDocumentSearch);
    elements.themeToggle.addEventListener('click', toggleDarkMode);
    elements.mobileNavToggle.addEventListener('click', toggleMobileNav);
    elements.hideContextBtn.addEventListener('click', () => {
        elements.documentContextPanel.classList.add('d-none');
    });
    elements.deleteDocBtn.addEventListener('click', () => {
        const docId = elements.deleteDocBtn.dataset.documentId;
        if (docId) {
            deleteDocument(docId);
        }
    });
    
    // Nuevos event listeners para el panel lateral
    elements.agentToggle.addEventListener('click', toggleAgentSidebar);
    elements.closeSidebarBtn.addEventListener('click', toggleAgentSidebar);
    elements.toggleDetailsBtn.addEventListener('click', toggleAgentDetailsPanel);
    
    // Auto-ajuste de altura para el textarea
    elements.userInput.addEventListener('input', () => {
        elements.userInput.style.height = 'auto';
        elements.userInput.style.height = (elements.userInput.scrollHeight) + 'px';
    });

    // Detectar clic fuera del sidebar en móvil para cerrarlo
    document.addEventListener('click', (event) => {
        if (window.innerWidth < 768 && 
            elements.sidebar.classList.contains('show') && 
            !elements.sidebar.contains(event.target) &&
            event.target !== elements.mobileNavToggle) {
            elements.sidebar.classList.remove('show');
        }
    });
}

/**
 * Cambia entre modo claro y oscuro
 */
function toggleDarkMode() {
    appState.darkMode = !appState.darkMode;
    
    if (appState.darkMode) {
        document.documentElement.setAttribute('data-theme', 'dark');
        elements.themeToggle.innerHTML = '<i class="bi bi-sun"></i>';
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        elements.themeToggle.innerHTML = '<i class="bi bi-moon"></i>';
    }
    
    localStorage.setItem('darkMode', appState.darkMode);
}

/**
 * Muestra/oculta la navegación en móvil
 */
function toggleMobileNav() {
    elements.sidebar.classList.toggle('show');
}

/**
 * Muestra/oculta el panel lateral de agentes
 */
function toggleAgentSidebar() {
    appState.sidebarVisible = !appState.sidebarVisible;
    
    if (appState.sidebarVisible) {
        elements.agentSidebar.classList.remove('d-none');
        elements.agentToggle.classList.add('active');
        // Ajustar el ancho del área de contenido principal
        if (window.innerWidth >= 768) {
            elements.mainContent.classList.remove('col-md-9', 'col-lg-10');
            elements.mainContent.classList.add('col-md-6', 'col-lg-7');
        }
    } else {
        elements.agentSidebar.classList.add('d-none');
        elements.agentToggle.classList.remove('active');
        // Restaurar el ancho del área de contenido principal
        if (window.innerWidth >= 768) {
            elements.mainContent.classList.remove('col-md-6', 'col-lg-7');
            elements.mainContent.classList.add('col-md-9', 'col-lg-10');
        }
    }
}

/**
 * Muestra/oculta el panel de detalles completos de agentes
 */
function toggleAgentDetailsPanel() {
    elements.agentDetailsPanel.classList.toggle('d-none');
    const isVisible = !elements.agentDetailsPanel.classList.contains('d-none');
    
    elements.toggleDetailsBtn.innerHTML = isVisible ? 
        '<i class="bi bi-eye-slash me-1"></i> Ocultar Detalles Completos' : 
        '<i class="bi bi-info-circle me-1"></i> Ver Detalles Completos';
}

/**
 * Actualiza el estado visual de los indicadores de agentes
 * @param {string} agent - Nombre del agente
 * @param {boolean} active - Estado activo
 */
function updateAgentIndicator(agent, active) {
    appState.activeAgents[agent] = active;
    
    if (active) {
        elements.agentBadges[agent].classList.add('agent-active');
    } else {
        elements.agentBadges[agent].classList.remove('agent-active');
    }
}

/**
 * Actualiza el estado de un paso en la línea de tiempo
 * @param {string} step - ID del paso (retrieveContext, supervisor, etc)
 * @param {string} status - Estado (pending, processing, completed, error)
 * @param {string} content - Contenido a mostrar
 */
function updateTimelineStep(step, status, content = '') {
    // Actualizar estado en el modelo
    appState.processingSteps[step] = {
        status: status,
        content: content || appState.processingSteps[step].content
    };
    
    // Actualizar UI
    const timelineItem = elements.timelineItems[step];
    const timelineContent = elements.timelineContents[step];
    
    // Limpiar estados anteriores
    timelineItem.classList.remove('pending', 'processing', 'completed', 'error', 'active');
    
    // Aplicar nuevo estado
    timelineItem.classList.add(status);
    if (status === 'processing') {
        timelineItem.classList.add('active');
    }
    
    // Actualizar contenido
    if (content) {
        if (status === 'pending') {
            timelineContent.innerHTML = `<div class="timeline-status">Pendiente</div>`;
        } else if (status === 'processing') {
            timelineContent.innerHTML = `
                <div class="timeline-status">Procesando...</div>
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `;
        } else if (status === 'completed') {
            // Formatear el contenido con markdown básico
            const formattedContent = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                           .replace(/\*(.*?)\*/g, '<em>$1</em>')
                                           .replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>')
                                           .replace(/`(.*?)`/g, '<code>$1</code>')
                                           .replace(/\n/g, '<br>');
                                           
            timelineContent.innerHTML = formattedContent;
        } else if (status === 'error') {
            timelineContent.innerHTML = `<div class="timeline-status error">Error: ${content}</div>`;
        }
    }
    
    // Mostrar el panel lateral si no está visible
    if (!appState.sidebarVisible && status === 'processing') {
        toggleAgentSidebar();
    }
}

/**
 * Resetea todos los pasos de la línea de tiempo
 */
function resetTimelineSteps() {
    updateTimelineStep('retrieveContext', 'pending');
    updateTimelineStep('supervisor', 'pending');
    updateTimelineStep('researcher', 'pending');
    updateTimelineStep('analyst', 'pending');
    updateTimelineStep('communicator', 'pending');
}

/**
 * Resetea todos los indicadores de agentes a inactivo
 */
function resetAgentIndicators() {
    updateAgentIndicator('supervisor', false);
    updateAgentIndicator('researcher', false);
    updateAgentIndicator('analyst', false);
    updateAgentIndicator('communicator', false);
}

/**
 * Crea una nueva conversación.
 */
function createNewConversation() {
    // Generar ID para la conversación
    const conversationId = Date.now().toString();
    
    // Crear objeto de conversación
    const conversation = {
        id: conversationId,
        title: `Conversación ${appState.conversations.length + 1}`,
        timestamp: new Date().toISOString()
    };
    
    // Añadir a la lista de conversaciones
    appState.conversations.unshift(conversation);
    
    // Establecer como conversación actual
    appState.currentConversationId = conversationId;
    appState.messages = [];
    
    // Actualizar UI
    updateConversationList();
    clearChatMessages();
    
    // Añadir mensaje de bienvenida
    addSystemMessage('Bienvenido al asistente de empresa con Agentes IA. ¿En qué puedo ayudarte hoy?');
    
    // Ocultar paneles
    elements.workflowContainer.classList.add('d-none');
    elements.agentDetailsPanel.classList.add('d-none');
    elements.documentContextPanel.classList.add('d-none');
    elements.agentToggle.classList.add('d-none');
    
    // Reiniciar estado
    resetAgentIndicators();
    resetTimelineSteps();
    
    // Si está abierto el panel lateral, cerrarlo
    if (appState.sidebarVisible) {
        toggleAgentSidebar();
    }
    
    // En móvil, cerrar el sidebar
    if (window.innerWidth < 768) {
        elements.sidebar.classList.remove('show');
    }
}

/**
 * Actualiza la lista de conversaciones en la UI.
 */
function updateConversationList() {
    elements.conversationList.innerHTML = '';
    
    appState.conversations.forEach(conversation => {
        const conversationItem = document.createElement('div');
        conversationItem.className = `conversation-item ${conversation.id === appState.currentConversationId ? 'active' : ''}`;
        conversationItem.dataset.id = conversation.id;
        
        const date = new Date(conversation.timestamp);
        const formattedDate = date.toLocaleDateString();
        
        conversationItem.innerHTML = `
            <div>${conversation.title}</div>
            <small>${formattedDate}</small>
        `;
        
        conversationItem.addEventListener('click', () => loadConversation(conversation.id));
        
        elements.conversationList.appendChild(conversationItem);
    });
}

/**
 * Carga una conversación existente.
 * @param {string} conversationId - ID de la conversación a cargar
 */
function loadConversation(conversationId) {
    // Establecer como conversación actual
    appState.currentConversationId = conversationId;
    
    // Cargar mensajes (en una app real, se cargarían desde el servidor)
    appState.messages = []; // Aquí cargaríamos los mensajes del servidor
    
    // Actualizar UI
    updateConversationList();
    clearChatMessages();
    
    // Añadir mensaje de bienvenida
    addSystemMessage('Conversación cargada. Continúa tu chat con los agentes IA.');
    
    // Ocultar paneles
    elements.workflowContainer.classList.add('d-none');
    elements.agentDetailsPanel.classList.add('d-none');
    elements.documentContextPanel.classList.add('d-none');
    elements.agentToggle.classList.add('d-none');
    
    // Reiniciar estado
    resetAgentIndicators();
    resetTimelineSteps();
    
    // Si está abierto el panel lateral, cerrarlo
    if (appState.sidebarVisible) {
        toggleAgentSidebar();
    }
    
    // En móvil, cerrar el sidebar
    if (window.innerWidth < 768) {
        elements.sidebar.classList.remove('show');
    }
}

/**
 * Limpia los mensajes del chat en la UI.
 */
function clearChatMessages() {
    elements.chatMessages.innerHTML = '';
}

/**
 * Maneja el envío de un mensaje.
 * @param {Event} event - Evento de submit
 */
function handleMessageSubmit(event) {
    event.preventDefault();
    
    const message = elements.userInput.value.trim();
    if (!message || appState.isProcessing) return;
    
    // Añadir mensaje del usuario a la UI
    addUserMessage(message);
    
    // Limpiar campo de entrada
    elements.userInput.value = '';
    elements.userInput.style.height = 'auto';
    
    // Procesar mensaje
    processUserMessage(message);
}

/**
 * Añade un mensaje del usuario a la UI.
 * @param {string} message - Texto del mensaje
 */
function addUserMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'user-message';
    
    const currentTime = new Date();
    const formattedTime = currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageElement.innerHTML = `
        <div class="message-content">${message}</div>
        <div class="message-meta">
            <div></div>
            <div class="message-time">${formattedTime}</div>
        </div>
    `;
    
    elements.chatMessages.appendChild(messageElement);
    scrollToBottom();
    
    // Guardar mensaje en el estado
    appState.messages.push({
        content: message,
        type: 'human',
        sender: 'user',
        timestamp: currentTime.toISOString()
    });
}

/**
 * Añade un mensaje del sistema a la UI.
 * @param {string} message - Texto del mensaje
 */
function addSystemMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'system-message';
    
    messageElement.innerHTML = `
        <div class="message-content">${message}</div>
    `;
    
    elements.chatMessages.appendChild(messageElement);
    scrollToBottom();
    
    // Guardar mensaje en el estado
    appState.messages.push({
        content: message,
        type: 'system',
        sender: 'system',
        timestamp: new Date().toISOString()
    });
}

/**
 * Añade un mensaje de IA a la UI.
 * @param {string} message - Texto del mensaje
 * @param {Array} sources - Fuentes de información
 */
function addAIMessage(message, sources = []) {
    const messageElement = document.createElement('div');
    messageElement.className = 'ai-message';
    
    const currentTime = new Date();
    const formattedTime = currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Procesamiento básico de markdown para el contenido
    const formattedMessage = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                   .replace(/\*(.*?)\*/g, '<em>$1</em>')
                                   .replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>')
                                   .replace(/`(.*?)`/g, '<code>$1</code>')
                                   .replace(/\n/g, '<br>');
    
    let sourcesHTML = '';
    if (sources && sources.length > 0) {
        sourcesHTML = '<div class="message-sources">';
        sources.forEach(source => {
            if (source && source !== 'undefined') {
                sourcesHTML += `<span class="source-badge" onclick="viewDocument('${source}')">${source.substring(0, 8)}</span>`;
            }
        });
        sourcesHTML += '</div>';
    }
    
    messageElement.innerHTML = `
        <div class="message-content">${formattedMessage}</div>
        ${sourcesHTML}
        <div class="message-meta">
            <div></div>
            <div class="message-time">${formattedTime}</div>
        </div>
    `;
    
    // Reemplazar el indicador de carga si existe
    const loadingIndicator = document.querySelector('.loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
    
    elements.chatMessages.appendChild(messageElement);
    scrollToBottom();
    
    // Guardar mensaje en el estado
    appState.messages.push({
        content: message,
        type: 'ai',
        sender: 'assistant',
        sources: sources,
        timestamp: currentTime.toISOString()
    });
}

/**
 * Scroll al fondo del chat
 */
function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

/**
 * Añade un indicador de carga.
 */
function addLoadingIndicator() {
    const loadingElement = document.createElement('div');
    loadingElement.className = 'ai-message loading-indicator';
    
    loadingElement.innerHTML = `
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    
    elements.chatMessages.appendChild(loadingElement);
    scrollToBottom();
}

/**
 * Procesa un mensaje del usuario.
 * @param {string} message - Mensaje del usuario
 */
async function processUserMessage(message) {
    try {
        // Iniciar procesamiento
        appState.isProcessing = true;
        
        // Mostrar indicador de carga
        addLoadingIndicator();
        
        // Mostrar el botón de agentes
        elements.agentToggle.classList.remove('d-none');
        
        // Mostrar panel de flujo de trabajo
        elements.workflowContainer.classList.remove('d-none');
        
        // Iniciar procesamiento en la línea de tiempo
        resetTimelineSteps();
        
        // Paso 1: Recuperación de contexto
        updateTimelineStep('retrieveContext', 'processing', 'Buscando documentos relevantes...');
        
        // Preparar contexto de la conversación
        const context = appState.messages.map(msg => ({
            content: msg.content,
            type: msg.type,
            sender: msg.sender
        }));
        
        // Enviar solicitud al servidor
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: message,
                context: context
            })
        });
        
        if (!response.ok) {
            throw new Error('Error al procesar la consulta');
        }
        
        const data = await response.json();
        
        // Actualizar estado de recuperación de contexto
        if (data.context_documents && data.context_documents.length > 0) {
            updateTimelineStep('retrieveContext', 'completed', 
                `Encontrados ${data.context_documents.length} documentos relevantes.`);
            
            // Mostrar documentos de contexto
            updateContextDocuments(data.context_documents);
            elements.documentContextPanel.classList.remove('d-none');
        } else {
            updateTimelineStep('retrieveContext', 'completed', 
                'No se encontraron documentos relevantes para esta consulta.');
        }
        
        // Procesar respuestas de los agentes
        updateAgentResponses(data.agent_responses);
        
        // Añadir respuesta del asistente
        addAIMessage(data.response, Object.values(data.agent_responses).flatMap(ar => ar.sources || []));
        
    } catch (error) {
        console.error('Error:', error);
        addSystemMessage(`Error: ${error.message}`);
        
        // Marcar error en todos los pasos pendientes
        Object.keys(appState.processingSteps).forEach(step => {
            if (appState.processingSteps[step].status === 'processing') {
                updateTimelineStep(step, 'error', error.message);
            }
        });
        
        // Desactivar todos los indicadores
        resetAgentIndicators();
        
    } finally {
        // Finalizar procesamiento
        appState.isProcessing = false;
    }
}

/**
 * Actualiza las respuestas de los agentes en la UI y línea de tiempo
 * @param {Object} agentResponses - Respuestas de los agentes
 */
function updateAgentResponses(agentResponses) {
    // Limpiar paneles
    Object.values(elements.agentPanels).forEach(panel => {
        panel.innerHTML = '';
    });
    
    console.log("Respuestas de agentes recibidas:", agentResponses);
    
    // Verificar estructura de la respuesta y normalizar nombre de roles
    const normalizedResponses = {};
    for (const [role, response] of Object.entries(agentResponses)) {
        // Convertir a minúsculas para normalizar
        let normalizedRole = role.toLowerCase();
        // Manejar casos como "SUPERVISOR", "Supervisor", etc.
        if (normalizedRole.includes('supervisor')) normalizedRole = 'supervisor';
        if (normalizedRole.includes('researcher') || normalizedRole.includes('investigador')) normalizedRole = 'researcher';
        if (normalizedRole.includes('analyst') || normalizedRole.includes('analista')) normalizedRole = 'analyst';
        if (normalizedRole.includes('communicator') || normalizedRole.includes('comunicador')) normalizedRole = 'communicator';
        
        normalizedResponses[normalizedRole] = response;
    }
    
    console.log("Respuestas normalizadas:", normalizedResponses);
    
    // Actualizar cada panel de agente
    const roleMapping = {
        'supervisor': { id: 'supervisor', title: 'Evaluando la consulta...' },
        'researcher': { id: 'researcher', title: 'Investigando información...' },
        'analyst': { id: 'analyst', title: 'Analizando resultados...' },
        'communicator': { id: 'communicator', title: 'Formulando respuesta final...' }
    };
    
    // Actualizar los pasos de la línea de tiempo para todos los agentes presentes en la respuesta
    Object.entries(roleMapping).forEach(([role, info], index) => {
        const response = normalizedResponses[role] || agentResponses[role.toUpperCase()];
        
        if (response) {
            const timelineId = info.id;
            const panelId = info.id;
            const delay = 1000 + (index * 500); // Escalonamiento en la animación
            
            // Actualizar el estado a "procesando"
            updateTimelineStep(timelineId, 'processing', info.title);
            updateAgentIndicator(panelId, true);
            
            // Simular el tiempo de procesamiento y luego marcar como completado
            setTimeout(() => {
                updateTimelineStep(timelineId, 'completed', response.content);
                updateAgentIndicator(panelId, false);
                
                // Formatear contenido con markdown básico para el panel de detalles
                const formattedContent = response.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                                   .replace(/\*(.*?)\*/g, '<em>$1</em>')
                                                   .replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>')
                                                   .replace(/`(.*?)`/g, '<code>$1</code>')
                                                   .replace(/\n/g, '<br>');
                
                // Añadir fuentes si hay
                let sourcesHTML = '';
                if (response.sources && response.sources.length > 0) {
                    sourcesHTML = '<div class="mt-3"><strong>Fuentes:</strong><ul>';
                    response.sources.forEach(source => {
                        if (source && source !== 'undefined') {
                            sourcesHTML += `<li><a href="#" onclick="viewDocument('${source}'); return false;">${source}</a></li>`;
                        }
                    });
                    sourcesHTML += '</ul></div>';
                }
                
                // Actualizar panel de detalles
                if (elements.agentPanels[panelId]) {
                    elements.agentPanels[panelId].innerHTML = `
                        <div>${formattedContent}</div>
                        ${sourcesHTML}
                    `;
                }
            }, delay);
        }
    });
}

/**
 * Actualiza el panel de documentos de contexto
 * @param {Array} documents - Lista de documentos 
 */
function updateContextDocuments(documents) {
    elements.contextDocumentsContainer.innerHTML = '';
    
    documents.forEach(doc => {
        const docElement = document.createElement('div');
        docElement.className = 'doc-card';
        docElement.innerHTML = `
            <div class="doc-card-title">${doc.title}</div>
            <div class="doc-card-type">${getDocumentTypeLabel(doc.document_type)}</div>
            <div class="doc-card-content">${doc.snippet}</div>
        `;
        
        docElement.addEventListener('click', () => viewDocument(doc.id));
        elements.contextDocumentsContainer.appendChild(docElement);
    });
}

/**
 * Obtiene una etiqueta legible para el tipo de documento
 * @param {string} type - Tipo de documento
 * @returns {string} Etiqueta legible
 */
function getDocumentTypeLabel(type) {
    const types = {
        'policy': 'Política',
        'procedure': 'Procedimiento',
        'manual': 'Manual',
        'guide': 'Guía',
        'report': 'Informe',
        'other': 'Otro'
    };
    
    return types[type] || type;
}

/**
 * Carga documentos desde el servidor.
 */
async function loadDocuments() {
    try {
        const response = await fetch('/api/documents/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: '',
                limit: 50
            })
        });
        
        if (!response.ok) {
            throw new Error('Error al cargar documentos');
        }
        
        const data = await response.json();
        
        // Actualizar estado
        appState.documents = data.results || [];
        
        // Actualizar UI
        updateDocumentsList();
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error al cargar documentos: ${error.message}`);
    }
}

/**
 * Actualiza la lista de documentos en la modal.
 */
function updateDocumentsList() {
    elements.documentsList.innerHTML = '';
    
    if (appState.documents.length === 0) {
        elements.documentsList.innerHTML = '<p class="text-center">No hay documentos disponibles.</p>';
        return;
    }
    
    appState.documents.forEach(doc => {
        const docElement = document.createElement('div');
        docElement.className = 'doc-card';
        
        docElement.innerHTML = `
            <div class="doc-card-title">${doc.title}</div>
            <div class="doc-card-type">${getDocumentTypeLabel(doc.document_type)}</div>
            <div class="doc-card-content">${doc.content.substring(0, 150)}${doc.content.length > 150 ? '...' : ''}</div>
        `;
        
        docElement.addEventListener('click', () => {
            modals.browseDocs.hide();
            viewDocument(doc.id);
        });
        
        elements.documentsList.appendChild(docElement);
    });
}

/**
 * Maneja la búsqueda de documentos.
 */
async function handleDocumentSearch() {
    try {
        const searchQuery = document.getElementById('docSearchInput').value.trim();
        
        if (!searchQuery) {
            loadDocuments();
            return;
        }
        
        const response = await fetch('/api/documents/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: searchQuery,
                limit: 50
            })
        });
        
        if (!response.ok) {
            throw new Error('Error al buscar documentos');
        }
        
        const data = await response.json();
        
        // Actualizar estado
        appState.documents = data.results || [];
        
        // Actualizar UI
        updateDocumentsList();
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error al buscar documentos: ${error.message}`);
    }
}

/**
 * Maneja la subida de un documento.
 */
async function handleDocumentUpload() {
    try {
        const title = document.getElementById('docTitle').value.trim();
        const type = document.getElementById('docType').value;
        const content = document.getElementById('docContent').value.trim();
        const source = document.getElementById('docSource').value.trim();
        
        if (!title || !content) {
            alert('Por favor completa los campos requeridos');
            return;
        }
        
        const docData = {
            title: title,
            document_type: type,
            content: content,
            source: source || 'user_upload'
        };
        
        const response = await fetch('/api/documents', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(docData)
        });
        
        if (!response.ok) {
            throw new Error('Error al subir documento');
        }
        
        // Cerrar modal y limpiar campos
        modals.uploadDoc.hide();
        document.getElementById('docTitle').value = '';
        document.getElementById('docType').value = 'policy';
        document.getElementById('docContent').value = '';
        document.getElementById('docSource').value = '';
        
        // Mostrar mensaje de éxito
        addSystemMessage('Documento subido correctamente');
        
        // Actualizar lista de documentos
        await loadDocuments();
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error al subir documento: ${error.message}`);
    }
}

/**
 * Visualiza un documento.
 * @param {string} documentId - ID del documento
 */
async function viewDocument(documentId) {
    try {
        // Buscar el documento en el estado o cargarlo del servidor
        let document = appState.documents.find(doc => doc.id === documentId);
        
        if (!document) {
            const response = await fetch('/api/documents/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    document_id: documentId
                })
            });
            
            if (!response.ok) {
                throw new Error('Error al cargar documento');
            }
            
            const data = await response.json();
            document = data.results && data.results.length > 0 ? data.results[0] : null;
        }
        
        if (!document) {
            throw new Error('Documento no encontrado');
        }
        
        // Configurar modal de visualización
        document.getElementById('viewDocTitle').textContent = document.title;
        document.getElementById('viewDocType').textContent = getDocumentTypeLabel(document.document_type);
        document.getElementById('viewDocSource').textContent = `Fuente: ${document.source || 'Desconocida'}`;
        document.getElementById('viewDocContent').innerHTML = document.content.replace(/\n/g, '<br>');
        
        // Configurar botón de eliminar
        elements.deleteDocBtn.dataset.documentId = document.id;
        
        // Mostrar modal
        modals.viewDoc.show();
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error al visualizar documento: ${error.message}`);
    }
}

/**
 * Elimina un documento.
 * @param {string} documentId - ID del documento
 */
async function deleteDocument(documentId) {
    try {
        const response = await fetch(`/api/documents/${documentId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Error al eliminar documento');
        }
        
        // Cerrar modal
        modals.viewDoc.hide();
        
        // Mostrar mensaje de éxito
        addSystemMessage('Documento eliminado correctamente');
        
        // Actualizar lista de documentos
        await loadDocuments();
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error al eliminar documento: ${error.message}`);
    }
}

// Inicializar la aplicación al cargar la página
document.addEventListener('DOMContentLoaded', initApp); 