# MCP-Powered Developer Assistant

> AI-powered development assistant that exposes GitHub, Docker, and filesystem operations through FastAPI and Model Context Protocol (MCP). Built with LangChain for intelligent agent workflows.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3%2B-orange.svg)](https://www.langchain.com/)

## 🌟 Features

### 🐙 GitHub Integration
- **Search repositories** by keyword with configurable results
- **Create and manage issues** in any repository
- **Fetch repository information** (stars, forks, description, language)
- **Read file contents** from repositories with branch support
- **List issues** with state filtering (open/closed/all)

### 🐳 Docker Management
- **List containers** (all or running only)
- **Start/stop containers** with timeout configuration
- **View container logs** with tail and timestamp options
- **Get real-time statistics** (CPU, memory, network I/O)
- **Deploy new services** from Docker images

### 📁 Filesystem Operations
- **Read/write files** with UTF-8 encoding
- **List directory contents** with hidden file support
- **Search files by pattern** (supports wildcards: `*.py`, `test_*`)
- **Get file statistics** (size, dates, permissions)
- **Secure path validation** (restricted to allowed directories)

### 🤖 AI-Powered Agent
- **Natural language queries** using LangChain ReAct agent
- **Multi-tool chaining** (agent intelligently uses multiple operations)
- **Code analysis** with quality assessment and security review
- **Repository analysis** with technology stack identification
- **Conversation memory** for contextual interactions

## 🏗️ Architecture

```
AI Agent (Claude/ChatGPT)
         ↓
   MCP Protocol
         ↓
   FastAPI Server → LangChain Agent → GPT-4
         ↓
   [GitHub | Docker | Filesystem]
```

## 📋 Prerequisites

- **Python 3.10+**
- **Docker** (for Docker management features)
- **GitHub Personal Access Token** (for GitHub operations)
- **OpenAI API Key** (for AI agent features)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd mcp-dev-assistant
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file from the example:

```bash
cp env.example .env
```

Edit `.env` with your credentials:

```env
# GitHub Configuration
GITHUB_TOKEN=ghp_your_github_personal_access_token

# OpenAI Configuration (for LangChain)
OPENAI_API_KEY=sk-your_openai_api_key

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

**Getting Tokens:**
- **GitHub Token**: [Create here](https://github.com/settings/tokens) (needs `repo` scope for private repos)
- **OpenAI Key**: [Get from OpenAI](https://platform.openai.com/api-keys)

### 3. Run Server

```bash
python main.py
```

Server will start at `http://localhost:8000`

**Check it's running:**
```bash
curl http://localhost:8000/health
```

### 4. Explore API

Open interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Endpoints

### Health & Info
- `GET /` - Service health check
- `GET /health` - Configuration status
- `GET /mcp/tools` - List available MCP tools

### GitHub Operations (`/github`)
- `GET /github/search-repos?query={query}&max_results={n}` - Search repositories
- `GET /github/repo/{owner}/{repo}` - Get repository info
- `POST /github/issues` - Create issue
- `GET /github/issues/{owner}/{repo}?state={state}` - List issues
- `GET /github/file/{owner}/{repo}?path={path}&branch={branch}` - Get file content

### Docker Operations (`/docker`)
- `GET /docker/containers?all={bool}` - List containers
- `POST /docker/containers/{id}/start` - Start container
- `POST /docker/containers/{id}/stop?timeout={seconds}` - Stop container
- `GET /docker/containers/{id}/logs?tail={lines}` - Get logs
- `GET /docker/containers/{id}/stats` - Get statistics
- `POST /docker/deploy` - Deploy new service

### Filesystem Operations (`/filesystem`)
- `GET /filesystem/read?path={path}` - Read file
- `POST /filesystem/write` - Write file
- `GET /filesystem/list?path={path}` - List directory
- `GET /filesystem/search?pattern={pattern}&recursive={bool}` - Search files
- `GET /filesystem/stats?path={path}` - Get file stats

### AI Agent (`/ai`)
- `POST /ai/agent/query` - Natural language query
- `POST /ai/agent/clear-memory` - Clear conversation history
- `POST /ai/analysis/code` - Analyze code quality
- `POST /ai/analysis/repository` - Analyze repository

## 💡 Usage Examples

### Search GitHub Repositories

```bash
curl "http://localhost:8000/github/search-repos?query=fastapi&max_results=3"
```

### AI Agent Query

```bash
curl -X POST "http://localhost:8000/ai/agent/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Search for FastAPI repositories, get info about the top result, and list its main files"
  }'
```

### Analyze Code Quality

```bash
curl -X POST "http://localhost:8000/ai/analysis/code" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "tiangolo",
    "repo": "fastapi",
    "file_path": "fastapi/applications.py"
  }'
```

### List Docker Containers

```bash
curl "http://localhost:8000/docker/containers?all=true"
```

### Search Local Files

```bash
curl "http://localhost:8000/filesystem/search?pattern=*.py&recursive=true"
```

## 🔌 Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "dev-assistant": {
      "command": "python",
      "args": [
        "C:/path/to/your/MCP/main.py"
      ],
      "env": {
        "GITHUB_TOKEN": "your_github_token",
        "OPENAI_API_KEY": "your_openai_key"
      }
    }
  }
}
```

**Then try in Claude:**
- "Search for Python web frameworks on GitHub"
- "List all my Docker containers"
- "Analyze the code quality of main.py in the FastAPI repository"

## 🛠️ Tech Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern web framework
- **[FastAPI-MCP](https://github.com/modelcontextprotocol/fastapi-mcp)** - MCP protocol integration
- **[LangChain](https://www.langchain.com/)** - AI agent orchestration
- **[LangChain-OpenAI](https://python.langchain.com/docs/integrations/platforms/openai)** - GPT-4 integration
- **[PyGithub](https://github.com/PyGithub/PyGithub)** - GitHub API wrapper
- **[Docker SDK](https://docker-py.readthedocs.io/)** - Docker API client
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server

## 📁 Project Structure

```
mcp-dev-assistant/
├── main.py                          # FastAPI app entry point
├── requirements.txt                 # Dependencies
├── env.example                      # Environment template
├── README.md                        # This file
├── config/
│   └── settings.py                  # Configuration management
├── services/
│   ├── github_service.py            # GitHub operations (241 lines)
│   ├── docker_service.py            # Docker operations (272 lines)
│   └── filesystem_service.py        # File operations (281 lines)
├── schemas/
│   └── models.py                    # Pydantic models (139 lines)
├── langchain_integration/
│   ├── agent.py                     # ReAct agent (208 lines)
│   ├── chains.py                    # Analysis chains (286 lines)
│   └── service.py                   # AI endpoints (153 lines)
└── mcp_tools/
    └── __init__.py                  # MCP tools metadata
