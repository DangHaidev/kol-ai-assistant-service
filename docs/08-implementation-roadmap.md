# 08 - Implementation Roadmap

## Phase 0 - Chuẩn bị repo

### Task 0.1: Tạo repo

Tên repo đề xuất:

```txt
kol-ai-assistant-service
```

### Task 0.2: Tạo virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Task 0.3: Cài dependencies ban đầu

`requirements.txt` MVP:

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
```

Nếu dùng OpenAI:

```txt
openai
```

Nếu dùng Gemini:

```txt
google-generativeai
```

## Phase 1 - FastAPI base

### Task 1.1: Tạo `app/main.py`

```python
from fastapi import FastAPI
from app.api.routes import health, chat

app = FastAPI(title="KOL AI Assistant Service")

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
```

### Task 1.2: Tạo health endpoint

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "kol-ai-assistant-service"}
```

### Task 1.3: Chạy thử

```bash
uvicorn app.main:app --reload --port 8001
```

Mở:

```txt
http://localhost:8001/docs
```

## Phase 2 - Schemas

### Task 2.1: Tạo `KolSearchCriteria`

```python
from typing import Optional
from pydantic import BaseModel, Field

class KolSearchCriteria(BaseModel):
    category: Optional[str] = None
    platforms: list[str] = Field(default_factory=list)
    minFollowers: Optional[int] = None
    maxFollowers: Optional[int] = None
    minBudget: Optional[int] = None
    maxBudget: Optional[int] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    campaignGoal: Optional[str] = None
    serviceType: Optional[str] = None
```

### Task 2.2: Tạo Chat Request/Response

```python
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.criteria import KolSearchCriteria

class ChatRequest(BaseModel):
    brandId: int
    conversationId: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    conversationId: str
    reply: str
    intent: str
    criteria: KolSearchCriteria
    recommendations: list[dict] = Field(default_factory=list)
    needClarification: bool = False
    clarificationQuestions: list[str] = Field(default_factory=list)
```

## Phase 3 - Database conversation memory

### Task 3.1: Cấu hình database

`.env`:

```env
DATABASE_URL=postgresql+asyncpg://kol_ai_user:kol_ai_secret@localhost:5432/kol_ai
SPRING_BACKEND_BASE_URL=http://localhost:8080
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
```

### Task 3.2: Tạo model SQLAlchemy

Cần bảng:

```txt
ai_conversations
ai_messages
ai_recommendation_logs
```

### Task 3.3: Tạo repository

Functions cần có:

```python
create_conversation(brand_id)
get_conversation(conversation_id, brand_id)
update_current_criteria(conversation_id, criteria)
save_message(conversation_id, role, content, metadata)
get_messages(conversation_id, limit=20)
```

## Phase 4 - LLM client

### Task 4.1: Tạo abstraction

```python
class LlmClient:
    async def generate_json(self, prompt: str) -> dict:
        pass

    async def generate_text(self, prompt: str) -> str:
        pass
```

### Task 4.2: Implement provider

MVP có thể chọn một provider trước:

- OpenAI.
- Gemini.
- Groq.
- Ollama local.

Không hard-code provider vào service logic.

## Phase 5 - Intent + Criteria Extraction

### Task 5.1: Intent service

Input:

```txt
message
```

Output:

```json
{
  "intent": "recommend_kol",
  "confidence": 0.95
}
```

### Task 5.2: Criteria service

Input:

```txt
history
currentCriteria
message
```

Output:

```json
{
  "category": "fashion",
  "platforms": ["tiktok"],
  "minFollowers": 100000,
  "maxBudget": 10000000
}
```

### Task 5.3: Criteria merge

Merge criteria cũ và mới theo rule:

```txt
new value có dữ liệu → cập nhật
new value null → giữ old value
platforms → merge unique
```

## Phase 6 - KOL backend client

### Task 6.1: Tạo client gọi Spring Boot

```python
import httpx

class KolBackendClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def search_candidates(self, criteria: dict, limit: int = 50):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.base_url}/api/internal/kols/search-candidates",
                json={**criteria, "limit": limit},
            )
            response.raise_for_status()
            return response.json()["items"]
```

