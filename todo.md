# TODO - KOL AI Assistant Service

Cap nhat lan cuoi: 2026-06-12

## Trang thai hien tai

Service AI da duoc scaffold va da push len GitHub o commit `1e4283c`.
FastAPI, LangGraph workflow, OpenAI-compatible LLM client, ranking, repository PostgreSQL/fallback, Dockerfile, Docker Compose, Alembic va test suite da co san.

Database da duoc doi huong sang dung chung DB `kol_booking` cua backend va tao cac bang `ai_*` trong public schema, khong tao schema rieng. Migration chua apply duoc tren may hien tai vi `localhost:5432` tu choi password cho user `kol_user`.

## Da hoan thanh

### Phase 0 - Repo va tooling

- [x] Tao base repo structure theo `docs/09-repo-structure.md`
- [x] Tao `.venv`
- [x] Dong bo `requirements.txt`
- [x] Dong bo `.env.example`
- [x] Dong bo `.gitignore`
- [x] Tao `Dockerfile`
- [x] Tao `docker-compose.yml`
- [x] Tao `alembic.ini`
- [x] Commit va push len `origin/main`

### Phase 1 - FastAPI API

- [x] Tao app FastAPI trong `app/main.py`
- [x] Tao health endpoint `GET /api/v1/health`
- [x] Tao chat endpoint `POST /api/v1/chat`
- [x] Tao recommendation endpoint `POST /api/v1/recommendations`

### Phase 2 - Schemas

- [x] Tao `KolSearchCriteria`
- [x] Tao `ChatRequest` / `ChatResponse`
- [x] Tao `RecommendationRequest` / `RecommendationResponse`
- [x] Tao KOL candidate schema

### Phase 3 - Database conversation memory

- [x] Tao SQLAlchemy base/session trong `app/core/database.py`
- [x] Tao model `Conversation`
- [x] Tao model `Message`
- [x] Tao migration `001_create_ai_tables.py`
- [x] Tao repository PostgreSQL bang SQLAlchemy async
- [x] Giu fallback in-memory khi DB chua san sang
- [x] Doi config sang dung chung database backend `kol_booking`
- [x] Docker Compose AI service khong tao PostgreSQL rieng nua
- [ ] Apply migration that vao DB backend bang Alembic
- [ ] Xac nhan cac bang `ai_conversations`, `ai_messages`, `ai_recommendation_logs` nam trong public schema cua DB backend

### Phase 4 - LLM client

- [x] Implement OpenAI-compatible client
- [x] Ho tro `OPENAI_BASE_URL`
- [x] Ho tro retry cho timeout/network/rate limit
- [x] Ho tro parse JSON trong markdown/code fence
- [x] Ho tro JSON repair fallback
- [x] Test smoke voi API key that: provider tra `200 OK`

### Phase 5 - Intent va Criteria Extraction

- [x] Tao intent service voi LLM + rule-based fallback
- [x] Tao criteria service voi LLM + rule-based fallback
- [x] Normalize category/platform tu output LLM ve canonical value
- [x] Parse duoc tieng Viet co dau va khong dau cho case thoi trang/TikTok/follower/budget
- [x] Merge criteria qua nhieu luot chat
- [x] Co clarification logic co ban
- [x] Mo rong normalize cho day du 8 category canonical cua backend
- [x] Mo rong test extraction cho beauty, food, lifestyle, travel, fitness, tech, entertainment
- [x] Tinh chinh prompt de LLM luon tra canonical enum/category slug

### Phase 6 - KOL backend client

- [x] Tao `KolBackendClient`
- [x] Ho tro internal token qua `X-Internal-Token`
- [x] Ho tro retry va fallback mock candidates
- [x] Ho tro response dang raw `{ items: [...] }`
- [x] Ho tro response envelope `{ success, data }`
- [x] Normalize category/platform/gender tu backend response
- [x] Backend Spring Boot co endpoint `POST /api/internal/kols/search-candidates`
- [ ] Test client voi backend Spring Boot that
- [x] Chot auth internal token giua Spring Boot va AI service bang header `X-Internal-Token`

### Phase 7 - Ranking Service

- [x] Tao ranking service
- [x] Score theo category, platform, follower, budget, engagement, rating, completed booking
- [x] Generate reason cho recommendation
- [x] Co test ranking co ban
- [x] Ra soat cong thuc diem voi `docs/07-ranking-logic.md`
- [x] Them test cho edge cases: khong co platform, gia null, candidate vuot budget, follower gan nguong

### Phase 8 - LangGraph Workflow

