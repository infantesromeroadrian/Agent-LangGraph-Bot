# Langchain Company Bot

An AI-powered company assistant built with LangChain, LangSmith, and LangGraph.

## 🌟 Features

- **Multi-Agent System**: Specialized agents working together through LangGraph
- **Role-Based Agents**: Supervisor, Researcher, Analyst, and Communicator roles
- **Document Retrieval**: Semantic search for company knowledge
- **Conversation Memory**: Maintains context across interactions
- **Vector Store Integration**: ChromaDB for document storage and retrieval
- **LangSmith Integration**: Full tracing and logging of agent interactions
- **Docker Deployment**: Easy containerized setup and deployment

## 🏗️ Architecture

The system uses a modular, multi-agent approach with LangGraph to coordinate the workflow:

1. **Supervisor Agent**: Orchestrates the workflow and understands the user query
2. **Researcher Agent**: Retrieves and synthesizes relevant information
3. **Analyst Agent**: Analyzes information and draws insights
4. **Communicator Agent**: Crafts the final response to the user

![Agent Workflow](docs/workflow.png)

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- API keys for:
  - OpenAI (or compatible LLM provider)
  - LangSmith (optional, for tracing)

### Environment Setup

1. Create a `.env` file at the root of the project with your API keys:

```env
# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
LLM_MODEL_NAME=gpt-4
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=2000

# LangSmith Configuration
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_PROJECT=company-bot
LANGCHAIN_TRACING_V2=true

# ChromaDB Configuration
CHROMA_HOST=chroma-db
CHROMA_PORT=8000
CHROMA_COLLECTION=company_documents

# App Configuration
DATA_PATH=data
DEBUG=false
```

### Running with Docker

1. Build and start the containers:

```bash
docker-compose up --build
```

2. The API will be available at http://localhost:5800 with docs at http://localhost:5800/docs

### Loading Sample Data

The system includes a utility to create and load sample data:

```bash
docker-compose exec agent-app python -m src.utils.load_sample_data --create-samples --recursive
```

## 📚 API Endpoints

### Query the Bot

```
POST /api/query
```

Example Request:
```json
{
  "query": "What is our remote work policy?",
  "context": [],
  "metadata": {}
}
```

### Document Management

```
POST /api/documents       # Add a document
DELETE /api/documents/{id}  # Delete a document
POST /api/documents/search  # Search documents
```

## 🧩 Project Structure

```
/
├── src/
│   ├── agents/           # Agent definitions and utilities
│   ├── controllers/      # API controllers
│   ├── graph/            # LangGraph workflow definitions
│   ├── models/           # Data models
│   ├── services/         # Core services
│   ├── utils/            # Utility functions
│   └── main.py           # Application entry point
├── data/                 # Data storage
│   └── sample/           # Sample documents
├── tests/                # Test suite
├── Dockerfile            # Container definition
├── docker-compose.yml    # Multi-container orchestration
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

## 🛠️ Development

### Adding New Agents

To add a new agent:

1. Add a new agent role in `src/models/class_models.py`
2. Add a prompt template in `src/agents/agent_utils.py`
3. Create a new agent node in `src/agents/agent_nodes.py`
4. Update the graph workflow in `src/graph/agent_graph.py`

### Testing

Run the test suite:

```bash
docker-compose exec agent-app pytest
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain)
- [LangSmith](https://smith.langchain.com)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [ChromaDB](https://github.com/chroma-core/chroma) 