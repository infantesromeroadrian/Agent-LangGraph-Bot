/**
 * Diagrama dinámico del flujo de trabajo de Agentes
 * Usando mermaid.js para visualizar la arquitectura y estados de los agentes
 */

// Estado del diagrama
const diagramState = {
    activeNodes: [],
    activeEdges: [],
    workflowStep: 'initialize' // Estado inicial
};

// Configuración del diagrama
const diagramConfig = {
    theme: 'dark',
    securityLevel: 'loose',
    flowchart: {
        curve: 'basis',
        htmlLabels: true,
        nodeSpacing: 25,
        rankSpacing: 35,
        padding: 5
    }
};

/**
 * Inicializa el diagrama de flujo de trabajo
 */
function initWorkflowDiagram() {
    // Cargar mermaid.js desde CDN si no está ya cargado
    if (!window.mermaid) {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mermaid@9/dist/mermaid.min.js';
        script.onload = () => {
            configureAndRenderDiagram();
        };
        document.head.appendChild(script);
    } else {
        configureAndRenderDiagram();
    }
}

/**
 * Configura y renderiza el diagrama
 */
function configureAndRenderDiagram() {
    // Inicializar mermaid
    mermaid.initialize(diagramConfig);
    
    // Renderizar diagrama inicial
    updateWorkflowDiagram();
    
    // Configurar actualización automática cuando cambie el estado de procesamiento
    setInterval(() => {
        if (appState.isProcessing) {
            updateWorkflowDiagram();
        }
    }, 2000);
}

/**
 * Actualiza el diagrama basado en el estado actual
 */
function updateWorkflowDiagram() {
    const workflowContainer = document.getElementById('workflowDiagram');
    if (!workflowContainer) return;
    
    // Mapear estados de procesamiento a estado del diagrama
    mapProcessingToGraph();
    
    // Crear definición del diagrama
    const diagram = createDiagramDefinition();
    
    // Actualizar contenedor con el nuevo diagrama
    workflowContainer.innerHTML = diagram;
    
    // Renderizar con mermaid
    mermaid.init(undefined, workflowContainer);
}

/**
 * Mapea el estado de procesamiento al grafo
 */
function mapProcessingToGraph() {
    // Reiniciar estado
    diagramState.activeNodes = [];
    diagramState.activeEdges = [];
    
    // Mapear nodos activos
    for (const [agent, status] of Object.entries(appState.processingSteps)) {
        if (status.status === 'completed' || status.status === 'processing') {
            diagramState.activeNodes.push(agent);
        }
    }
    
    // Derivar aristas activas basadas en la lógica del flujo de trabajo
    if (diagramState.activeNodes.includes('retrieveContext')) {
        diagramState.workflowStep = 'context';
    }
    
    if (diagramState.activeNodes.includes('solution_architect')) {
        diagramState.workflowStep = 'architecture';
        diagramState.activeEdges.push('retrieveContext_to_solution_architect');
    }
    
    if (diagramState.activeNodes.includes('technical_research')) {
        diagramState.workflowStep = 'research';
        diagramState.activeEdges.push('solution_architect_to_technical_research');
    }
    
    if (diagramState.activeNodes.includes('code_review')) {
        diagramState.workflowStep = 'code_review';
        diagramState.activeEdges.push('technical_research_to_code_review');
    }
    
    if (diagramState.activeNodes.includes('project_management')) {
        diagramState.workflowStep = 'project';
        // La arista podría venir desde code_review o technical_research
        if (diagramState.activeNodes.includes('code_review')) {
            diagramState.activeEdges.push('code_review_to_project_management');
        } else {
            diagramState.activeEdges.push('technical_research_to_project_management');
        }
    }
    
    if (diagramState.activeNodes.includes('market_analysis')) {
        diagramState.workflowStep = 'market';
        // La arista podría venir desde diferentes nodos previos
        if (diagramState.activeNodes.includes('project_management')) {
            diagramState.activeEdges.push('project_management_to_market_analysis');
        } else if (diagramState.activeNodes.includes('code_review')) {
            diagramState.activeEdges.push('code_review_to_market_analysis');
        }
    }
    
    if (diagramState.activeNodes.includes('data_analysis')) {
        diagramState.workflowStep = 'data';
        // La arista podría venir desde different nodos previos
        if (diagramState.activeNodes.includes('market_analysis')) {
            diagramState.activeEdges.push('market_analysis_to_data_analysis');
        } else if (diagramState.activeNodes.includes('project_management')) {
            diagramState.activeEdges.push('project_management_to_data_analysis');
        }
    }
    
    if (diagramState.activeNodes.includes('client_communication')) {
        diagramState.workflowStep = 'communication';
        // La arista podría venir desde different nodos previos
        if (diagramState.activeNodes.includes('data_analysis')) {
            diagramState.activeEdges.push('data_analysis_to_client_communication');
        } else if (diagramState.activeNodes.includes('market_analysis')) {
            diagramState.activeEdges.push('market_analysis_to_client_communication');
        } else if (diagramState.activeNodes.includes('project_management')) {
            diagramState.activeEdges.push('project_management_to_client_communication');
        }
    }
}