### Task 6.2: Nếu backend chưa có API này

Tạm thời mock data trước để code AI Service.

```python
async def search_candidates(self, criteria: dict, limit: int = 50):
    return [
        {
            "kolId": 1,
            "displayName": "Demo Fashion KOL",
            "categories": ["fashion"],
            "platforms": [
                {"platform": "tiktok", "followers": 150000, "engagementRate": 0.04}
            ],
            "priceFrom": 7000000,
            "averageRating": 4.7,
            "completedBookingCount": 12,
        }
    ]
```

## Phase 7 - Ranking Service

### Task 7.1: Implement score functions

Functions:

```python
calculate_category_score
calculate_platform_score
calculate_follower_score
calculate_budget_score
calculate_engagement_score
calculate_rating_score
calculate_booking_score
calculate_match_score
generate_reason
```

### Task 7.2: Return top K

```python
recommendations = sorted(candidates, key=lambda x: x["matchScore"], reverse=True)[:top_k]
```

## Phase 8 - LangGraph workflow

### Task 8.1: Tạo state

Dựa trên `05-ai-workflow.md`.

### Task 8.2: Tạo nodes

```txt
load_conversation
extract_intent
extract_criteria
merge_criteria
check_clarification
generate_clarification_response
retrieve_kol_candidates
rank_kols
generate_final_response
save_conversation
```

### Task 8.3: Wire graph

Dùng conditional edge:

```txt
needClarification true → generate_clarification_response
needClarification false → retrieve_kol_candidates
```

## Phase 9 - Chat endpoint integration

### Task 9.1: Controller gọi graph

```python
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = await chat_graph.ainvoke(request.model_dump())
    return ChatResponse(**result)
```

### Task 9.2: Test bằng Swagger

Case 1:

```json
{
  "brandId": 1,
  "conversationId": null,
  "message": "Tôi muốn tìm KOL thời trang follower trên 100k"
}
```

Case 2:

```json
{
  "brandId": 1,
  "conversationId": "uuid-from-case-1",
  "message": "Ưu tiên TikTok, ngân sách dưới 10 triệu"
}
```

## Phase 10 - Docker

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic.ini .
COPY migrations ./migrations

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### docker-compose.yml

```yaml
services:
  ai-service:
    build: .
    ports:
      - "8001:8001"
    env_file:
      - .env
    depends_on:
      - postgres-ai

  postgres-ai:
    image: postgres:16
    environment:
      POSTGRES_DB: kol_ai
      POSTGRES_USER: kol_ai_user
      POSTGRES_PASSWORD: kol_ai_secret
    ports:
      - "5433:5432"
    volumes:
      - postgres_ai_data:/var/lib/postgresql/data

volumes:
  postgres_ai_data:
```

## Phase 11 - Tích hợp với Spring Boot

### Task 11.1: Spring Boot gọi AI Service

Tạo module client trong backend chính:

```txt
kolbooking.datn.ai
├── AiAssistantClient.java
├── AiChatController.java
├── dto/
```

### Task 11.2: Frontend chỉ gọi Spring Boot

Không nên để frontend gọi thẳng AI Service nếu muốn giữ auth tập trung.

```txt
Frontend → Spring Boot → AI Service
```

## Phase 12 - Test checklist

### Test cases

- User nhập đủ thông tin → trả recommendation.
- User nhập thiếu category → bot hỏi thêm.
- User nhập tiếp thông tin → bot nhớ criteria cũ.
- LLM trả JSON lỗi → retry/fallback.
- Backend KOL API lỗi → trả message thân thiện.
- Không có KOL phù hợp → gợi ý nới điều kiện.

## Thứ tự code khuyên dùng

```txt
1. FastAPI base + health
2. Schemas
3. Mock Chat API không cần LLM
4. Ranking với mock KOL
5. LLM criteria extraction
6. Conversation DB
7. LangGraph
8. Backend client
9. Docker
10. Tích hợp Spring Boot
```
