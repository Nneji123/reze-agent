# 📋 Implementation Plan: Reze AI Agent

## 🎯 Project Overview

Reze is a **chat-based AI agent** for Resend.com. Users interact through natural conversation:

- **Single Interface**: Everything happens through chat messages
- **Multi-turn Conversations**: Agent asks clarifying questions when needed
  - Example: "Send an email to John" → Agent asks "What's the subject?"
  - User: "Welcome email" → Agent asks "HTML or plain text?"
  - User: "HTML" → Agent sends email
- **AI-Driven Decisions**: Agent decides when to call tools based on conversation
- **Real-Time Streaming**: See agent's thought process as it happens
- **RAG Knowledge**: Pulls info from Resend.com docs when answering questions

**Tech Stack:**
- **Framework**: FastAPI + PydanticAI
- **AI Model**: GLM 4.7 from z.ai (OpenAI-compatible protocol)
- **RAG System**: Memvid (single-file, hybrid search)
- **Email Service**: Resend.com API
- **Task Queue**: Celery with Redis for background processing
- **Streaming**: Server-Sent Events (SSE)
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Cache**: Redis

---

## 📊 Architecture

```
User Chat Message
    ↓
FastAPI Chat Endpoint
    ↓
AI Agent (GLM 4.7) + Memvid RAG (Streaming)
    ↓
Agent asks questions OR calls tools (Send Email, Check Status, etc.)
    ↓
Tools execute (Resend API via httpx)
    ↓
Native FastAPI Streaming
    ↓
User sees real-time agent responses
```

---

## 📁 File Modification Map

### 🗑️ Files to Remove
```
src/api/routers/whatsapp_router.py
src/api/processors/*
src/tools/location.py
src/services/speech_to_text.py
src/services/whatsapp.py
src/prompts/config/* (remove if not needed)
src/prompts/context/* (remove if not needed)
src/prompts/managers/* (remove if not needed)
```

### ✏️ Files to Modify
```
pyproject.toml                              # Update dependencies
env.example                                 # New environment variables
pytest.ini                                  # Add pytest configuration
main.py                                     # Entry point
src/config.py                               # New configuration classes
src/services/ai.py                          # GLM 4.7 integration
src/services/rag.py                         # Memvid integration
src/services/embeddings.py                  # Update for Memvid
src/api/app.py                              # Remove WhatsApp, add Reze setup
src/database/models.py                      # Email/conversation models
README.md                                   # Updated documentation
Dockerfile                                  # Remove ChromaDB
compose.yml                                 # Update services
```

### ➕ Files to Create
```
src/api/routers/chat_router.py              # Chat API (ONLY endpoint)
src/api/schemas/chat.py                     # Chat request/response schemas
src/tools/resend_tools.py                   # Resend API tools
src/services/resend.py                      # Resend API client
src/services/memvid.py                      # Memvid integration service
src/services/streaming.py                   # SSE streaming handler

src/prompts/reze_agent.py                   # Reze system prompts
tests/                                      # Test files (pytest)
```

---

## 🔄 Phase-by-Phase Implementation Plan

### **Phase 1: Core Infrastructure Setup**

#### 1.1 Update `pyproject.toml`

**Remove:**
```toml
"google-generativeai>=0.3.0",
"pywa>=3.0.0",
"chromadb>=1.0.15",
"pydub>=0.25.1",
"geopy>=2.4.0",
"torch>=2.0.0,<3.0.0",
"llmlingua>=0.2.0",
```

**Add:**
```toml
"memvid-sdk>=1.0.0",
"resend>=1.0.0",
"httpx>=0.25.0",
"pytest>=7.4.0",
"pytest-asyncio>=0.21.0",
"pytest-cov>=4.1.0",
```