/**
 * Crea la definición del diagrama
 * @returns {string} Definición del diagrama en formato mermaid
 */
function createDiagramDefinition() {
    // Colores para diferentes estados
    const colors = {
        inactive: '#424242',
        active: '#64B5F6',
        completed: '#81C784',
        processing: '#FFD54F'
    };
    
    // Obtener colores para nodos
    const getNodeColor = (node) => {
        const status = appState.processingSteps[node]?.status || 'inactive';
        switch (status) {
            case 'completed': return colors.completed;
            case 'processing': return colors.processing;
            default: return colors.inactive;
        }
    };
    
    // Verificar si un nodo está activo
    const isActive = (node) => diagramState.activeNodes.includes(node);
    
    // Verificar si una arista está activa
    const isEdgeActive = (edge) => diagramState.activeEdges.includes(edge);
    
    // Comprobar si el contenedor está en el sidebar
    const isInSidebar = document.getElementById('workflowDiagram').closest('.sidebar') !== null;
    
    // Usar etiquetas más cortas si está en el sidebar
    const labels = isInSidebar ? {
        context: 'Contexto',
        architect: 'Arquitecto',
        research: 'Investigador',
        code: 'Código',
        project: 'Proyecto',
        market: 'Mercado',
        data: 'Datos',
        client: 'Cliente'
    } : {
        context: 'Recuperación de Contexto',
        architect: 'Arquitecto de Soluciones',
        research: 'Investigador Técnico',
        code: 'Revisor de Código',
        project: 'Gestor de Proyectos',
        market: 'Análisis de Mercado',
        data: 'Análisis de Datos',
        client: 'Comunicación con Cliente'
    };
    
    // Crear la definición de mermaid
    return `graph TB
    classDef active fill:#64B5F6,stroke:#1E88E5,color:#fff
    classDef inactive fill:#424242,stroke:#313131,color:#DDD
    classDef completed fill:#81C784,stroke:#4CAF50,color:#fff
    classDef processing fill:#FFD54F,stroke:#FFC107,color:#fff
    
    %% Definición de nodos
    User((Usuario))
    Context[${labels.context}]
    Architect[${labels.architect}]
    Research[${labels.research}]
    Code[${labels.code}]
    Project[${labels.project}]
    Market[${labels.market}]
    Data[${labels.data}]
    Client[${labels.client}]
    
    %% Conexiones
    User --> Context
    Context -- Info --> Architect
    Architect -- Diseño --> Research
    Research -- Código --> Code
    Research -- NoCode --> Project
    Code -- Review --> Project
    Code -- Alt --> Market
    Project -- Eval --> Market
    Project -- Alt --> Data
    Market -- Insights --> Data
    Market -- NoData --> Client
    Data -- Results --> Client
    
    %% Aplicar estilos basados en estado
    class Context ${appState.processingSteps.retrieveContext?.status || 'inactive'}
    class Architect ${appState.processingSteps.solution_architect?.status || 'inactive'}
    class Research ${appState.processingSteps.technical_research?.status || 'inactive'}
    class Code ${appState.processingSteps.code_review?.status || 'inactive'}
    class Project ${appState.processingSteps.project_management?.status || 'inactive'}
    class Market ${appState.processingSteps.market_analysis?.status || 'inactive'}
    class Data ${appState.processingSteps.data_analysis?.status || 'inactive'}
    class Client ${appState.processingSteps.client_communication?.status || 'inactive'}
    class User active
    `;
}

/**
 * Actualiza el estilo del diagrama según el tema actual
 */
function updateDiagramTheme() {
    if (appState.darkMode) {
        diagramConfig.theme = 'dark';
    } else {
        diagramConfig.theme = 'default';
    }
    
    if (window.mermaid) {
        mermaid.initialize(diagramConfig);
        updateWorkflowDiagram();
    }
}

// Exponer funciones para usar en otros archivos
window.workflowDiagram = {
    init: initWorkflowDiagram,
    update: updateWorkflowDiagram,
    updateTheme: updateDiagramTheme
}; 