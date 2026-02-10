# Agentic Project Manager 🤖📊

An AI-powered project management tool that automates software planning, requirements analysis, and resource allocation. Built with **LangGraph**, **FastAPI**, and **React**, it uses a multi-agent system to turn a simple project brief into a fully prioritized and assigned Kanban board.

## 🚀 Features

* **Multi-Agent Architecture:** Orchestrates specialized agents (Business Analyst, Planner, Allocator) to break down complex tasks.
* **Automated User Stories:** Converts high-level project briefs into detailed user stories with acceptance criteria and technical notes.
* **Intelligent Allocation:** Matches tasks to team members based on their specific skills and roles using a local LLM (Gemma 3).
* **Human-in-the-Loop:** Interactive review phase allows users to modify priorities and stories before final allocation.
* **Real-Time Streaming:** Uses Server-Sent Events (SSE) to provide live feedback on agent thought processes and state updates.
* **State Persistence:** Maintains context across the entire workflow (Planning → Review → Allocation) to ensure seamless execution.

## 🛠️ Tech Stack

### Backend
* **Python 3.11+**
* **FastAPI:** High-performance API for handling SSE streams and agent requests.
* **LangGraph:** For stateful, cyclic multi-agent orchestration.
* **LangChain:** For LLM interaction and prompt management.
* **Ollama:** Local LLM runner (using `gemma3:27b`).

### Frontend
* **React 18** (Vite)
* **TypeScript**
* **Tailwind CSS** & **Shadcn/UI**
* **Zustand:** For global state management.
* **Lucide React:** For icons.

## ⚙️ Installation

### Prerequisites
* Node.js 18+
* Python 3.11+
* [Ollama](https://ollama.com/) installed and running.

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn langgraph langchain-ollama python-dotenv

# Start the API server (Runs on port 8200)
python api.py
```


*Note: Ensure your api.py is configured to run on port 8200...*.

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev

```
## 📖 Usage

1.  **Define Project & Team:**
    * Enter a project brief (e.g., "Build a CRM for a dental clinic").
    * Add team members to the roster with their roles (Backend, Frontend, QA) and skills.

2.  **Run Agents:**
    * Click **"Start Analysis"**.
    * Watch as the **Business Analyst Agent** breaks down the brief into modules.
    * The **Planner Agent** then generates detailed user stories for each module.

3.  **Review & Prioritize:**
    * The system pauses for **Human Review**.
    * Verify the generated stories in the Prioritization Grid.
    * Edit priorities or remove tasks if needed.

4.  **Allocate Resources:**
    * Click **"Approve & Allocate"**.
    * The **Allocator Agent** assigns tasks to the best-fit team members based on their skill sets.
    * View the final results on the **Kanban Dashboard**.

## 🧠 Architecture Highlights

* **Robust JSON Parsing:** Implements Regex-based cleaning to handle LLM "chat" output, ensuring strict JSON formats for the frontend.
* **Session Management:** Solved the "Amnesia Bug" by capturing and passing a unique `session_id` between the frontend and backend, allowing the graph to resume execution exactly where it paused.
* **Data Transformation:** Automatically flattens nested Python dictionaries into frontend-friendly objects for the UI components.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.