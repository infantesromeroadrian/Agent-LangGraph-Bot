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
        solution_architect: false,
        technical_research: false,
        code_review: false,
        project_management: false,
        market_analysis: false,
        data_analysis: false,
        client_communication: false
    },
    sidebarVisible: false,
    processingSteps: {
        retrieveContext: { status: 'pending', content: '' },
        solution_architect: { status: 'pending', content: '' },
        technical_research: { status: 'pending', content: '' },
        code_review: { status: 'pending', content: '' },
        project_management: { status: 'pending', content: '' },
        market_analysis: { status: 'pending', content: '' },
        data_analysis: { status: 'pending', content: '' },
        client_communication: { status: 'pending', content: '' }
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
        solution_architect: document.getElementById('timelineSolutionArchitect'),
        technical_research: document.getElementById('timelineTechnicalResearch'),
        code_review: document.getElementById('timelineCodeReview'),
        project_management: document.getElementById('timelineProjectManagement'),
        market_analysis: document.getElementById('timelineMarketAnalysis'),
        data_analysis: document.getElementById('timelineDataAnalysis'),
        client_communication: document.getElementById('timelineClientCommunication')
    },
    timelineContents: {
        retrieveContext: document.getElementById('retrieveContextContent'),
        solution_architect: document.getElementById('solutionArchitectTimelineContent'),
        technical_research: document.getElementById('technicalResearchTimelineContent'),
        code_review: document.getElementById('codeReviewTimelineContent'),
        project_management: document.getElementById('projectManagementTimelineContent'),
        market_analysis: document.getElementById('marketAnalysisTimelineContent'),
        data_analysis: document.getElementById('dataAnalysisTimelineContent'),
        client_communication: document.getElementById('clientCommunicationTimelineContent')
    },
    agentBadges: {
        solution_architect: document.getElementById('solutionArchitectBadge'),
        technical_research: document.getElementById('technicalResearchBadge'),
        code_review: document.getElementById('codeReviewBadge'),
        project_management: document.getElementById('projectManagementBadge'),
        market_analysis: document.getElementById('marketAnalysisBadge'),
        data_analysis: document.getElementById('dataAnalysisBadge'),
        client_communication: document.getElementById('clientCommunicationBadge')
    },
    agentPanels: {
        solution_architect: document.getElementById('solutionArchitectContent'),
        technical_research: document.getElementById('technicalResearchContent'),
        code_review: document.getElementById('codeReviewContent'),
        project_management: document.getElementById('projectManagementContent'),
        market_analysis: document.getElementById('marketAnalysisContent'),
        data_analysis: document.getElementById('dataAnalysisContent'),
        client_communication: document.getElementById('clientCommunicationContent')
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
    
    // Verificar que los elementos existen
    if (!elements.agentSidebar || !elements.mainContent) {
        console.warn('Elementos de sidebar no encontrados');
        return;
    }
    
    if (appState.sidebarVisible) {
        elements.agentSidebar.classList.remove('d-none');
        if (elements.agentToggle) {
            elements.agentToggle.classList.add('active');
        }
        // Ajustar el ancho del área de contenido principal
        if (window.innerWidth >= 768) {
            elements.mainContent.classList.remove('col-md-9', 'col-lg-10');
            elements.mainContent.classList.add('col-md-6', 'col-lg-7');
        }
    } else {
        elements.agentSidebar.classList.add('d-none');
        if (elements.agentToggle) {
            elements.agentToggle.classList.remove('active');
        }
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
    // Verificar que el panel existe
    if (!elements.agentDetailsPanel) {
        console.warn('agentDetailsPanel no encontrado en el DOM');
        return;
    }
    
    elements.agentDetailsPanel.classList.toggle('d-none');
    const isVisible = !elements.agentDetailsPanel.classList.contains('d-none');
    
    // Verificar que el botón existe
    if (elements.toggleDetailsBtn) {
        elements.toggleDetailsBtn.innerHTML = isVisible ? 
            '<i class="bi bi-eye-slash me-1"></i> Ocultar Detalles Completos' : 
            '<i class="bi bi-info-circle me-1"></i> Ver Detalles Completos';
    }
}

/**
 * Actualiza el estado visual de los indicadores de agentes
 * @param {string} agent - Nombre del agente
 * @param {boolean} active - Estado activo
 */
function updateAgentIndicator(agent, active) {
    appState.activeAgents[agent] = active;
    
    // Verificar que el badge del agente existe antes de modificarlo
    if (elements.agentBadges[agent]) {
        if (active) {
            elements.agentBadges[agent].classList.add('agent-active');
        } else {
            elements.agentBadges[agent].classList.remove('agent-active');
        }
    } else {
        console.warn(`Badge para el agente ${agent} no encontrado`);
    }
}

/**
 * Actualiza el estado de un paso en la línea de tiempo
 * @param {string} step - ID del paso (retrieveContext, solution_architect, etc)
 * @param {string} status - Estado (pending, processing, completed, error)
 * @param {string} content - Contenido a mostrar
 */
function updateTimelineStep(step, status, content = '') {
    // Actualizar estado en el modelo
    appState.processingSteps[step] = {
        status: status,
        content: content || appState.processingSteps[step].content
    };
    
    // Verificar que los elementos existen antes de modificarlos
    const timelineItem = elements.timelineItems[step];
    const timelineContent = elements.timelineContents[step];
    
    // Salir si no existen los elementos necesarios
    if (!timelineItem || !timelineContent) {
        console.warn(`Elementos de timeline para el paso ${step} no encontrados`);
        return;
    }
    
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
 * Restablece los pasos de la línea de tiempo a su estado inicial.
 */
function resetTimelineSteps() {
    // Restablecer todos los pasos a pendiente
    appState.processingSteps = {
        retrieveContext: { status: 'pending', content: '' },
        solution_architect: { status: 'pending', content: '' },
        technical_research: { status: 'pending', content: '' },
        code_review: { status: 'pending', content: '' },
        project_management: { status: 'pending', content: '' },
        market_analysis: { status: 'pending', content: '' },
        data_analysis: { status: 'pending', content: '' },
        client_communication: { status: 'pending', content: '' }
    };
    
    // Actualizar la vista de la línea de tiempo
    for (const [step, content] of Object.entries(elements.timelineContents)) {
        if (content) {
            content.innerHTML = '<div class="timeline-status">Pendiente</div>';
            
            // Eliminar clases de estado
            const timelineItem = elements.timelineItems[step];
            if (timelineItem) {
                timelineItem.classList.remove('completed', 'in-progress', 'error');
            }
        }
    }
}

/**
 * Restablece los indicadores de agentes a su estado inactivo.
 */
function resetAgentIndicators() {
    // Restablecer el estado de activación de agentes
    appState.activeAgents = {
        solution_architect: false,
        technical_research: false,
        code_review: false,
        project_management: false,
        market_analysis: false,
        data_analysis: false,
        client_communication: false
    };
    
    // Restablecer indicadores visuales
    for (const [agentName, badge] of Object.entries(elements.agentBadges)) {
        if (badge) {
            const indicator = badge.querySelector('.agent-indicator');
            if (indicator) {
                indicator.classList.remove('active');
            } else {
                console.warn(`Indicador para el agente ${agentName} no encontrado`);
            }
        }
    }
}

/**
 * Crea una nueva conversación.
 */
function createNewConversation() {
    // Generar un ID único para la conversación
    appState.currentConversationId = Date.now().toString(36) + Math.random().toString(36).substring(2);
    
    // Añadir la conversación a la lista
    appState.conversations.push({
        id: appState.currentConversationId,
        title: `Conversación ${appState.conversations.length + 1}`,
        timestamp: new Date().toISOString()
    });
    
    // Actualizar la lista de conversaciones
    updateConversationList();
    
    // Inicializar el chat con el mensaje de bienvenida
    appState.messages = [{
        type: 'system',
        content: 'Bienvenido a la Consultora Tecnológica IA. ¿En qué proyecto puedo ayudarte hoy?',
        timestamp: new Date().toISOString()
    }];
    
    // Reiniciar la UI
    clearChatMessages();
    
    const systemMessage = document.createElement('div');
    systemMessage.className = 'system-message';
    systemMessage.innerHTML = `
        <div class="message-content">
            <p>${appState.messages[0].content}</p>
        </div>
    `;
    
    elements.chatMessages.appendChild(systemMessage);
    
    // Reiniciar los estados de los agentes
    resetAgentIndicators();
    resetTimelineSteps();
    
    // Ocultar paneles adicionales
    elements.agentDetailsPanel.classList.add('d-none');
    elements.documentContextPanel.classList.add('d-none');
    elements.agentToggle.classList.add('d-none');
    
    if (appState.sidebarVisible) {
        toggleAgentSidebar();
    }
    
    // Enfocar el input
    elements.userInput.focus();
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
 * Maneja el envío de mensajes.
 * @param {Event} event - Evento de submit del formulario
 */
function handleMessageSubmit(event) {
    event.preventDefault();
    
    const message = elements.userInput.value.trim();
    if (!message || appState.isProcessing) return;
    
    // Guardar el mensaje original
    const sentMessage = message;
    
    // Limpiar campo de entrada
    elements.userInput.value = '';
    elements.userInput.style.height = 'auto';
    
    // Añadir mensaje del usuario a la UI (guardar referencia al elemento)
    const messageElement = addUserMessage(sentMessage);
    
    // Añadir el indicador de carga después del mensaje del usuario
    const loadingElement = addLoadingIndicator();
    
    // Establecer estado de procesamiento
    appState.isProcessing = true;
    
    // Procesar el mensaje de forma asíncrona
    const processPromise = processUserMessage(sentMessage);
    
    // Manejar la finalización del procesamiento
    processPromise
        .then(() => {
            // Procesamiento exitoso, el loadingElement ya debe haber sido eliminado
            appState.isProcessing = false;
        })
        .catch(error => {
            console.error('Error procesando mensaje:', error);
            
            // Asegurarse de que el mensaje del usuario sigue visible
            if (!elements.chatMessages.contains(messageElement)) {
                console.log("El mensaje del usuario desapareció, volviendo a añadir");
                addUserMessage(sentMessage);
            }
            
            // Eliminar el indicador de carga si aún existe
            if (loadingElement && elements.chatMessages.contains(loadingElement)) {
                loadingElement.remove();
            }
            
            // Añadir mensaje de error
            addSystemMessage(`Lo siento, ocurrió un error al procesar tu mensaje: ${error.message}`);
            
            // Asegurarse de resetear el estado de procesamiento
            appState.isProcessing = false;
        });
}

/**
 * Añade un mensaje del usuario a la UI.
 * @param {string} message - Texto del mensaje
 * @returns {HTMLElement} Elemento del mensaje creado
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
    
    // Devolver el elemento creado para referencias futuras
    return messageElement;
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
 * @returns {HTMLElement} Elemento del indicador creado
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
    
    // Devolver el elemento para referencias futuras
    return loadingElement;
}

/**
 * Procesa un mensaje del usuario.
 * @param {string} message - Mensaje del usuario
 */
async function processUserMessage(message) {
    try {
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
        
        console.log("Enviando consulta:", message);
        console.log("Contexto enviado:", context);
        
        // Verificar si podemos conectarnos al servidor (nueva comprobación)
        try {
            const healthCheck = await fetch('/health', { method: 'GET' });
            if (!healthCheck.ok) {
                console.warn("El servidor podría no estar disponible:", await healthCheck.text());
            }
        } catch (healthErr) {
            console.warn("No se puede contactar al servidor, pero continuaremos el intento:", healthErr);
        }
        
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
        
        console.log("Estado de respuesta:", response.status);
        
        // Manejo detallado de errores HTTP
        if (!response.ok) {
            let errorText = '';
            try {
                const errorData = await response.json();
                errorText = errorData.detail || JSON.stringify(errorData);
            } catch {
                errorText = await response.text();
            }
            console.error("Error del servidor:", errorText);
            throw new Error(`Error del servidor (${response.status}): ${errorText}`);
        }
        
        const data = await response.json();
        console.log("Datos recibidos:", data);
        
        // Si no hay respuesta, mostrar un error amigable
        if (!data || typeof data !== 'object') {
            console.error("Respuesta inválida del servidor:", data);
            throw new Error('Respuesta del servidor inválida o vacía');
        }
        
        if (!data.response) {
            console.error("La respuesta no contiene el campo 'response':", data);
            
            // Fallback - crear una respuesta basada en cualquier agente disponible
            if (data.agent_responses && Object.keys(data.agent_responses).length > 0) {
                const firstAgent = Object.keys(data.agent_responses)[0];
                data.response = data.agent_responses[firstAgent].content || 
                                "No se encontró una respuesta específica, pero los agentes han procesado tu consulta.";
                console.log("Respuesta fallback creada:", data.response);
            } else {
                data.response = "No se pudo procesar tu mensaje correctamente. Por favor, intenta con una consulta diferente.";
            }
        }
        
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
        if (data.agent_responses) {
            updateAgentResponses(data.agent_responses);
        } else {
            console.warn("No se recibieron respuestas de agentes");
            // Mostrar un mensaje de recuperación
            updateTimelineStep('solution_architect', 'completed', 'Evaluación de arquitectura completada');
            updateTimelineStep('client_communication', 'completed', 'Comunicación preparada');
        }
        
        // Eliminar el indicador de carga (podría estar ya eliminado)
        const loadingIndicator = document.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
        
        // Añadir respuesta del asistente
        addAIMessage(data.response, 
            data.agent_responses ? Object.values(data.agent_responses).flatMap(ar => ar.sources || []) : []);
        
    } catch (error) {
        console.error('Error en processUserMessage:', error);
        
        // Marcar error en todos los pasos pendientes
        Object.keys(appState.processingSteps).forEach(step => {
            if (appState.processingSteps[step].status === 'processing' || 
                appState.processingSteps[step].status === 'pending') {
                updateTimelineStep(step, 'error', 'Error de procesamiento');
            }
        });
        
        // Desactivar todos los indicadores
        resetAgentIndicators();
        
        // Propagar el error para que lo maneje handleMessageSubmit
        throw error;
    }
}

/**
 * Actualiza las respuestas de los agentes en el panel de detalles.
 * 
 * @param {Object} agentResponses - Respuestas de los agentes
 */
function updateAgentResponses(agentResponses) {
    resetTimelineSteps();
    resetAgentIndicators();
    
    // Lista de todos los agentes para asegurar que todos tengan algún estado
    const allAgents = [
        'solution_architect', 
        'technical_research', 
        'code_review', 
        'project_management', 
        'market_analysis', 
        'data_analysis', 
        'client_communication'
    ];
    
    // Recopilar todos los agentes que han respondido
    const respondedAgents = new Set(Object.keys(agentResponses).map(role => {
        // Convertir los nombres antiguos al nuevo formato si es necesario
        if (role === 'supervisor') return 'solution_architect';
        if (role === 'researcher') return 'technical_research';
        if (role === 'analyst') return 'code_review';
        if (role === 'communicator') return 'client_communication';
        return role;
    }));
    
    // Actualizar el paso de recuperación de contexto
    updateTimelineStep('retrieveContext', 'completed', 'Contexto recuperado correctamente.');
    
    // Procesar las respuestas de agentes que han respondido
    for (const [role, response] of Object.entries(agentResponses)) {
        let agentName = role;
        
        // Convertir los nombres antiguos al nuevo formato si es necesario
        if (role === 'supervisor') agentName = 'solution_architect';
        if (role === 'researcher') agentName = 'technical_research';
        if (role === 'analyst') agentName = 'code_review';
        if (role === 'communicator') agentName = 'client_communication';
        
        // Ignorar roles que no tenemos en nuestra interfaz
        if (!appState.processingSteps[agentName]) continue;
        
        // Marcar el agente como activo
        appState.activeAgents[agentName] = true;
        
        // Actualizar el paso del timeline
        updateTimelineStep(agentName, 'completed', response.content);
        
        // Actualizar el contenido del panel
        if (elements.agentPanels[agentName]) {
            elements.agentPanels[agentName].innerHTML = `
                <div class="agent-response">
                    <p class="response-text">${response.content}</p>
                    ${response.sources && response.sources.length > 0 ? `
                        <div class="response-sources">
                            <h6>Fuentes:</h6>
                            <ul>
                                ${response.sources.map(source => `<li>${source}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        } else {
            console.warn(`Panel para el agente ${agentName} no encontrado`);
        }
        
        // Actualizar el indicador de agente
        if (elements.agentBadges[agentName]) {
            const indicator = elements.agentBadges[agentName].querySelector('.agent-indicator');
            if (indicator) {
                indicator.classList.add('active');
            } else {
                console.warn(`Indicador para el agente ${agentName} no encontrado`);
            }
        } else {
            console.warn(`Badge para el agente ${agentName} no encontrado`);
        }
    }
    
    // Manejar agentes que no han respondido (estado pendiente o ignorado)
    for (const agentName of allAgents) {
        if (!respondedAgents.has(agentName)) {
            // Si es el revisor de código, proporcionar una respuesta genérica útil
            if (agentName === 'code_review' && elements.agentPanels[agentName]) {
                updateTimelineStep(agentName, 'completed', 'No se detectó código para revisar en esta consulta.');
                
                elements.agentPanels[agentName].innerHTML = `
                    <div class="agent-response">
                        <p class="response-text">No se detectó código específico para revisar en esta consulta. Para utilizar el revisor de código, puedes compartir fragmentos de código o hacer preguntas relacionadas con desarrollo de software.</p>
                        <div class="code-review-tip">
                            <h6>Sugerencia:</h6>
                            <p>Prueba con preguntas como "¿Puedes revisar este código: function suma(a, b) { return a + b; }?" o "¿Cómo mejorarías esta consulta SQL?"</p>
                        </div>
                    </div>
                `;
            } else {
                // Para otros agentes, simplemente marcarlos como pendientes o ignorados
                if (appState.processingSteps[agentName]) {
                    updateTimelineStep(agentName, 'pending', 'Agente no activado para esta consulta');
                }
            }
        }
    }
    
    // Hacer visible el botón de alternancia de agentes
    if (elements.agentToggle) {
        elements.agentToggle.classList.remove('d-none');
    }
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