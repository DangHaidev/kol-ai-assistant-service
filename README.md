# KOL AI Assistant Service

## 1. Mục tiêu

`kol-ai-assistant-service` là một AI service riêng, dùng để hỗ trợ Brand tìm KOL bằng hội thoại tự nhiên.

Ví dụ:

```txt
Tôi muốn tìm KOL về thời trang, follower trên 100k, ưu tiên TikTok, ngân sách dưới 10 triệu.
```

Service cần:
- hiểu yêu cầu của người dùng
- lưu ngữ cảnh hội thoại
- trích xuất tiêu chí tìm kiếm
- gọi dữ liệu KOL thật từ backend chính
- xếp hạng và trả về danh sách KOL đề xuất

## 2. Vai trò trong hệ thống

Backend chính hiện tại là hệ thống KOL Booking dùng Java 21, Spring Boot, PostgreSQL, JWT, Docker và Flyway. AI service này không thay thế backend chính, mà đóng vai trò lớp thông minh phía trên Search & Discovery.

```txt
Frontend Chatbot
    ->
Spring Boot Backend
    -> REST API
KOL AI Assistant Service
    ->
LLM + Conversation Memory + Recommendation Logic
    ->
Spring Boot KOL APIs / PostgreSQL
```

## 3. Stack

| Thành phần | Công nghệ |
|---|---|
| Language | Python 3.11+ / 3.12 |
| API Framework | FastAPI |
| AI Workflow | LangGraph |
| LLM Client | OpenAI-compatible / Gemini / Groq / Ollama |
| Validation | Pydantic |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migration | Alembic |
| HTTP Client | httpx |
| Deploy | Docker, Docker Compose |

## 4. Nguyên tắc thiết kế

### 4.1. AI không được tự quyết định dữ liệu

LLM chỉ được dùng để:
- hiểu câu hỏi của người dùng
- trích xuất tiêu chí tìm kiếm
- tạo câu trả lời tự nhiên
- đề xuất câu hỏi làm rõ nếu thiếu thông tin

LLM không được:
- tự bịa tên KOL
- tự bịa follower, giá, rating
- tự tạo SQL rồi chạy trực tiếp
- tự quyết định booking hoặc payment

### 4.2. Dữ liệu KOL phải lấy từ hệ thống thật

```txt
User message
-> LLM extract criteria
-> Backend query KOL thật
-> Ranking bằng code
-> LLM viết response dựa trên kết quả thật
```

### 4.3. Có ngữ cảnh hội thoại

Chatbot cần nhớ các điều kiện đã nhập ở lượt trước.

Ví dụ:

```txt
User: Tôi muốn tìm KOL thời trang follower trên 100k.
Bot: Bạn muốn ưu tiên nền tảng nào?
User: TikTok, ngân sách dưới 10 triệu.
```

Criteria đầy đủ sau lượt 2:

```json
{
  "category": "fashion",
  "minFollowers": 100000,
  "platforms": ["tiktok"],
  "maxBudget": 10000000
}
```

## 5. MVP

MVP gồm 5 phần:
1. API `/api/v1/chat`
2. Lưu conversation và messages vào PostgreSQL
3. Extract criteria từ message bằng LLM
4. Gọi backend chính để lấy danh sách KOL
5. Rank KOL và trả về top kết quả kèm lý do

## 6. Chạy service

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Chọn LLM provider

Mặc định service dùng OpenAI-compatible API. Để chạy với Gemini 3.1 Flash-Lite, cấu hình `.env` như sau:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_TIMEOUT_SECONDS=15
```

Gemini gọi native Generative Language API và trả JSON có cấu trúc cho luồng phân loại intent/trích xuất tiêu chí.

### Làm mới dữ liệu KOL mock

Script dưới đây tải KOL public từ backend, lấy detail của từng KOL và ghi vào `mock_data/backend_search_candidates.json`:

```powershell
.\.venv\Scripts\python scripts\refresh_mock_candidates.py
```

Script dùng `sort=follower_desc` vì endpoint public có thể trả ID trùng khi dùng thứ tự `featured` mặc định.

Trên Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

## 6.1. Test DB local trước khi dùng remote

Nếu muốn xác nhận migration và các bảng `ai_*` ổn định ở local trước, dùng flow này:

1. Tạo env local:

```powershell
Copy-Item .env.local.example .env.local
```

2. Khởi động PostgreSQL local:

```powershell
docker compose -f docker-compose.local.yml up -d postgres
```

3. Apply Alembic và kiểm tra bảng:

```powershell
$env:DATABASE_URL = "postgresql+asyncpg://kol_user:kol_secret@localhost:5433/kol_booking"
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python scripts\verify_local_db.py
```

Kết quả mong đợi:
- `ALEMBIC_VERSION=001`
- có đủ `ai_conversations`, `ai_messages`, `ai_recommendation_logs`

4. Nếu muốn chạy cả AI service với DB local:

```powershell
docker compose -f docker-compose.local.yml up --build
```

Hoặc chạy từ host:

```powershell
Copy-Item .env.local .env
uvicorn app.main:app --reload --port 8001
```

## 7. Tài liệu trong repo

| File | Nội dung |
|---|---|
| `docs/01-product-requirements.md` | Mô tả chức năng và phạm vi MVP |
| `docs/02-architecture.md` | Kiến trúc tổng thể và module nội bộ |
| `docs/03-api-contract.md` | API request/response giữa Frontend, Spring Boot và AI Service |
| `docs/04-database-design.md` | Thiết kế DB cho conversation memory |
| `docs/05-ai-workflow.md` | Workflow LangGraph và state chatbot |
| `docs/06-prompts.md` | Prompt cho intent extraction, criteria extraction, response generation |
| `docs/07-ranking-logic.md` | Công thức chấm điểm KOL |
| `docs/08-implementation-roadmap.md` | Checklist code theo từng bước |
| `docs/09-repo-structure.md` | Cấu trúc thư mục repo đề xuất |