- [x] Tao graph state
- [x] Tao nodes cho load/extract/merge/clarify/retrieve/rank/respond/save
- [x] Chuyen sang LangGraph `StateGraph`
- [x] Co conditional edge clarify/recommend
- [x] Them error-path ro rang cho backend unavailable, LLM invalid output, DB unavailable
- [x] Them logging/metadata de debug moi node trong workflow

### Phase 9 - Docker va local run

- [x] Dockerfile build duoc image Python service
- [x] Docker Compose chi chay AI service va tro DB ve PostgreSQL backend
- [ ] Chay `docker compose up --build`
- [ ] Test `GET /api/v1/health` trong container
- [ ] Test `POST /api/v1/chat` trong container

### Phase 10 - End-to-end integration

- [ ] Backend Spring Boot goi AI service `/api/v1/chat`
- [ ] AI service goi backend internal search candidate API
- [ ] Frontend chat luu/lay `conversationId`
- [ ] Test luong `Frontend -> Spring Boot -> AI Service -> Spring Boot KOL data -> AI ranking`

## Viec can lam ngay tiep theo

1. Xac dinh DATABASE_URL that cua backend dang chay.

   Neu dung Docker compose backend local:

   ```env
   DATABASE_URL=postgresql+asyncpg://kol_user:kol_secret@localhost:5432/kol_booking
   ```

   Neu dung Supabase/remote DB theo `.env.example` cua backend:

   ```env
   DATABASE_URL=postgresql+asyncpg://postgres.ouotjxgpszmqemfgoits:<password>@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres
   ```

2. Apply migration AI vao dung DB backend.

   ```powershell
   .\.venv\Scripts\python -m alembic upgrade head
   ```

3. Xac nhan bang AI da duoc tao.

   ```sql
   SELECT table_name
   FROM information_schema.tables
   WHERE table_schema = 'public'
     AND table_name LIKE 'ai_%';
   ```

4. Dong bo token noi bo giua 2 service.

   Backend Docker can co:

   ```env
   APP_INTERNAL_TOKEN=<same-secret>
   ```

   AI service can co:

   ```env
   SPRING_BACKEND_INTERNAL_TOKEN=<same-secret>
   SPRING_BACKEND_BASE_URL=http://localhost:8080
   ```

5. Test AI service voi DB shared va backend internal API that.

   ```powershell
   .\.venv\Scripts\python -m pytest -q
   uvicorn app.main:app --reload --port 8001
   ```

6. Chay Docker AI service sau khi DB backend local da dung credential.

   ```powershell
   docker compose up --build
   ```

## Da xong trong phien nay

- Mo rong `normalize_category` thanh 8 slug canonical: `fashion`, `beauty`, `food`, `lifestyle`, `travel`, `fitness`, `tech`, `entertainment`
- Tinh chinh `criteria_prompt` de ep LLM tra ve dung canonical slug/category enum
- Bo sung log fallback ro rang cho LLM, backend client va repository fallback khi DB khong san sang
- Them `workflowTrace` va `warnings` vao metadata cua moi luot chat de debug workflow
- Cap nhat ranking cho category lien quan va bo sung test edge cases theo `docs/07-ranking-logic.md`
- Them `docker-compose.local.yml`, `.env.local.example` va `scripts/verify_local_db.py` de test bang `ai_*` o local truoc khi dung DB remote
- Chay lai test suite: `25 passed, 1 warning`
- Bo sung endpoint Spring Boot `POST /api/internal/kols/search-candidates`
- Bo sung `APP_INTERNAL_TOKEN` cho backend Docker Compose va `.env.example`
- Test backend Docker endpoint:
  - `GET /actuator/health` tra `UP`
  - Khong co `X-Internal-Token` tra `403 FORBIDDEN`
  - Token dung tra response raw `{ "items": [...] }`
  - Platform sai tra `400 VALIDATION_FAILED`

## Blocker hien tai

- `alembic current` dang fail voi loi `password authentication failed for user "kol_user"` khi tro toi `localhost:5432/kol_booking`.
- Docker API trong phien nay co luc khong truy cap duoc `npipe:////./pipe/dockerDesktopLinuxEngine`, can dam bao Docker Desktop dang chay truoc khi test container.
- Can set cung mot secret cho `APP_INTERNAL_TOKEN` cua backend va `SPRING_BACKEND_INTERNAL_TOKEN` cua AI service truoc khi test end-to-end.

## Lenh verify da chay gan nhat

```powershell
.\.venv\Scripts\python -m compileall app migrations tests
.\.venv\Scripts\python -m pytest -q
```

Ket qua moi nhat: `25 passed, 1 warning`.
