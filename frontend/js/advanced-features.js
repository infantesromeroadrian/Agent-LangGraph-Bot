/**
 * Advanced Features Module
 * Handles advanced LangGraph features like observability, parallel execution, and feedback loops
 */

// Global state for advanced features
const advancedState = {
    observabilityEnabled: false,
    parallelExecutionEnabled: false,
    feedbackLoopEnabled: false,
    lastConversationId: null,
    traceInfo: null
};

// DOM Elements
let observabilityBtn;
let observabilityPanel;
let observabilityToggle;
let closeObservabilityBtn;
let observabilityStatus;
let traceInfoContainer;
let traceProjectName;
let traceRunId;
let traceDashboardLink;
let traceNodesContainer;
let parallelExecutionSwitch;
let feedbackLoopSwitch;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements
    observabilityBtn = document.getElementById('observabilityBtn');
    observabilityPanel = document.getElementById('observabilityPanel');
    observabilityToggle = document.getElementById('observabilityToggle');
    closeObservabilityBtn = document.getElementById('closeObservabilityBtn');
    observabilityStatus = document.getElementById('observabilityStatus');
    traceInfoContainer = document.getElementById('traceInfoContainer');
    traceProjectName = document.getElementById('traceProjectName');
    traceRunId = document.getElementById('traceRunId');
    traceDashboardLink = document.getElementById('traceDashboardLink');
    traceNodesContainer = document.getElementById('traceNodesContainer');
    parallelExecutionSwitch = document.getElementById('parallelExecutionSwitch');
    feedbackLoopSwitch = document.getElementById('feedbackLoopSwitch');

    // Initialize event listeners
    initEventListeners();
});

// Initialize event listeners for advanced features
function initEventListeners() {
    // Toggle observability panel
    if (observabilityBtn) {
        observabilityBtn.addEventListener('click', toggleObservability);
    }

    // Close observability panel
    if (closeObservabilityBtn) {
        closeObservabilityBtn.addEventListener('click', () => {
            observabilityPanel.classList.add('d-none');
            observabilityToggle.classList.add('d-none');
        });
    }

    // Observability toggle button (mobile)
    if (observabilityToggle) {
        observabilityToggle.addEventListener('click', () => {
            observabilityPanel.classList.toggle('d-none');
        });
    }

    // Parallel execution switch
    if (parallelExecutionSwitch) {
        parallelExecutionSwitch.addEventListener('change', (e) => {
            advancedState.parallelExecutionEnabled = e.target.checked;
            console.log(`Parallel execution ${advancedState.parallelExecutionEnabled ? 'enabled' : 'disabled'}`);
        });
    }

    // Feedback loop switch
    if (feedbackLoopSwitch) {
        feedbackLoopSwitch.addEventListener('change', (e) => {
            advancedState.feedbackLoopEnabled = e.target.checked;
            console.log(`Feedback loop ${advancedState.feedbackLoopEnabled ? 'enabled' : 'disabled'}`);
        });
    }

    // Intercept message submission
    const messageForm = document.getElementById('messageForm');
    if (messageForm) {
        // Store the original onsubmit handler
        const originalOnSubmit = messageForm.onsubmit;
        
        // Replace with our own handler
        messageForm.onsubmit = function(e) {
            // If observability is enabled, use advanced submission
            if (advancedState.observabilityEnabled || 
                advancedState.parallelExecutionEnabled || 
                advancedState.feedbackLoopEnabled) {
                e.preventDefault();
                handleAdvancedSubmit();
                return false;
            } else {
                // Otherwise, use the original handler
                return originalOnSubmit ? originalOnSubmit.call(this, e) : true;
            }
        };
    }
}

