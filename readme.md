# Kubernetes AI Agent

This project implements a Kubernetes AI Agent using LangGraph and FastAPI. It allows users to interact with a Kubernetes cluster through a REST API, enabling real-time, session-based chat conversations. The agent can manage a wide range of Kubernetes resources.

## Files

*   [`main.py`](main.py): The main FastAPI application entry point, handling API routing and agent orchestration.
*   [`config.py`](config.py): Manages application configuration, including environment variables and settings.
*   [`database.py`](database.py): Contains SQLAlchemy models and functions for database interactions.
*   [`models.py`](models.py): Defines Pydantic models for API request and response validation.
*   [`k8s_tools.py`](k8s_tools.py): A library of functions (tools) for interacting with the Kubernetes API.
*   [`streamlit_app.py`](streamlit_app.py): (Optional) A Streamlit web interface for interacting with the agent API.

## Prerequisites

*   Python 3.10+
*   A Kubernetes cluster (e.g., Minikube, Kind, or a cloud-based cluster)
*   `~/.kube/config` file to connect to your cluster
*   The following Python packages:
    *   `langgraph`
    *   `langchain-openai`
    *   `kubernetes`
    *   `python-dotenv`
    *   `fastapi`
    *   `uvicorn[standard]`
    *   `pyyaml`
    *   `sqlalchemy`
    *   `pydantic`
    *   `pyyaml`
    *   `prometheus-fastapi-instrumentator`
    *   `streamlit` (optional, for a UI)

## Setup

1.  Clone the repository
2.  Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

To run the FastAPI server:

```bash
uvicorn main:app --reload
```

To run the Streamlit chat interface:

```bash
streamlit run streamlit_app.py
```

You can then interact with the agent by typing commands in the chat interface. For example:

*   `List all namespaces`
*   `Create a pod named 'my-pod' with image 'nginx'`
*   `Delete deployment 'my-deployment' in namespace 'default'`


## API Endpoints

You can interact with the Kubernetes agent API directly using tools like `curl` or any HTTP client.

### Chat (Synchronous)

Sends a message to the agent and waits for the complete response.

`POST /chat`

**Request Body (JSON):**

```json
{
  "message": "List all pods in the default namespace",
  "session_id": "optional-session-id",
  "enable_tool_response": false
}
```

*   `message` (string, required): The user's message or command.
*   `session_id` (string, optional): A unique identifier for the chat session. If not provided, a new session will be created.
*   `enable_tool_response` (boolean, optional): If true, the response will include details about the tools used and their outputs. Defaults to false.

**Example using curl:**

```bash
curl -X POST http://localhost:8000/chat \
-H "Content-Type: application/json" \
-H "x-api-key: YOUR_API_KEY" \
-d '{
  "message": "List all pods in the default namespace"
}'
```

### Chat Stream (Server-Sent Events)

Sends a message to the agent and receives the response as a stream of tokens using Server-Sent Events (SSE).

`POST /chat/stream`

**Request Body (JSON):**

```json
{
  "message": "Describe the deployment 'my-deployment' in namespace 'default'",
  "session_id": "optional-session-id"
}
```

*   `message` (string, required): The user's message or command.
*   `session_id` (string, optional): A unique identifier for the chat session. If not provided, a new session will be created.

**Example using curl:**

```bash
curl -X POST http://localhost:8000/chat/stream \
-H "Content-Type: application/json" \
-H "x-api-key: YOUR_API_KEY" \
-d '{
  "message": "Describe the deployment \'my-deployment\' in namespace \'default\'"
}'
```

The response will be a stream of `data:` lines, each containing a chunk of the agent's response. The first message will contain the `session_id`.

## Session Management

*   `GET /sessions`: List all active chat sessions.
*   `GET /sessions/{session_id}`: Get the history of a specific session.
*   `DELETE /sessions/{session_id}`: Delete a specific session and its history.

**Example using curl:**

```bash
# List sessions
curl http://localhost:8000/sessions -H "x-api-key: YOUR_API_KEY"

# Get session history
curl http://localhost:8000/sessions/your-session-id -H "x-api-key: YOUR_API_KEY"

# Delete a session
curl -X DELETE http://localhost:8000/sessions/your-session-id -H "x-api-key: YOUR_API_KEY"
```
## Configuration

Configuration is managed via the [`config.py`](config.py) file, which loads settings from a `.env` file in the project directory. Create a `.env` file and set the following variables:

*   `URL`: Base URL for the OpenAI API (if using a custom endpoint)
*   `MODEL`: The OpenAI model to use (e.g., `gpt-3.5-turbo`)
*   `KEY`: Your OpenAI API key
