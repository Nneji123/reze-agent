# Reze AI Agent

An intelligent AI assistant for Resend.com that sends emails via natural language, tracks delivery status, and provides API assistance using RAG.

[![License](https://img.shields.io/badge/license-MIT-purple)](https://github.com/Nneji123/reze-agent/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-green)](https://github.com/Nneji123/reze-agent)

## Features

- Chat-only interface through natural conversation
- Email operations: send emails, check status, retrieve attachments
- RAG documentation powered by Memvid with Resend.com docs
- Real-time streaming responses
- GLM 4.7 AI model via z.ai (OpenAI-compatible)
- Multi-turn conversations with full context memory
- Username-based conversation isolation
- Markdown rendering for formatted responses
- Persistent SQLite storage for conversation history

## Quick Start

```bash
# Install dependencies
pip install uv
uv sync

# Configure environment (edit .env with your API keys)
cp env.example .env

# Start server
uv run python main.py

# Visit chat interface at http://localhost:8000
```

## Environment Variables

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

## Usage Examples

### Send Email via Chat

```bash
curl -N -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Send an email to john@example.com welcoming him to our platform",
    "username": "user1"
  }'
```

Agent asks clarifying questions (subject, content), then sends email.

### Check Email Status

```bash
curl -N -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Check the status of that email",
    "conversation_id": "previous_conversation_id",
    "username": "user1"
  }'
```

Agent remembers context and checks delivery status.

### Ask About Resend Features

```bash
curl -N -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the email size limits?",
    "username": "user1"
  }'
```

Agent uses RAG to answer from Resend documentation.

## API Endpoints

Interactive API documentation available at: http://localhost:8000/docs

| Method | Endpoint | Description |
|---------|-----------|-------------|
| POST | `/api/chat/message` | Chat with AI agent (streaming) |
| GET | `/api/chat/conversations/{username}` | List user conversations |
| GET | `/api/chat/conversations/{id}/history` | Get conversation history |
| DELETE | `/api/chat/conversations/{id}` | Delete conversation |
| GET | `/health` | Health check endpoint |

## Tech Stack

- Backend: FastAPI, Python 3.12, SQLAlchemy (async)
- AI: PydanticAI, GLM 4.7 (z.ai), OpenAI-compatible API
- Knowledge Base: Memvid (semantic search)
- Database: SQLite + aiosqlite
- Frontend: Vanilla JavaScript with marked.js

## Populate Documentation

```bash
# Populate Memvid with Resend.com documentation
uv run python scripts/populate_memvid.py
```

## Architecture

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

## Project Structure

```
ai-resend-agent/
├── src/
│   ├── api/          # FastAPI routes and schemas
│   ├── services/      # AI, RAG, Resend, conversation
│   ├── tools/         # PydanticAI tools for Resend operations
│   ├── database/      # SQLAlchemy models and session
│   └── config.py     # Configuration
├── scripts/
│   └── populate_memvid.py
├── main.py           # Application entry point
└── README.md
```

## License

MIT License - see [LICENSE](https://github.com/Nneji123/reze-agent/blob/main/LICENSE) for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

- Issues: https://github.com/Nneji123/reze-agent/issues
- Discussions: https://github.com/Nneji123/reze-agent/discussions