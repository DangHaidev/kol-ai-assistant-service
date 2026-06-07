# TODO - KOL AI Assistant Service

Cap nhat lan cuoi: 2026-06-05

## Trang thai hien tai

Repo da duoc scaffold theo `docs/09-repo-structure.md`. Hien tai service da co `.venv`, dependencies da cai, test dang pass, `uvicorn` da smoke test thanh cong, va workflow da chuyen sang LangGraph that. Cac phan chua xong la DB that, LLM that, va backend Spring Boot that.

## Da hoan thanh

### Phase 0 - Chuan bi repo

- [x] Tao base repo structure theo `docs/09-repo-structure.md`
- [x] Tao `.venv`
- [x] Dong bo `requirements.txt`
- [x] Dong bo `.env.example`
- [x] Dong bo `.gitignore`
- [x] Tao `Dockerfile`
- [x] Tao `docker-compose.yml`
- [x] Tao `alembic.ini`

### Phase 1 - FastAPI base

- [x] Tao [app/main.py](D:/University/Doan3/kol-ai-assistant-service/app/main.py)
- [x] Tao health endpoint [app/api/routes/health.py](D:/University/Doan3/kol-ai-assistant-service/app/api/routes/health.py)
- [x] Chay thu `uvicorn app.main:app --reload --port 8001` bang smoke test health

### Phase 2 - Schemas

- [x] Tao [app/schemas/criteria.py](D:/University/Doan3/kol-ai-assistant-service/app/schemas/criteria.py)
- [x] Tao [app/schemas/chat.py](D:/University/Doan3/kol-ai-assistant-service/app/schemas/chat.py)
- [x] Tao [app/schemas/recommendation.py](D:/University/Doan3/kol-ai-assistant-service/app/schemas/recommendation.py)
- [x] Tao [app/schemas/kol.py](D:/University/Doan3/kol-ai-assistant-service/app/schemas/kol.py)

### Phase 3 - Database conversation memory

- [x] Scaffold [app/core/database.py](D:/University/Doan3/kol-ai-assistant-service/app/core/database.py)
- [x] Scaffold models [app/models/conversation.py](D:/University/Doan3/kol-ai-assistant-service/app/models/conversation.py) va [app/models/message.py](D:/University/Doan3/kol-ai-assistant-service/app/models/message.py)
- [x] Tao migration [migrations/versions/001_create_ai_tables.py](D:/University/Doan3/kol-ai-assistant-service/migrations/versions/001_create_ai_tables.py)
- [x] Tao repository interface tam thoi bang in-memory: [app/repositories/conversation_repository.py](D:/University/Doan3/kol-ai-assistant-service/app/repositories/conversation_repository.py)
- [x] Ket noi repository voi PostgreSQL that
- [x] Doi cau hinh DB sang dung chung database `kol_booking` cua backend, tao bang `ai_*` trong public schema
- [ ] Tao va ap dung migration that bang Alembic

### Phase 4 - LLM client

- [x] Scaffold abstraction [app/clients/llm_client.py](D:/University/Doan3/kol-ai-assistant-service/app/clients/llm_client.py)
- [x] Implement provider OpenAI co ban trong [app/clients/llm_client.py](D:/University/Doan3/kol-ai-assistant-service/app/clients/llm_client.py)
- [x] Co fallback ve rule-based neu khong co `OPENAI_API_KEY` hoac LLM loi
- [ ] Test end-to-end voi API key that
- [x] Them retry/json-repair ro rang khi LLM tra JSON loi

### Phase 5 - Intent + Criteria Extraction

- [x] Tao [app/services/intent_service.py](D:/University/Doan3/kol-ai-assistant-service/app/services/intent_service.py) ban mock rule-based
- [x] Tao [app/services/criteria_service.py](D:/University/Doan3/kol-ai-assistant-service/app/services/criteria_service.py) ban mock rule-based
- [x] Co merge criteria co ban
- [x] Co logic clarification co ban
- [x] Noi intent/criteria service voi LLM theo che do fallback
- [ ] Test va tinh chinh output extraction bang LLM that
- [ ] Bo sung normalize/fallback day du hon

### Phase 6 - KOL backend client

