# 02 - Architecture Design

## 1. Kiến trúc tổng thể

Service AI nên được tách repo riêng và giao tiếp với backend chính thông qua REST API.

```txt
+-------------------+
| Frontend          |
| Chatbot UI        |
+---------+---------+
          |
          v
+-------------------+
| Spring Boot API   |
| Auth, Brand, KOL  |
| Booking, Payment  |
+---------+---------+
          |
          v
+---------------------------+
| KOL AI Assistant Service  |
| FastAPI + LangGraph       |
+---------+-----------------+
          |
          +----------------------+
          |                      |
          v                      v
+-------------------+    +-------------------+
| LLM Provider      |    | PostgreSQL         |
| OpenAI/Gemini/... |    | AI conversations   |
+-------------------+    +-------------------+
```

## 2. Trách nhiệm từng hệ thống

### Spring Boot Backend

Giữ các nghiệp vụ chính:

- Authentication.
- Authorization.
- Brand profile.
- KOL profile.
- Search KOL cơ bản.
- Booking.
- Payment.
- Review.
- Notification.

### AI Service

Chỉ xử lý phần AI:

- Nhận message từ backend.
- Phân tích intent.
- Extract criteria.
- Lưu conversation memory.
- Gọi backend lấy KOL.
- Chấm điểm recommendation.
- Sinh response tự nhiên.

## 3. Vì sao nên tách service?

Ưu điểm:

- Không làm phình backend Spring Boot chính.
- Dễ thử nhiều LLM provider.
- Dễ phát triển recommendation, embedding, vector search.
- Python phù hợp AI hơn.
- Dễ deploy độc lập.

Nhược điểm:

- Cần quản lý thêm service.
- Cần xử lý network error giữa Spring Boot và AI Service.
- Cần đồng bộ contract API.

## 4. Luồng request chính

```txt
1. Brand gửi message từ frontend.
2. Frontend gọi Spring Boot API.
3. Spring Boot xác thực JWT.
4. Spring Boot lấy brandId từ token.
5. Spring Boot gọi AI Service /api/v1/chat.
6. AI Service lưu user message.
7. AI Service load conversation state.
8. AI Service dùng LLM extract intent + criteria.
9. AI Service merge criteria cũ và mới.
10. Nếu thiếu dữ kiện quan trọng, bot hỏi thêm.
11. Nếu đủ dữ kiện, AI Service gọi Spring Boot KOL Search API.
12. AI Service rank KOL.
13. AI Service sinh response.
14. AI Service lưu assistant message.
15. Spring Boot trả response về frontend.
```

## 5. Nội bộ AI Service

```txt
app/
├── api/
│   └── routes/chat.py
├── schemas/
│   ├── chat.py
│   ├── criteria.py
│   └── recommendation.py
├── services/
│   ├── conversation_service.py
│   ├── intent_service.py
│   ├── criteria_service.py
│   ├── kol_retrieval_service.py
│   ├── ranking_service.py
│   └── response_service.py
├── graph/
│   ├── state.py
│   ├── nodes.py
│   └── kol_chat_graph.py
├── clients/
│   ├── llm_client.py
│   └── kol_backend_client.py
├── repositories/
│   └── conversation_repository.py
└── prompts/
    ├── intent_prompt.py
    ├── criteria_prompt.py
    └── response_prompt.py
```

## 6. Module Responsibilities

### `chat.py`

Nhận request từ Spring Boot hoặc frontend nội bộ.

### `conversation_service.py`

- Tạo conversation.
- Lưu message.
- Lấy lịch sử hội thoại.
- Lưu current criteria.

### `intent_service.py`

Dùng LLM để xác định user đang muốn:

```txt
recommend_kol
compare_kol
booking_help
general_question
```

### `criteria_service.py`

- Extract tiêu chí tìm kiếm.
- Normalize dữ liệu.
- Merge criteria.
- Kiểm tra còn thiếu tiêu chí quan trọng không.

### `kol_retrieval_service.py`

Gọi backend chính để lấy KOL candidates.

### `ranking_service.py`

Tính điểm phù hợp cho từng KOL.

### `response_service.py`

Sinh câu trả lời cuối cùng dựa trên kết quả thật.

## 7. Quy tắc giao tiếp với backend chính

AI Service không nên truy cập bảng booking/payment/user nhạy cảm.

Khuyến nghị gọi backend qua API:

```txt
GET /api/kols/search
POST /api/kols/recommendation-candidates
GET /api/kols/{id}
```

Spring Boot nên kiểm soát quyền truy cập và dữ liệu trả về.

## 8. Error Handling

### LLM timeout

Trả về:

```json
{
  "reply": "Hiện tại trợ lý AI đang phản hồi chậm. Bạn có thể thử lại sau hoặc dùng bộ lọc tìm kiếm thông thường.",
  "recommendations": []
}
```

### Backend chính lỗi

Trả về:

```json
{
  "reply": "Tôi đã hiểu yêu cầu của bạn nhưng chưa lấy được danh sách KOL từ hệ thống. Vui lòng thử lại.",
  "criteria": {...},
  "recommendations": []
}
```

### LLM output sai JSON

- Retry 1 lần.
- Nếu vẫn sai, fallback rule-based extraction.

## 9. Deploy Development

```txt
Spring Boot Backend: localhost:8080
AI Service: localhost:8001
PostgreSQL: localhost:5432
```

Docker Compose có thể gồm:

```txt
ai-service
postgres-ai
redis optional
```

Nếu dùng chung PostgreSQL với backend chính, nên tạo schema riêng:

```sql
CREATE SCHEMA ai_assistant;
```
