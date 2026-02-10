## Graph-Based RAG Project Documentation

### 1. Project Overview
This project implements a **Retrieval-Augmented Generation (RAG)** system using a **knowledge graph** architecture. It combines vector databases (Milvus) with graph-based knowledge representation to improve information retrieval and generation accuracy.

### 2. Key Components

#### 2.1 Core Files
- `build_knowledge_graph.py` - Main script for creating and managing the knowledge graph
- `milvus_db.py` - Handles Milvus vector database interactions
- `retrieve.py` - Implements the retrieval-augmented generation workflow
- `prompt_library.py` - Stores prompt templates for different tasks
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (e.g., Milvus connection details)

#### 2.2 Directory Structure
```
graph_based_RAG/
├── build_knowledge_graph.py
├── milvus_db.py
├── retrieve.py
├── prompt_library.py
├── README.md
├── requirements.txt
└── .env
```

### 3. Setup & Configuration

#### 3.1 Prerequisites
- Python 3.10+
- Milvus vector database
- PostgreSQL (if using graph database)

#### 3.2 Installation
1. Clone repository
```bash
git clone https://github.com/your-repo.git
```
2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```
3. Install dependencies
```bash
pip install -r requirements.txt
```

#### 3.3 Configuration
1. Create `.env` file:
```
MILVUS_HOST=127.0.0.1
MILVUS_PORT=19530
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```
2. Update `milvus_db.py` with your Milvus connection details

### 4. Usage

#### 4.1 Basic Workflow
1. Build knowledge graph
```bash
python build_knowledge_graph.py --input data/sample_data.json
```
2. Start retrieval-augmented generation
```bash
python retrieve.py --query "What is the capital of France?"
```

#### 4.2 Advanced Features
- Multiple retrieval strategies (vector search, graph traversal)
- Prompt templating system
- Metric tracking for evaluation

### 5. File Descriptions

#### `build_knowledge_graph.py`
- Creates graph nodes/edges from raw data
- Handles:
  - Text preprocessing
  - Entity recognition
  - Relationship mapping

#### `milvus_db.py`
- Manages vector database operations
- Features:
  - Embedding storage
  - Vector similarity search
  - Data indexing

#### `retrieve.py`
- Implements RAG workflow
- Process:
  - Query understanding
  - Knowledge graph traversal
  - Answer generation

### 6. Contribution Guidelines
- Follow PEP8 style guide
- Write tests for new features
- Document API endpoints
- Update README.md for new components