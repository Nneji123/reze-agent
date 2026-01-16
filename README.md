# Reze AI Agent

An intelligent AI agent for Resend.com that sends emails via natural language, tracks delivery status, and provides API assistance using RAG.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12+-green)
![License](https://img.shields.io/badge/license-MIT-purple)

## ✨ Features
## Features

- 💬 **Chat-Only Interface**: Interact through natural conversation
- 🤖 **AI Agent**: Agent asks clarifying questions when needed
- 📧 **Email Operations**: Send emails, check status, retrieve attachments via chat
- 🔍 **RAG Documentation**: Memvid-powered knowledge from Resend.com docs
- 📡 **Real-Time Streaming**: See agent's responses in real-time
- 🧠 **GLM 4.7 AI**: Powered by z.ai's advanced language model
- 🔄 **Multi-Turn Conversations**: Continue until task is complete

## 🏗️ Architecture

```
User Request
    ↓
FastAPI Endpoint
    ↓
AI Agent (GLM 4.7) + Memvid RAG
    ↓
Resend.com API
    ↓
Streaming Response
```

## ⚡ Quick Start (5 Minutes)

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment (edit .env with your API keys)
cp env.example .env

# 3. Start the server
uv run python main.py

# 4. Open chat interface
# Visit: http://localhost:8000
# Or test with curl:
curl -N -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "conversation_id": null, "streaming": true}'
```

**That's it!** The application is now running with:
- ✅ SQLite database (auto-created)
- ✅ Memvid RAG (empty, ready for docs)
- ✅ GLM 4.7 AI agent
- ✅ Beautiful chat interface at http://localhost:8000

To populate Memvid with Resend.com documentation:
```bash
uv run python scripts/populate_memvid.py
```

## 🚀 Quick Start

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
# Required: GLM_API_KEY and RESEND_API_KEY

# (Optional) Populate Memvid with Resend.com documentation
uv run python scripts/populate_memvid.py
```

### Environment Variables

Required variables in `.env`:

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

# Database
DATABASE_URL=sqlite+aiosqlite:///./database.db
```

### Running Application

```bash
# Start FastAPI server
uv run python main.py

# Or with uvicorn directly
uvicorn src.api.app:app --reload

# Access chat interface
open http://localhost:8000

# Access API docs
open http://localhost:8000/docs
```

### Docker (Optional)

```bash
# Start application
docker compose up --build

# View logs
docker compose logs -f
```

## 📖 Usage Examples

## 💬 Usage Examples

**Reze is a chat-only AI agent.** Just like ChatGPT, you chat with it and it uses tools to perform actions.

### Example 1: Send an Email via Chat

```bash
curl -N -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Send an email to john@example.com welcoming him to our platform",
    "conversation_id": null,
    "streaming": true
  }'
```

**Streaming Response:**
```
Sure! I'll help you send a welcome email to John.

What subject line would you like for the email?
```

**User continues:**
```bash
curl -N -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Welcome to Our Platform",
    "conversation_id": "conv_abc123",
    "streaming": true
  }'
```

**Agent asks more questions, then sends email:**
```
Got it! What should the email content be? Would you like it in HTML or plain text?
```

Eventually the agent calls the `send_email` tool and you'll see:
```
✓ Email sent successfully! Email ID: email_xyz789
```

### Example 2: Check Email Status

```bash
curl -N -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Check the status of email email_xyz789",
    "streaming": true
  }'
```

**Agent responds:**
```
The email email_xyz789 was successfully delivered to john@example.com at 2024-01-15T10:30:00Z.
```

### Example 3: Ask About Resend Features

```bash
curl -N -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the email size limits with Resend?",
    "streaming": true
  }'
```

**Agent uses RAG to answer:**
```
According to Resend.com documentation, the email size limits are:
- Maximum email size: 40 MB
- Maximum attachment size: 40 MB total per email
- Maximum number of attachments: Unlimited, but total size cannot exceed 40 MB