**Keep:**
```toml
"fastapi>=0.104.0",
"uvicorn[standard]>=0.24.0",
"sqlalchemy[asyncio]>=2.0.0",
"asyncpg>=0.29.0",
"aiosqlite>=0.19.0",
"pydantic>=2.5.0",
"pydantic-settings>=2.0.0",
"pydantic-extra-types>=2.0.0",
"python-dotenv>=1.0.0",
"redis>=5.0.1",

"structlog>=23.2.0",
"pydantic-ai>=0.1.0",
"loguru>=0.7.3",
"sentry-sdk[fastapi]>=2.0.0",
"pytz>=2024.1",
```

#### 1.2 Create `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=src
    --cov-report=html
    --cov-report=term-missing
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

#### 1.3 Create New Configuration (`src/config.py`)

```python
"""Configuration settings for Reze AI Agent."""

from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Application core settings."""
    debug: bool = Field(default=True, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")


class GLMSettings(BaseSettings):
    """GLM 4.7 AI provider settings."""
    glm_api_key: str = Field(..., env="GLM_API_KEY")
    glm_base_url: str = Field(default="https://open.bigmodel.cn/api/paas/v4", env="GLM_BASE_URL")
    glm_model: str = Field(default="glm-4.7", env="GLM_MODEL")


class ResendSettings(BaseSettings):
    """Resend.com API settings."""
    resend_api_key: str = Field(..., env="RESEND_API_KEY")
    resend_from_email: str = Field(..., env="RESEND_FROM_EMAIL")
    resend_base_url: str = Field(default="https://api.resend.com", env="RESEND_BASE_URL")


class MemvidSettings(BaseSettings):
    """Memvid RAG settings."""
    memvid_file_path: str = Field(default="./memory.mv2", env="MEMVID_FILE_PATH")
    memvid_index_kind: str = Field(default="basic", env="MEMVID_INDEX_KIND")


class DatabaseSettings(BaseSettings):
    """Database settings."""
    database_url: str = Field(default="sqlite+aiosqlite:///./database", env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")


class RedisSettings(BaseSettings):
    """Redis settings."""
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")





class Settings(BaseSettings):
    """Main settings."""
    app: AppSettings = Field(default_factory=AppSettings)
    ai: GLMSettings = Field(default_factory=GLMSettings)
    resend: ResendSettings = Field(default_factory=ResendSettings)
    memvid: MemvidSettings = Field(default_factory=MemvidSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    settings: RedisSettings = Field(default_factory=RedisSettings)

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"


settings = Settings()
```

#### 1.4 Update `env.example`

```env
# =============================================================================
# REZE AI AGENT - ENVIRONMENT CONFIGURATION
# =============================================================================

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
DEBUG=True
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# =============================================================================
# GLM 4.7 AI SETTINGS
# =============================================================================
GLM_API_KEY=your_glm_api_key_here
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
GLM_MODEL=glm-4.7

# =============================================================================
# RESEND.COM SETTINGS
# =============================================================================
RESEND_API_KEY=re_xxxxxxxxxxxx
RESEND_FROM_EMAIL=noreply@yourdomain.com
RESEND_BASE_URL=https://api.resend.com

# =============================================================================
# MEMVID RAG SETTINGS
# =============================================================================
MEMVID_FILE_PATH=./memory.mv2
MEMVID_INDEX_KIND=basic

# =============================================================================
# DATABASE SETTINGS
# =============================================================================
DATABASE_URL=sqlite+aiosqlite:///./database.db
DATABASE_ECHO=false

# =============================================================================
# REDIS SETTINGS
# =============================================================================
REDIS_URL=redis://localhost:6379/0

# =============================================================================
# CELERY SETTINGS
# =============================================================================
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

#### 1.5 Update `compose.yml`

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    volumes:
      - ./memory.mv2:/app/memory.mv2
      - ./database:/app/database
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload



  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

---

### **Phase 2: AI Model Integration (GLM 4.7)**

#### 2.1 Implement `src/services/ai.py`

```python
"""AI service with GLM 4.7 integration."""

from typing import Optional
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

from src.config import settings
from src.tools import ALL_TOOLS