```

**Total: ~1,500 lines of professional Python code**

## 🔒 Security Features

### Path Validation
Filesystem operations are restricted to:
- Current working directory
- User home directory

### Error Handling
- Proper HTTP status codes (400, 403, 404, 500, 503)
- Detailed error messages
- Input validation with Pydantic

### Docker Safety
- Connection checks before operations
- Timeout configurations
- Status validation

## 🎯 AI Agent Capabilities

The LangChain agent uses the **ReAct (Reasoning + Acting)** pattern:

1. **Reasoning**: Agent thinks about what to do
2. **Action**: Agent selects a tool to use
3. **Observation**: Agent sees the result
4. **Repeat**: Until task is complete

**Available Tools:**
- `search_github_repos` - Search repositories
- `get_repo_info` - Get repo details
- `get_github_file` - Read files from repos
- `list_docker_containers` - List containers
- `get_container_logs` - Get logs
- `read_file` - Read local files
- `list_directory` - List directories
- `search_files` - Search by pattern

**Example Multi-Step Query:**
```
"Find the most popular FastAPI repository, read its README, 
analyze the code quality, and summarize the project"
```

The agent will:
1. Search for FastAPI repos
2. Get top result info
3. Fetch README file
4. Run code analysis
5. Generate summary

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### List All Endpoints
```bash
curl http://localhost:8000/openapi.json | jq '.paths | keys'
```

### Test GitHub (no auth needed for public repos)
```bash
curl "http://localhost:8000/github/search-repos?query=python"
```

### Test Filesystem
```bash
curl "http://localhost:8000/filesystem/list?path=."
```

## 🐛 Troubleshooting

### "GitHub token not configured"
- Make sure `.env` file exists with `GITHUB_TOKEN`
- Restart the server after adding the token

### "Docker is not available"
- Ensure Docker Desktop is running
- Check Docker daemon status: `docker ps`

### "OPENAI_API_KEY not configured"
- Add your OpenAI API key to `.env`
- AI endpoints won't work without it

### Server won't start
- Check if port 8000 is already in use
- Change port in `.env`: `PORT=8001`

## 📈 Performance

- **Response Time**: < 100ms for most operations
- **Docker Stats**: Real-time CPU/memory metrics
- **LLM Calls**: ~2-5s for AI agent queries
- **Code Analysis**: ~3-10s depending on file size

## 🛣️ Roadmap

- [ ] Add authentication/API keys
- [ ] WebSocket support for real-time logs
- [ ] Database integration for caching
- [ ] More AI analysis chains (security audit, performance profiling)
- [ ] Docker Compose support
- [ ] Kubernetes integration
- [ ] GitHub Actions integration

## 📝 License

MIT License - feel free to use this project however you like!

## 🤝 Contributing

Contributions welcome! This is a professional-grade project with:
- Clean architecture
- Type hints throughout
- Comprehensive error handling
- Detailed documentation