// Toggle observability feature
function toggleObservability() {
    advancedState.observabilityEnabled = !advancedState.observabilityEnabled;
    
    // Update UI
    if (advancedState.observabilityEnabled) {
        observabilityStatus.textContent = 'Activo';
        observabilityStatus.classList.remove('bg-secondary');
        observabilityStatus.classList.add('bg-success');
        observabilityBtn.innerHTML = '<i class="bi bi-eye-slash me-1"></i> Desactivar Observabilidad';
        observabilityPanel.classList.remove('d-none');
        observabilityToggle.classList.remove('d-none');
    } else {
        observabilityStatus.textContent = 'Inactivo';
        observabilityStatus.classList.remove('bg-success');
        observabilityStatus.classList.add('bg-secondary');
        observabilityBtn.innerHTML = '<i class="bi bi-eye me-1"></i> Activar Observabilidad';
        // Don't hide the panel, just update status
    }
}

// Handle message submission with advanced features
async function handleAdvancedSubmit() {
    const userInput = document.getElementById('userInput');
    const query = userInput.value.trim();
    
    if (!query) return;
    
    // Get conversation ID from the app state
    const conversationId = window.currentConversationId || generateId();
    advancedState.lastConversationId = conversationId;
    
    // Clear input field
    userInput.value = '';
    
    // Add user message to the chat (reuse function from main app if available)
    if (window.addMessage) {
        window.addMessage('user', query);
    } else {
        // Fallback implementation
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'user-message';
        messageDiv.innerHTML = `<div class="message-content"><p>${escapeHtml(query)}</p></div>`;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Prepare API endpoint based on enabled features
    let endpoint = '/api/query';
    let additionalData = {};
    
    if (advancedState.observabilityEnabled) {
        endpoint = '/api/advanced/observable';
        // Reset trace info
        resetTraceInfo();
    } else if (advancedState.parallelExecutionEnabled) {
        endpoint = '/api/advanced/parallel';
        // Configure which agents to run in parallel
        additionalData = {
            agents_config: {
                "technical_branch": ["solution_architect", "technical_research"],
                "business_branch": ["market_analysis", "client_communication"]
            }
        };
    } else if (advancedState.feedbackLoopEnabled) {
        endpoint = '/api/advanced/feedback-loop';
        // Configure feedback loop
        additionalData = {
            loop_config: {
                loop_name: "refinement_loop",
                start_node: "solution_architect",
                end_node: "technical_research",
                max_iterations: 3
            }
        };
    }
    
    // Prepare request data
    const requestData = {
        query: query,
        conversation_id: conversationId,
        ...additionalData
    };
    
    try {
        // Set UI to loading state
        setLoading(true);
        
        // Make API call
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Process response based on endpoint
        if (endpoint === '/api/advanced/observable') {
            processObservabilityResponse(data);
        } else if (endpoint === '/api/advanced/parallel') {
            processParallelResponse(data);
        } else if (endpoint === '/api/advanced/feedback-loop') {
            processFeedbackLoopResponse(data);
        } else {
            // Standard response processing
            const botResponse = data.response || 'No se pudo generar una respuesta.';
            addBotMessage(botResponse);
        }
    } catch (error) {
        console.error('Error processing query:', error);
        addBotMessage('Lo siento, ocurrió un error al procesar tu consulta.');
    } finally {
        setLoading(false);
    }
}

// Process response from the observability endpoint
function processObservabilityResponse(data) {
    // Add the assistant's response to the chat
    const botResponse = data.response || 'No se pudo generar una respuesta.';
    addBotMessage(botResponse);
    
    // Update trace info in the observability panel
    if (data.trace_info) {
        updateTraceInfo(data.trace_info);
    }
}

// Process response from the parallel execution endpoint
function processParallelResponse(data) {
    // Get responses from different branches
    let compiledResponse = '';
    
    if (data.results) {
        const branches = Object.keys(data.results);
        
        for (const branch of branches) {
            const branchData = data.results[branch];
            if (branchData.agent_responses) {
                // Compile responses from all agents in this branch
                for (const [agent, response] of Object.entries(branchData.agent_responses)) {
                    if (response && response.trim()) {
                        compiledResponse += `**${formatAgentName(agent)}**: ${response}\n\n`;
                    }
                }
            }
        }
    }
    
    // Add the compiled response to the chat
    if (!compiledResponse) {
        compiledResponse = 'No se obtuvieron respuestas de los agentes en paralelo.';
    }
    
    addBotMessage(compiledResponse);
}

// Process response from the feedback loop endpoint
function processFeedbackLoopResponse(data) {
    // Format the final response
    let finalResponse = data.final_response || 'No se pudo generar una respuesta.';
    
    // Add information about the iterations if available
    if (data.iterations && Object.keys(data.iterations).length > 0) {
        const loopName = Object.keys(data.iterations)[0];
        const iterations = data.iterations[loopName];
        finalResponse = `*Respuesta refinada después de ${iterations} iteraciones:*\n\n${finalResponse}`;
    }
    
    // Add the response to the chat
    addBotMessage(finalResponse);
}

// Reset trace info in the observability panel
function resetTraceInfo() {
    if (traceInfoContainer) {
        traceInfoContainer.classList.add('d-none');
    }
    
    if (traceDashboardLink) {
        traceDashboardLink.classList.add('d-none');
    }
    
    if (traceNodesContainer) {
        traceNodesContainer.innerHTML = `
            <div class="text-center text-muted py-4">
                No hay datos de trazas disponibles
            </div>
        `;
    }
}

// Update trace info in the observability panel
function updateTraceInfo(traceInfo) {
    if (!traceInfo) return;
    
    // Update trace info fields
    if (traceProjectName) {
        traceProjectName.textContent = traceInfo.project_name || '-';
    }
    
    if (traceRunId) {
        traceRunId.textContent = traceInfo.run_id || '-';
    }
    
    // Update dashboard link
    if (traceDashboardLink && traceInfo.dashboard_url) {
        traceDashboardLink.href = traceInfo.dashboard_url;
        traceDashboardLink.classList.remove('d-none');
    }
    
    // Show trace info container
    if (traceInfoContainer) {
        traceInfoContainer.classList.remove('d-none');
    }
    
    // Add sample trace nodes for demonstration
    updateTraceNodes();
}

// Update trace nodes in the observability panel (demo version)
function updateTraceNodes() {
    if (!traceNodesContainer) return;
    
    // Sample nodes for demonstration
    const nodes = [
        { name: 'language_detection', status: 'Completado', time: '0.2s', active: false },
        { name: 'retrieve_context', status: 'Completado', time: '1.5s', active: false },
        { name: 'solution_architect', status: 'Completado', time: '3.8s', active: false },
        { name: 'technical_research', status: 'Completado', time: '4.2s', active: false },
        { name: 'client_communication', status: 'Completado', time: '2.1s', active: true }
    ];
    
    // Clear container
    traceNodesContainer.innerHTML = '';
    
    // Add nodes
    for (const node of nodes) {
        const nodeElement = document.createElement('div');
        nodeElement.className = `trace-node-item ${node.active ? 'active' : ''}`;
        nodeElement.innerHTML = `
            <div class="d-flex justify-content-between">
                <div class="node-name">${node.name}</div>
                <div class="node-time">${node.time}</div>
            </div>
            <div class="node-status">${node.status}</div>
        `;
        traceNodesContainer.appendChild(nodeElement);
    }
}

// Helper function to add bot message to the chat
function addBotMessage(message) {
    if (window.addMessage) {
        window.addMessage('assistant', message);
    } else {
        // Fallback implementation
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'assistant-message';
        messageDiv.innerHTML = `<div class="message-content"><p>${formatMarkdown(message)}</p></div>`;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Helper function to set loading state
function setLoading(isLoading) {
    // Use the app's setLoading function if available
    if (window.setLoading) {
        window.setLoading(isLoading);
    } else {
        // Simple fallback
        const sendButton = document.querySelector('#messageForm button[type="submit"]');
        if (sendButton) {
            sendButton.disabled = isLoading;
            sendButton.innerHTML = isLoading ? 
                '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>' : 
                '<i class="bi bi-send"></i>';
        }
    }
}

// Format agent name for display
function formatAgentName(name) {
    return name
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Generate a random ID
function generateId() {
    return Math.random().toString(36).substring(2, 15);
}

// Format markdown for display
function formatMarkdown(text) {
    // Very simple markdown formatting - just bold, italics, and line breaks
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

// Escape HTML special characters
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
} 