class AIService:
    """Manages AI model configuration for GLM 4.7."""

    def __init__(self):
        self._agent: Optional[Agent] = None

    def get_agent(self) -> Agent:
        """Get the configured AI agent."""
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent

    def _create_agent(self) -> Agent:
        """Create GLM 4.7 agent."""
        # GLM 4.7 uses OpenAI-compatible protocol
        model = OpenAIChatModel(
            settings.ai.glm_model,
            api_key=settings.ai.glm_api_key,
            base_url=settings.ai.glm_base_url,
        )

        return Agent(
            model,
            tools=ALL_TOOLS,
        )


# Global AI service instance
ai_service = AIService()
```

---

### **Phase 3: RAG System (Memvid)**

#### 3.1 Implement `src/services/memvid.py`

```python
"""Memvid integration for RAG."""

import os
from typing import List, Dict, Optional

from loguru import logger
from memvid_sdk import create, use

from src.config import settings


class MemvidService:
    """Memvid RAG service."""

    def __init__(self):
        self.mem = None
        self._initialize()

    def _initialize(self):
        """Initialize Memvid store."""
        path = settings.memvid.memvid_file_path

        try:
            if os.path.exists(path):
                logger.info(f"Loading existing Memvid store from {path}")
                self.mem = use(settings.memvid.memvid_index_kind, path)
            else:
                logger.info(f"Creating new Memvid store at {path}")
                self.mem = create(path, settings.memvid.memvid_index_kind)
                logger.info("Memvid store created successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Memvid: {e}")
            raise

    async def add_document(
        self,
        text: str,
        title: str,
        metadata: Optional[Dict] = None
    ):
        """Add document to Memvid."""
        await self.mem.put(
            title=title,
            text=text,
            metadata=metadata or {}
        )
        logger.info(f"Added document: {title}")

    async def search(
        self,
        query: str,
        k: int = 5,
        mode: str = "hybrid"
    ) -> List[Dict]:
        """Search documents in Memvid."""
        results = await self.mem.find(
            query=query,
            k=k,
            mode=mode
        )
        return results

    async def enrich_entities(self):
        """Extract and enrich entities."""
        await self.mem.enrich(engine="rules")

    async def get_entity_state(self, entity_name: str) -> Dict:
        """Get entity state."""
        state = await self.mem.state(entity_name)
        return state

    async def get_stats(self) -> Dict:
        """Get Memvid statistics."""
        # Basic stats implementation
        return {
            "file_path": settings.memvid.memvid_file_path,
            "index_kind": settings.memvid.memvid_index_kind,
        }


# Global Memvid service instance
memvid = MemvidService()
```

#### 3.2 Update `src/services/rag.py`

```python
"""RAG service with Memvid integration."""

from typing import Optional, List
from loguru import logger

from src.config import settings
from src.services.ai import ai_service
from src.services.memvid import memvid
from src.prompts import REZE_AGENT_PERSONA, REZE_SYSTEM_INSTRUCTIONS


class RAGService:
    """RAG service for document retrieval and AI responses."""

    def __init__(self):
        self.agent = ai_service.get_agent()
        self.system_prompt = self._build_system_prompt()
        self._load_documents()

    def _build_system_prompt(self) -> str:
        """Build system prompt."""
        return f"{REZE_AGENT_PERSONA}\n\n{REZE_SYSTEM_INSTRUCTIONS}"

    def _load_documents(self):
        """Load Resend.com documentation into Memvid."""
        # TODO: Implement document loading from Resend docs
        logger.info("Loading documents into Memvid...")
        # This will be populated from Resend.com/docs
        logger.info("Documents loaded")

    async def query(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        use_rag: bool = True
    ):
        """Query with optional RAG."""
        # Retrieve context if RAG is enabled
        context = None
        if use_rag:
            context = await self._retrieve_documents(query)

        # Generate response
        result = await self.agent.run(query)

        return {
            "message": result.data,
            "context": context,
            "tools_called": result.tool_calls if hasattr(result, 'tool_calls') else None
        }

    async def _retrieve_documents(self, query: str, k: int = 5) -> List[str]:
        """Retrieve relevant documents."""
        results = await memvid.search(query, k=k)
        return [doc.get("text", "") for doc in results]


