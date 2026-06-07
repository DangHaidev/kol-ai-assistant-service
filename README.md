# KOL AI Assistant Service

## 1. Mục tiêu

`kol-ai-assistant-service` là một service AI chạy riêng repo, dùng để hỗ trợ Brand tìm KOL bằng hội thoại tự nhiên.

Ví dụ người dùng nhập:

```txt
Tôi muốn kiếm KOL về thời trang, lượt follower trên 100k, ưu tiên TikTok, ngân sách dưới 10 triệu.
```

Service cần hiểu yêu cầu, lưu ngữ cảnh hội thoại, trích xuất tiêu chí tìm kiếm, gọi dữ liệu KOL thật từ backend chính, chấm điểm phù hợp và trả về danh sách KOL nên chọn.

## 2. Vai trò trong hệ thống

Backend chính hiện tại là hệ thống KOL Booking dùng Java 21, Spring Boot, PostgreSQL, JWT, Docker và Flyway. Service AI này không thay thế backend chính, mà đóng vai trò lớp thông minh phía trên chức năng Search & Discovery.

```txt
Frontend Chatbot
    ↓
Spring Boot Backend
    ↓ REST API
KOL AI Assistant Service
    ↓
LLM + Conversation Memory + Recommendation Logic
    ↓
Spring Boot KOL APIs / PostgreSQL
```

## 3. Stack đề xuất

| Thành phần | Công nghệ |
|---|---|
| Language | Python 3.11+ hoặc Python 3.12 |
| API Framework | FastAPI |
| AI Workflow | LangGraph |
| LLM Client | OpenAI / Gemini / Groq / Ollama tùy cấu hình |
| Validation | Pydantic |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migration | Alembic |
| HTTP Client | httpx |
| Optional Cache | Redis |
| Optional Vector Search | pgvector |
| Deploy | Docker, Docker Compose |

## 4. Nguyên tắc thiết kế quan trọng

### 4.1. AI không được tự quyết định dữ liệu

LLM chỉ được dùng để:

- Hiểu câu hỏi người dùng.
- Trích xuất tiêu chí tìm kiếm.
- Tạo câu trả lời tự nhiên.
- Đề xuất câu hỏi làm rõ nếu thiếu thông tin.

LLM không được:

- Tự bịa tên KOL.
- Tự bịa follower, giá, rating.
- Tự tạo SQL rồi chạy trực tiếp.
- Tự quyết định booking/payment.

### 4.2. Dữ liệu KOL phải lấy từ hệ thống thật

Luồng đúng:

```txt
User message
→ LLM extract criteria
→ Backend query KOL thật
→ Ranking bằng code
→ LLM viết response dựa trên kết quả thật
```

### 4.3. Có ngữ cảnh hội thoại

Chatbot cần nhớ các điều kiện đã nhập ở lượt trước.

Ví dụ:

```txt
User: Tôi muốn tìm KOL thời trang follower trên 100k.
Bot: Bạn muốn ưu tiên nền tảng nào?
User: TikTok, ngân sách dưới 10 triệu.
```

Sau lượt 2, criteria đầy đủ phải là:

```json
{
  "category": "fashion",
  "minFollowers": 100000,
  "platforms": ["tiktok"],
  "maxBudget": 10000000
}
```

## 5. MVP cần hoàn thành

MVP nên gồm 5 phần:

1. API `/api/v1/chat` nhận message từ người dùng.
2. Lưu conversation và messages vào PostgreSQL.
3. Extract criteria từ message bằng LLM.
4. Gọi backend chính để lấy danh sách KOL phù hợp.
5. Rank KOL và trả về top kết quả kèm lý do.

## 6. Lệnh chạy dự kiến

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Trên Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

## 7. Tài liệu trong thư mục này

| File | Nội dung |
|---|---|
| `01-product-requirements.md` | Mô tả chức năng và phạm vi MVP |
| `02-architecture.md` | Kiến trúc tổng thể và module nội bộ |
| `03-api-contract.md` | API request/response giữa Frontend, Spring Boot và AI Service |
| `04-database-design.md` | Thiết kế DB cho conversation memory |
| `05-ai-workflow.md` | Workflow LangGraph và state chatbot |
| `06-prompts.md` | Prompt dùng cho intent extraction, criteria extraction, response generation |
| `07-ranking-logic.md` | Công thức chấm điểm KOL |
| `08-implementation-roadmap.md` | Checklist code theo từng bước |
| `09-repo-structure.md` | Cấu trúc thư mục repo đề xuất |
