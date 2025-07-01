import config
import uuid
import json
from typing import Dict, List, Any
from fastapi import FastAPI, Depends, HTTPException, Request, Header
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator

import database as db
from k8s_tools import k8s_tools
from models import ChatRequest, ChatResponse, SessionInfo, SessionHistory, ToolInfo, ToolResponse


# --- FastAPI App Initialization ---
app = FastAPI(
    title="Kubernetes Agent API",
    description="API for interacting with Kubernetes via a LangGraph agent.",
    version="1.0.0",
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rate Limiting ---
app.state.limiter = config.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Prometheus Monitoring ---
Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
def on_startup():
    db.create_db_and_tables()
    logger.info("Application startup complete.")

# --- Global Exception Handlers ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: {}", exc)
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error: {}", exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

# --- Auth Dependency ---
def verify_api_key(x_api_key: str = Header(...)):
    pass
    if x_api_key not in {config.ADMIN_API_KEY, config.USER_API_KEY}:
        logger.warning("Unauthorized access with key: {}", x_api_key)
        raise HTTPException(status_code=401, detail="Invalid API Key")

# --- LLM & Agent Initialization ---
llm = ChatOpenAI(base_url=config.BASE_URL, model=config.MODEL_NAME, api_key=config.API_KEY, streaming=True)

agent = create_react_agent(
    model=llm,
    tools=k8s_tools,
    prompt=(
        "You're an **expert Kubernetes assistant**. Provide **accurate, factual info** strictly "
        "about **Kubernetes concepts, operations, and tool outputs**. "
        "**Crucial guardrails:**\n"
        "- **Strictly Kubernetes-focused:** If a query isn't about Kubernetes, **do not engage**; simply state you **cannot assist** with that topic.\n"
        "- **No external info/speculation:** Do not provide personal opinions, speculate, or pull information from outside your defined Kubernetes domain or tool results.\n"
        "- **Deletion Safety:** For **any deletion operation**, you **MUST ask for explicit confirmation** using the exact phrase: 'yes, delete [resource type] [resource name]'. **Absolutely do NOT proceed without this precise confirmation.**\n"
        "Be concise, clear, and prioritize safety. Begin by confirming your role."
    ),
)

# --- Chat Endpoints ---
@app.post("/chat", response_model=ChatResponse)
@config.limiter.limit("20/minute")
async def chat_invoke(request: Request, chat_request: ChatRequest, db_session: Session = Depends(db.get_db), x_api_key: str = Depends(verify_api_key)):
    session_id = chat_request.session_id or str(uuid.uuid4())
    db.add_message_to_session(db_session, session_id, "user", chat_request.message)

    history = db.get_session_history(db_session, session_id)
    result = await agent.ainvoke({"messages": history})

    final_response = ""
    tools_info, tool_responses = [], []
    tool_call_id_map = {}

    for msg in result.get("messages", []):
        if isinstance(msg, AIMessage):
            if msg.content:
                final_response = msg.content

            for call in msg.additional_kwargs.get("tool_calls", []):
                func = call.get("function", {})
                args_str = func.get("arguments", "{}")
                try:
                    args = json.loads(args_str)
                except Exception:
                    args = args_str

                tools_info.append(ToolInfo(name=func.get("name", "unknown_tool"), args=json.dumps(args)))
                tool_call_id_map[call.get("id")] = func.get("name", "unknown_tool")

        elif isinstance(msg, ToolMessage):
            tool_name = tool_call_id_map.get(msg.tool_call_id, "unknown_tool")
            tool_responses.append(ToolResponse(name=tool_name, response=msg.content or ""))

    if final_response:
        db.add_message_to_session(db_session, session_id, "assistant", final_response)

        return ChatResponse(
        session_id=session_id,
        response=final_response,
        tools_info=tools_info if chat_request.enable_tool_response else [],
        tool_response=tool_responses if chat_request.enable_tool_response else [],
    )

@app.post("/chat/stream")
@config.limiter.limit("10/minute")
async def chat_stream(request: Request, chat_request: ChatRequest, db_session: Session = Depends(db.get_db), x_api_key: str = Depends(verify_api_key)):
    session_id = chat_request.session_id or str(uuid.uuid4())
    db.add_message_to_session(db_session, session_id, "user", chat_request.message)
    history = db.get_session_history(db_session, session_id)

    async def stream_tokens():
        full_response = ""
        yield f"data: {json.dumps({'session_id': session_id})}\n\n"

        async for token, _ in agent.astream({"messages": history}, stream_mode="messages"):
            content = token.content
            full_response += content
            yield f"data: {content}\n\n"

        if full_response:
            db.add_message_to_session(db_session, session_id, "assistant", full_response)

    return StreamingResponse(stream_tokens(), media_type="text/event-stream")

# --- Session Endpoints ---
@app.get("/sessions", response_model=List[SessionInfo])
async def list_sessions(db_session: Session = Depends(db.get_db), x_api_key: str = Depends(verify_api_key)):
    return db.get_all_sessions(db_session)

@app.get("/sessions/{session_id}", response_model=SessionHistory)
async def get_session(session_id: str, db_session: Session = Depends(db.get_db), x_api_key: str = Depends(verify_api_key)):
    session = db_session.query(db.ChatSession).filter(db.ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    history = db.get_session_history(db_session, session_id)
    return {"id": session.id, "created_at": session.created_at, "messages": history}

@app.delete("/sessions/{session_id}", status_code=204)
async def remove_session(session_id: str, db_session: Session = Depends(db.get_db), x_api_key: str = Depends(verify_api_key)):
    if not db.delete_session(db_session, session_id):
        raise HTTPException(status_code=404, detail="Session not found")

# --- Health Check ---
@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    tool_names = [tool.__name__ for tool in k8s_tools]
    llm_status = {"status": "ok"}

    try:
        await llm.ainvoke("Health check", config={"max_tokens": 1})
    except Exception as e:
        llm_status = {"status": "error", "details": str(e)}

    return {
        "status": "ok",
        "llm_connection": llm_status,
        "tools": tool_names,
    }
