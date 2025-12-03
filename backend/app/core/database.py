from sqlmodel import SQLModel, create_engine, Session, Field
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")
engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session


class Integration(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    spec_url: str
    encrypted_key: Optional[str] = None
    auth_header_type: str = "Bearer"
    connection_id: str = Field(
        unique=True, index=True)


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    thread_id: str = Field(index=True)
    role: str
    content: str
    tool_calls: Optional[str] = None


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