Source: https://resend.com/docs/send-with-api/attachments
```

### Example 4: Multiple Chat Sessions

You can have separate conversations for different tasks:

```bash
# Session 1: Work emails
curl -N -X POST http://localhost:8000/api/chat/message \
  -d '{"message": "Send project update to team", "conversation_id": "work_session"}'

# Session 2: Personal emails
curl -N -X POST http://localhost:8000/api/chat/message \
  -d '{"message": "Email mom about dinner plans", "conversation_id": "personal_session"}'
```

Each session maintains its own context and conversation history.

## 📚 API Documentation

Interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🛣️ Endpoints

### Chat Operations (Only Endpoints)

| Method | Endpoint | Description |
|---------|-----------|-------------|
| POST | `/api/chat/message` | Chat with AI agent (streaming) |
| GET | `/api/chat/conversations` | List all chat sessions |
| GET | `/api/chat/conversations/{id}/history` | Get conversation history |
| DELETE | `/api/chat/conversations/{id}` | Delete a session |

**Note:** All interactions happen through chat. The AI agent internally uses tools to send emails, check status, etc.

## 📁 Project Structure

```
reze-ai-agent/
├── src/
│   ├── api/
│   │   ├── routers/
│   │   │   └── chat_router.py     # Chat endpoint (ONLY endpoint)
│   │   ├── schemas/
│   │   │   └── chat.py            # Chat schemas
│   │   └── app.py                 # FastAPI app
│   ├── services/
│   │   ├── ai.py                  # GLM 4.7 integration
│   │   ├── rag.py                 # Memvid RAG
│   │   ├── resend.py              # Resend API (httpx)
│   │   ├── memvid.py      # Memvid service
│   │   ├── conversation.py        # Conversation management
│   │   └── streaming.py          # Streaming handler
│   ├── tools/
│   │   └── resend_tools.py        # PydanticAI tools
│   ├── database/
│   │   ├── models.py             # Database models
│   │   └── session.py            # DB session
│   ├── prompts/
│   │   ├── reze_agent.py         # System prompts
│   │   └── __init__.py
│   └── config.py                 # Configuration
├── tests/
│   ├── test_resend_service.py
│   ├── test_ai_service.py
│   └── test_celery_tasks.py
├── docs/
│   └── IMPLEMENTATION_PLAN.md
├── main.py                       # Entry point
├── pytest.ini                    # Test config
├── pyproject.toml                # Dependencies
├── compose.yml                   # Docker Compose
└── README.md
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_resend_service.py

# Run async tests
pytest tests/test_ai_service.py -v

# Repopulate Memvid with latest docs
uv run python scripts/populate_memvid.py
```

```bash
# Run with markers
pytest -m unit
pytest -m integration
```

## 🔧 Development

### Adding New Endpoints

1. Create async function in services
2. Use httpx for external API calls
3. Add endpoint in router with proper error handling
4. Document with FastAPI docstrings

### Managing Memvid Knowledge Base

The `scripts/populate_memvid.py` script handles documentation ingestion:

```bash
# Populate with Resend.com docs (direct URLs)
uv run python scripts/populate_memvid.py

# To crawl and discover more pages
# Edit the script and set discover=True
```

The script:
- Fetches documentation from Resend.com
- Parses HTML and extracts content
- Stores in Memvid for RAG
- Supports both direct URL lists and site crawling

### Running Locally

```bash
# Start server
uv run python main.py

# View logs in another terminal
tail -f logs/app.log

# Test application
uv run python test_app.py

# Access chat interface
open http://localhost:8000
```

## 🛠️ Tech Stack

- **Framework**: FastAPI + PydanticAI
- **AI Model**: GLM 4.7 (z.ai) - OpenAI-compatible
- **RAG System**: Memvid (single-file, hybrid search)
- **Email Service**: Resend.com API (httpx)
- **Conversation Management**: In-memory + SQLite persistence
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Testing**: Pytest

## 📋 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/your-org/reze-ai-agent/issues)
- 💬 [Discussions](https://github.com/your-org/reze-ai-agent/discussions)

## 🙏 Acknowledgments