- [x] Tao [app/clients/kol_backend_client.py](D:/University/Doan3/kol-ai-assistant-service/app/clients/kol_backend_client.py)
- [x] Co mock candidates de phat trien tiep
- [ ] Tich hop that voi Spring Boot `/api/internal/kols/search-candidates`
- [x] Xu ly error response va auth internal token day du

### Phase 7 - Ranking Service

- [x] Tao [app/services/ranking_service.py](D:/University/Doan3/kol-ai-assistant-service/app/services/ranking_service.py)
- [x] Co score cho category, platform, follower, budget, engagement, rating, booking
- [x] Co `generate_reason`
- [x] Co test khung ranking
- [ ] Ra soat cong thuc diem voi `docs/07-ranking-logic.md` va tinh chinh chi tiet

### Phase 8 - Workflow

- [x] Tao state [app/graph/state.py](D:/University/Doan3/kol-ai-assistant-service/app/graph/state.py)
- [x] Tao nodes [app/graph/nodes.py](D:/University/Doan3/kol-ai-assistant-service/app/graph/nodes.py)
- [x] Tao file workflow [app/graph/kol_chat_graph.py](D:/University/Doan3/kol-ai-assistant-service/app/graph/kol_chat_graph.py)
- [x] Co mock flow end-to-end thay cho LangGraph that
- [x] Chuyen sang LangGraph that dung `StateGraph`
- [x] Them conditional edge clarify/recommend co ban
- [ ] Them retry, fallback, va error-path day du theo `docs/05-ai-workflow.md`

### Phase 9 - Chat endpoint integration

- [x] Tao [app/api/routes/chat.py](D:/University/Doan3/kol-ai-assistant-service/app/api/routes/chat.py)
- [x] Endpoint chat da goi workflow mock
- [x] Tao endpoint recommendations [app/api/routes/recommendations.py](D:/University/Doan3/kol-ai-assistant-service/app/api/routes/recommendations.py)
- [ ] Test thu bang Swagger hoac chay local that

### Phase 10 - Docker

- [x] Tao [Dockerfile](D:/University/Doan3/kol-ai-assistant-service/Dockerfile)
- [x] Tao [docker-compose.yml](D:/University/Doan3/kol-ai-assistant-service/docker-compose.yml)
- [ ] Chay thu docker compose

### Phase 11 - Tich hop voi Spring Boot

- [ ] Xac nhan contract API voi backend Spring Boot
- [ ] Tich hop internal token
- [ ] Test luong `Frontend -> Spring Boot -> AI Service`

### Phase 12 - Test checklist

- [x] Tao test khung:
- [x] [tests/test_health.py](D:/University/Doan3/kol-ai-assistant-service/tests/test_health.py)
- [x] [tests/test_criteria_service.py](D:/University/Doan3/kol-ai-assistant-service/tests/test_criteria_service.py)
- [x] [tests/test_ranking_service.py](D:/University/Doan3/kol-ai-assistant-service/tests/test_ranking_service.py)
- [x] [tests/test_chat_flow.py](D:/University/Doan3/kol-ai-assistant-service/tests/test_chat_flow.py)
- [x] Da kiem tra cu phap bang `python -m compileall app tests migrations`
- [x] Cai dependencies trong `.venv`: `python -m pip install -r requirements.txt`
- [x] Chay test that: `.\.venv\Scripts\python -m pytest -q`
- [x] Ket qua hien tai: `5 passed`
- [x] Mo rong test case cho DB, backend client, va LLM fallback

## Viec can lam ngay tiep theo

- [x] Chuyen repository conversation tu in-memory sang PostgreSQL
- [x] Test LLM voi `OPENAI_API_KEY` that va chot prompt/output format co ban
- [ ] Tich hop KOL backend client that voi Spring Boot
- [ ] Mo rong LangGraph cho retry/fallback/error handling
- [ ] Chay `docker compose up` va test luong local co PostgreSQL

## Ghi chu

- Scaffold hien tai uu tien tao khung de code tiep nhanh, chua phai ban production-ready.
- Moi truong dang dung Python `3.14.0`.
- `pytest` hien tai pass, nhung co 1 warning tu `starlette.testclient` ve `httpx` deprecation.
- Repo hien tai khong phai git repository, nen chua co lich su commit de doi chieu roadmap commit.
