import uuid
from typing import List, Dict

from sqlalchemy import create_engine, Column, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
from sqlalchemy.sql import func

# Use a file-based SQLite database
DATABASE_URL = "sqlite:///./chat_history.db"

# The connect_args is for SQLite to allow multi-threaded access, which FastAPI uses.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- SQLAlchemy Models ---

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    session = relationship("ChatSession", back_populates="messages")


# --- Database Management ---

def create_db_and_tables():
    """Creates all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- CRUD Functions for Sessions and Messages ---

def get_session_history(db: Session, session_id: str) -> List[Dict[str, str]]:
    """Retrieves all messages for a given session, ordered by creation time."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        return []
    history = [{"role": msg.role, "content": msg.content} for msg in sorted(session.messages, key=lambda m: m.created_at)]
    return history

def add_message_to_session(db: Session, session_id: str, role: str, content: str):
    """Adds a new message to a session. Creates the session if it doesn't exist."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        session = ChatSession(id=session_id)
        db.add(session)
    message = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(message)
    db.commit()

def get_all_sessions(db: Session) -> List[ChatSession]:
    """Retrieves all chat sessions."""
    return db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()

def delete_session(db: Session, session_id: str) -> bool:
    """Deletes a session and all its messages. Returns True if successful, False otherwise."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        db.delete(session)
        db.commit()
        return True
    return False