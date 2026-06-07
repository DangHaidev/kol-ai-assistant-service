# 09 - Repo Structure

## 1. Cấu trúc repo đề xuất

```txt
kol-ai-assistant-service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── chat.py
│   │       └── recommendations.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── criteria.py
│   │   ├── recommendation.py
│   │   └── kol.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── conversation.py
│   │   └── message.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── conversation_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── conversation_service.py
│   │   ├── intent_service.py
│   │   ├── criteria_service.py
│   │   ├── kol_retrieval_service.py
│   │   ├── ranking_service.py
│   │   └── response_service.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── kol_chat_graph.py
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── llm_client.py
│   │   └── kol_backend_client.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── intent_prompt.py
│   │   ├── criteria_prompt.py
│   │   ├── clarification_prompt.py
│   │   └── response_prompt.py
│   └── utils/
│       ├── __init__.py
│       ├── json_utils.py
│       └── text_normalizer.py
├── migrations/
│   ├── env.py
│   └── versions/
│       └── 001_create_ai_tables.py
├── tests/
│   ├── test_health.py
│   ├── test_criteria_service.py
│   ├── test_ranking_service.py
│   └── test_chat_flow.py
├── docs/
│   ├── 01-product-requirements.md
│   ├── 02-architecture.md
│   ├── 03-api-contract.md
│   ├── 04-database-design.md
│   ├── 05-ai-workflow.md
│   ├── 06-prompts.md
│   ├── 07-ranking-logic.md
│   └── 08-implementation-roadmap.md
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
└── README.md
```

## 2. `.env.example`

```env
APP_NAME=KOL AI Assistant Service
APP_ENV=development
APP_PORT=8001

DATABASE_URL=postgresql+asyncpg://kol_ai_user:kol_ai_secret@localhost:5433/kol_ai

SPRING_BACKEND_BASE_URL=http://localhost:8080
SPRING_BACKEND_INTERNAL_TOKEN=change_me

LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

REQUEST_TIMEOUT_SECONDS=10
MAX_RECOMMENDATION_CANDIDATES=50
DEFAULT_TOP_K=5
```

## 3. `requirements.txt`

```txt
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy
asyncpg
alembic
httpx
python-dotenv
langgraph
langchain
openai
pytest
pytest-asyncio
```

## 4. `.gitignore`

```gitignore
.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
.mypy_cache/
.DS_Store
.idea/
.vscode/
```

## 5. File code khởi đầu

### `app/core/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "KOL AI Assistant Service"
    app_env: str = "development"
    database_url: str
    spring_backend_base_url: str = "http://localhost:8080"
    spring_backend_internal_token: str | None = None
    llm_provider: str = "openai"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    request_timeout_seconds: int = 10
    max_recommendation_candidates: int = 50
    default_top_k: int = 5

    class Config:
        env_file = ".env"

settings = Settings()
```

### `app/main.py`

```python
from fastapi import FastAPI
from app.api.routes import health, chat, recommendations
from app.core.config import settings

app = FastAPI(title=settings.app_name)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])
```

### `app/api/routes/health.py`

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "kol-ai-assistant-service"}
```

## 6. Quy ước code

### Naming

- File Python: `snake_case.py`.
- Class: `PascalCase`.
- Function: `snake_case`.
- API field giữ camelCase nếu frontend/backend chính đang dùng camelCase.

### DTO

Dùng Pydantic cho tất cả request/response.

### Service layer

Không viết logic nhiều trong route/controller.

Sai:

```python
@router.post("/chat")
async def chat(request):
    # xử lý LLM, DB, ranking ngay trong controller
```

Đúng:

```python
@router.post("/chat")
async def chat(request: ChatRequest):
    return await chat_service.handle_chat(request)
```

## 7. Commit roadmap đề xuất

```txt
commit 1: init FastAPI project structure
commit 2: add schemas and health endpoint
commit 3: add mock chat endpoint
commit 4: add ranking service with tests
commit 5: add LLM client and criteria extraction
commit 6: add database models and migrations
commit 7: add conversation memory
commit 8: add LangGraph workflow
commit 9: add Spring Boot backend client
commit 10: add Docker setup
```