# Global RAG service instance
rag_service = RAGService()
```

---

### **Phase 4: Resend.com Integration**

#### 4.1 Implement `src/services/resend.py`

```python
"""Resend.com API client."""

from typing import Optional, List, Dict
import resend
from loguru import logger

from src.config import settings


class ResendService:
    """Resend.com API client."""

    def __init__(self):
        resend.api_key = settings.resend.resend_api_key

    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> Dict:
        """Send email via Resend."""
        params = {
            "from": from_email or settings.resend.resend_from_email,
            "to": to,
            "subject": subject,
            "html": html_content,
        }

        if attachments:
            params["attachments"] = attachments

        try:
            result = resend.Emails.send(params)
            logger.info(f"Email sent successfully: {result['id']}")
            return result
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    async def get_email_status(self, email_id: str) -> Dict:
        """Get email status."""
        try:
            # Use Resend API to fetch status
            # Note: Adjust based on actual Resend API
            result = resend.Emails.get(email_id)
            return result
        except Exception as e:
            logger.error(f"Failed to get email status: {e}")
            raise

    async def get_email_attachments(self, email_id: str) -> List[Dict]:
        """Retrieve email attachments."""
        try:
            # Fetch email details and extract attachments
            result = resend.Emails.get(email_id)
            # Parse attachments from result
            return result.get("attachments", [])
        except Exception as e:
            logger.error(f"Failed to get attachments: {e}")
            raise

    async def list_emails(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """List sent emails."""
        try:
            # Use Resend API to list emails
            result = resend.Emails.list(limit=limit, offset=offset)
            return result
        except Exception as e:
            logger.error(f"Failed to list emails: {e}")
            raise


# Global Resend service instance
resend_service = ResendService()
```

#### 4.2 Implement `src/tools/resend_tools.py`

```python
"""PydanticAI tools for Resend operations."""

from pydantic_ai import RunContext
from pydantic import BaseModel, EmailStr


class SendEmailInput(BaseModel):
    """Input for sending email."""
    to: EmailStr
    subject: str
    html_content: str


class GetEmailStatusInput(BaseModel):
    """Input for getting email status."""
    email_id: str


async def send_email_tool(ctx: RunContext, data: SendEmailInput) -> str:
    """Send an email via Resend.com."""
    from src.services.resend import resend_service

    result = await resend_service.send_email(
        to=data.to,
        subject=data.subject,
        html_content=data.html_content
    )
    return f"Email sent successfully! ID: {result['id']}"


async def get_email_status_tool(ctx: RunContext, data: GetEmailStatusInput) -> str:
    """Get the status of a sent email."""
    from src.services.resend import resend_service

    status = await resend_service.get_email_status(data.email_id)
    return f"Email status: {status.get('status', 'unknown')}"


async def get_attachments_tool(ctx: RunContext, data: GetEmailStatusInput) -> str:
    """Get attachments from an email."""
    from src.services.resend import resend_service

    attachments = await resend_service.get_email_attachments(data.email_id)
    return f"Found {len(attachments)} attachments"


# Export all tools
ALL_TOOLS = [send_email_tool, get_email_status_tool, get_attachments_tool]
```

---

### **Phase 5: Celery Task Queue**

#### 5.1 Implement `src/celery/app.py`

```python
"""Celery application configuration."""

from celery import Celery
from src.config import settings

celery_app = Celery(
    "reze",
    broker=settings.celery.celery_broker_url,
    backend=settings.celery.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)
```

#### 5.2 Implement `src/celery/tasks/email_tasks.py`

```python
"""Celery tasks for email operations."""

from celery import current_task
from loguru import logger

from src.celery.app import celery_app
from src.services.resend import resend_service
from src.services.ai import ai_service
from src.services.rag import rag_service


@celery_app.task(bind=True)
def send_email_with_ai_task(
    self,
    recipient: str,
    user_request: str,
    conversation_id: str = None
):
    """
    Celery task to send email with AI-generated content.
    Updates progress via SSE-compatible callbacks.
    """
    try:
        # Update progress
        self.update_state(state="PROGRESS", meta={"status": "Analyzing request..."})

        # Use AI to understand the request
        agent = ai_service.get_agent()
        result = agent.run_sync(user_request)

        # Extract or generate email details
        # This is where the AI determines subject and content
        email_content = result.data

        # Update progress
        self.update_state(state="PROGRESS", meta={"status": "Sending email..."})

        # Send the email
        send_result = resend_service.send_email(
            to=recipient,
            subject="AI Generated Email",  # AI would determine this
            html_content=email_content
        )

        logger.info(f"Email sent via Celery: {send_result['id']}")

        return {
            "status": "success",
            "email_id": send_result["id"],
            "message": "Email sent successfully"
        }

    except Exception as e:
        logger.error(f"Celery task failed: {e}")
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise


@celery_app.task(bind=True)
def check_email_status_task(self, email_id: str):
    """
    Celery task to check email status.
    """
    try:
        self.update_state(state="PROGRESS", meta={"status": "Checking status..."})

        status_result = resend_service.get_email_status(email_id)

        return {
            "status": "success",
            "email_id": email_id,
            "email_status": status_result.get("status")
        }

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise
```

---

### **Phase 5: API Layer**

#### 6.1 Create `src/api/schemas/chat.py`

```python
"""Chat schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """Request for chatting with agent."""
    message: str = Field(..., description="User's message to the agent")
    conversation_id: Optional[str] = Field(
        None, 
        description="Conversation ID (auto-generated if not provided)"
    )
    streaming: bool = Field(
        default=True, 
        description="Always true - native FastAPI streaming"
    )


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="ISO timestamp")


class ConversationHistoryResponse(BaseModel):
    """Response for conversation history."""
    conversation_id: str
    messages: list[ChatMessage]
    message_count: int


class ConversationsListResponse(BaseModel):
    """Response for listing conversations."""
    conversations: list[str]
    total: int
```

#### 5.2 Create `src/api/routers/chat_router.py`

```python
"""Chat router - Single endpoint for all interactions."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from src.api.schemas.chat import ChatRequest
from src.services.ai import ai_service
from src.services.rag import rag_service
from src.services.conversation import conversation_memory

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post(
    "/message",
    summary="Chat with Reze AI Agent (Streaming)"
)
async def chat_message(request: ChatRequest):
    """
    Chat with Reze AI agent.
    
    This is the ONLY way to interact with Reze.
    
    **How it works:**
    1. Send a message
    2. Agent responds with streaming text
    3. Agent may ask questions if info is missing
    4. Agent calls tools when needed (send_email, get_status, etc.)
    5. Continue conversation until task is complete
    
    **Example Flow:**
    ```
    You: "Send an email to john@example.com"
    Reze: "Sure! What's the subject?"
    You: "Welcome to our platform"
    Reze: "Got it. What content should I include? Do you want HTML or plain text?"
    You: "Just a simple text message saying thanks"
    Reze: [Calls send_email tool] "Email sent! ID: abc123"
    ```
    
    - **message**: Your message to the agent
    - **conversation_id**: Track conversation (optional, auto-generated if not provided)
    - **streaming**: Always true (native FastAPI streaming)
    """
    try:
        # Get or create conversation
        conversation_id = request.conversation_id or conversation_memory.create_conversation()
        
        # Save user message
        conversation_memory.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message
        )
        
        # Get AI agent
        agent = ai_service.get_agent()
        
        # Async generator for streaming
        async def stream_chat():
            """Stream agent response."""
            full_response = ""
            
            try:
                # Run agent with streaming
                async with agent.run_stream(request.message) as result:
                    async for chunk in result:
                        # Yield each chunk to user
                        full_response += chunk.content
                        yield chunk.content
                
                # Save assistant's response
                conversation_memory.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response
                )
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"\n\n[Error: {str(e)}]"
        
        # Return streaming response
        return StreamingResponse(
            stream_chat(),
            media_type="text/plain",
            headers={
                "X-Conversation-ID": conversation_id,
                "Cache-Control": "no-cache",
            }
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/conversations/{conversation_id}/history",
    summary="Get conversation history"
)
async def get_conversation_history(conversation_id: str):
    """Get full conversation history."""
    try:
        history = conversation_memory.get_conversation_history(conversation_id)
        return {
            "conversation_id": conversation_id,
            "messages": history,
            "message_count": len(history)
        }
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/conversations",
    summary="List all conversations"
)
async def list_conversations():
    """List all conversation IDs."""
    try:
        conversations = conversation_memory.list_conversations()
        return {
            "conversations": conversations,
            "total": len(conversations)
        }
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/conversations/{conversation_id}",
    summary="Delete conversation"
)
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    try:
        conversation_memory.delete_conversation(conversation_id)
        return {"message": "Conversation deleted"}
    except Exception as e:
        logger.error(f"Failed to delete: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

### **Phase 6: Prompts**

#### 6.1 Create `src/prompts/reze_agent.py`

```python
"""Reze AI Agent system prompts."""

REZE_AGENT_PERSONA = """
You are Reze, an intelligent AI assistant for Resend.com. Your mission is to help users:
1. Send emails efficiently through the Resend API
2. Generate email content based on user requests
3. Check email delivery status
4. Retrieve email attachments
5. Explain Resend's features and capabilities

You are professional, helpful, and efficient. When users ask you to send an email:
- If they provide subject and content, use those directly
- If they provide only a natural language request, generate appropriate subject and HTML content
- Always ensure email addresses are valid
- Format HTML content properly

You have access to Resend.com's API documentation through a RAG system.
"""

REZE_SYSTEM_INSTRUCTIONS = """
## Email Sending Guidelines

1. **When subject and content are provided:**
   - Use them as-is
   - Validate email format
   - Send via Resend API

2. **When only a natural language request is provided:**
   - Analyze the request to understand intent
   - Generate a clear, concise subject line
   - Create professional HTML content
   - Include relevant details from the request

3. **Email content generation:**
   - Use professional language
   - Structure HTML properly with paragraphs, headings
   - Include a clear call-to-action if appropriate
   - Keep it concise but complete

4. **Error handling:**
   - Validate all inputs before sending
   - Report issues clearly to the user
   - Suggest fixes when possible

5. **Documentation queries:**
   - Use the RAG system to find relevant info
   - Provide accurate, up-to-date information
   - Link to official docs when helpful

Always prioritize user experience and email deliverability.
"""

RESEND_DOCS_SOURCES = [
    "https://resend.com/docs/api-reference",
    "https://resend.com/docs/send-with-api",
    "https://resend.com/docs/email-delivery",
    "https://resend.com/docs/domains",
    "https://resend.com/docs/webhooks",
    "https://resend.com/docs/attachments",
]
```

#### 6.2 Update `src/prompts/__init__.py`

```python
"""Prompts module for Reze AI Agent."""

from .reze_agent import (
    REZE_AGENT_PERSONA,
    REZE_SYSTEM_INSTRUCTIONS,
    RESEND_DOCS_SOURCES,
)

__all__ = [
    "REZE_AGENT_PERSONA",
    "REZE_SYSTEM_INSTRUCTIONS",
    "RESEND_DOCS_SOURCES",
]
```

---

### **Phase 7: Documentation**

#### 7.1 Update `README.md`

```markdown
# Reze AI Agent

An intelligent AI agent for Resend.com that sends emails via natural language, tracks delivery status, and provides API assistance using RAG.

## Features

- 🤖 **AI-Powered Email Sending**: Describe what you want, Reze generates and sends it
- 📊 **Email Tracking**: Check delivery status and retrieve attachments
- 🔍 **RAG Documentation**: Memvid-powered knowledge from Resend.com docs
- 🚀 **Background Processing**: Celery tasks handle email operations
- 📡 **Real-Time Streaming**: Native FastAPI streaming responses
- 🧠 **GLM 4.7 AI**: Powered by z.ai's advanced language model

## Architecture

```
FastAPI + PydanticAI (async)
    ↓
 GLM 4.7 (z.ai) + Memvid RAG
     ↓
 Resend.com API (httpx)
     ↓
 SSE Streaming Responses
```

## Quick Start

### Prerequisites

- Python 3.12+
 - Resend API key
 - GLM 4.7 API key from z.ai

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/reze-ai-agent.git
cd reze-ai-agent

# Install dependencies
uv sync

# Copy environment file
cp env.example .env

# Edit .env with your API keys
nano .env
```

### Environment Variables

```env
# GLM 4.7 AI
GLM_API_KEY=your_glm_api_key
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
GLM_MODEL=glm-4.7

# Resend.com
RESEND_API_KEY=re_xxxxxxxxxxxx
RESEND_FROM_EMAIL=noreply@yourdomain.com

# Memvid RAG
MEMVID_FILE_PATH=./memory.mv2

# Database & Redis
DATABASE_URL=sqlite+aiosqlite:///./database
REDIS_URL=redis://localhost:6379/0

```

### Running the Application

```bash
# Start Redis (if not running)
docker run -d -p 6379:6379 redis:7-alpine

# Start Celery worker
celery -A src.celery.app worker --loglevel=info

# Start FastAPI server
uvicorn main:app --reload
```

### Docker (All-in-One)

```bash
docker compose up --build
```

## Usage Examples

### 1. Send Email with AI-Generated Content

```bash
curl -X POST http://localhost:8000/api/emails/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "user@example.com",
    "user_request": "Send a welcome email to John welcoming him to our platform"
  }'
```

Response:
```json
{
  "email_id": "email_789",
  "status": "queued",
  "created_at": "2024-01-15T10:30:00Z",
  "message": "Email sent successfully"
}
```

### 3. Send Email with Explicit Content

```bash
curl -X POST http://localhost:8000/api/emails/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "user@example.com",
    "subject": "Monthly Newsletter",
    "html_content": "<p>Here is your monthly newsletter!</p>",
    "user_request": "Send newsletter"
  }'
```

### 4. Check Email Delivery Status

```bash
curl http://localhost:8000/api/emails/email_789/status
```

### 5. Get Email Attachments

```bash
curl http://localhost:8000/api/emails/email_789/attachments
```

## API Documentation

Interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### Email Operations
- `POST /api/emails/send` - Send to email (async)
- `GET /api/emails/{email_id}/status` - Get to email delivery status
- `GET /api/emails/{email_id}/attachments` - Get attachments

## Project Structure

```
.
├── src/
│   ├── api/
│   │   ├── routers/     # API endpoints
│   │   └── schemas/     # Pydantic models
│   ├── services/
│   │   ├── ai.py        # GLM 4.7 integration
│   │   ├── rag.py       # Memvid RAG
│   │   ├── resend.py    # Resend API (httpx)
│   │   └── memvid.py
│   ├── tools/           # PydanticAI tools
│   ├── database/        # Database models
│   ├── prompts/         # System prompts
│   └── config.py        # Configuration
├── tests/               # Pytest tests
├── docs/                # Documentation
├── main.py              # Entry point
├── pytest.ini           # Test configuration
├── compose.yml          # Docker Compose
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_resend_service.py

# Run async tests
pytest tests/test_ai_service.py -v
```

## Development

### Adding New Tools

1. Create tool function in `src/tools/`
2. Add tool to `ALL_TOOLS` list
3. Tool will be automatically available to agent
4. Agent decides when to call tools

### Adding New Conversations

Conversation management is handled by `src/services/conversation.py`:
- `create_conversation()` - Generate unique ID
- `add_message()` - Store messages
- `get_conversation_history()` - Retrieve history
- `delete_conversation()` - Remove conversation

### Testing Locally

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Access application
open http://localhost:8000/docs
```

## License

MIT
```

---

### **Phase 8: Testing**

#### 8.1 Create `tests/test_resend_service.py`

```python
"""Tests for Resend service."""

import pytest
from unittest.mock import patch, MagicMock
from src.services.resend import ResendService


@pytest.fixture
def resend_service():
    return ResendService()


@pytest.mark.asyncio
async def test_send_email(resend_service):
    """Test sending email."""
    with patch('resend.Emails.send') as mock_send:
        mock_send.return_value = {"id": "email_123"}

        result = await resend_service.send_email(
            to="test@example.com",
            subject="Test",
            html_content="<p>Test</p>"
        )

        assert result["id"] == "email_123"
```

#### 8.2 Create `tests/test_ai_service.py`

```python
"""Tests for AI service."""

import pytest
from src.services.ai import AIService


@pytest.fixture
def ai_service():
    return AIService()


def test_get_agent(ai_service):
    """Test getting AI agent."""
    agent = ai_service.get_agent()
    assert agent is not None


@pytest.mark.asyncio
async def test_agent_run(ai_service):
    """Test agent run."""
    agent = ai_service.get_agent()
    result = await agent.run("Hello")

    assert result.data is not None
```

---

### **Phase 9: Cleanup**

#### 9.1 Remove WhatsApp-specific files

```bash
# Remove files
rm -rf src/api/routers/whatsapp_router.py
rm -rf src/api/processors/
rm -rf src/tools/location.py
rm -rf src/services/speech_to_text.py
rm -rf src/services/whatsapp.py
rm -rf src/prompts/config/
rm -rf src/prompts/context/
rm -rf src/prompts/managers/
```

#### 9.2 Update main.py

```python
"""Reze AI Agent - Main entry point."""

import uvicorn
from loguru import logger

from src.config import settings


def main() -> None:
    """Run the FastAPI application."""
    uvicorn.run(
        "src.api.app:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level=settings.app.log_level.lower(),
    )


if __name__ == "__main__":
    main()
```

---

## 📝 Summary

### Total Files: ~30

**Configuration (4):**
- pyproject.toml
- env.example
- pytest.ini
- Dockerfile

**Services (5):**
- src/services/ai.py
- src/services/rag.py
- src/services/embeddings.py
- src/services/resend.py
- src/services/memvid.py

**API Layer (3):**
- src/api/app.py
- src/api/routers/chat_router.py
- src/api/schemas/chat.py

**Tools & Prompts (3):**
- src/tools/resend_tools.py
- src/prompts/reze_agent.py
- src/prompts/__init__.py

**Database (2):**
- src/database/models.py
- src/database/session.py

**Tests (3+):**
- tests/test_resend_service.py
- tests/test_ai_service.py
- tests/test_streaming.py
- tests/test_api.py

**Documentation (2):**
- README.md
- docs/IMPLEMENTATION_PLAN.md

---

## ⚠️ Important Notes

1. **GLM 4.7 API**: Ensure base_url and api_key are correct
2. **Memvid File**: `.mv2` file created on first run
3. **Native Streaming**: Use `agent.run_stream()` with `StreamingResponse` for real-time chat
4. **Tool Calling**: Agent automatically decides when to call tools based on conversation
5. **Async/Await**: Ensure all external calls use httpx with async
5. **Security**: Never commit API keys
6. **Error Handling**: Add comprehensive error handling

---

## 📚 Resources

- [PydanticAI](https://ai.pydantic.dev/)
- [Memvid](https://docs.memvid.com/)
- [GLM 4.7](https://z.ai/)
- [Resend API](https://resend.com/docs)
- [FastAPI Streaming](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [StreamingResponse](https://fastapi.tiangolo.com/api-reference/#streamingresponse)


---