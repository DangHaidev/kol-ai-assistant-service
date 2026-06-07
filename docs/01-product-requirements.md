# 01 - Product Requirements: AI KOL Recommendation Chatbot

## 1. Tên feature

**AI KOL Recommendation Assistant**

## 2. Mục tiêu nghiệp vụ

Giúp Brand tìm KOL phù hợp bằng cách nhập yêu cầu tự nhiên thay vì phải tự lọc thủ công nhiều tiêu chí.

Ví dụ:

```txt
Tôi muốn tìm KOL về thời trang, follower trên 100k, ngân sách dưới 10 triệu, ưu tiên TikTok.
```

Hệ thống trả về:

- Danh sách KOL phù hợp.
- Điểm phù hợp `matchScore`.
- Lý do đề xuất.
- Các tiêu chí AI đã hiểu được.
- Câu hỏi làm rõ nếu thiếu thông tin.

## 3. Người dùng chính

### Brand

Brand dùng chatbot để:

- Tìm KOL cho chiến dịch marketing.
- Nói yêu cầu bằng ngôn ngữ tự nhiên.
- Nhận danh sách KOL phù hợp.
- Click vào KOL để xem chi tiết.
- Gửi booking request sau khi chọn KOL.

### Admin

Admin có thể dùng log hội thoại để:

- Theo dõi nhu cầu tìm kiếm của Brand.
- Kiểm tra chất lượng gợi ý.
- Tối ưu hệ thống matching.

## 4. Use case chính

### UC-01: Brand tìm KOL bằng chatbot

**Actor:** Brand

**Pre-condition:** Brand đã đăng nhập.

**Main flow:**

1. Brand mở màn hình AI Assistant.
2. Brand nhập yêu cầu tìm KOL.
3. AI Service phân tích intent và criteria.
4. AI Service lưu message vào conversation.
5. AI Service gọi backend chính để lấy danh sách KOL.
6. AI Service chấm điểm và sắp xếp KOL.
7. AI Service trả về câu trả lời và danh sách recommendation.
8. Frontend hiển thị kết quả.

**Post-condition:** Brand có danh sách KOL đề xuất.

### UC-02: Chatbot hỏi thêm thông tin khi thiếu criteria

Ví dụ người dùng nhập:

```txt
Tôi muốn tìm KOL quảng bá sản phẩm mới.
```

Thông tin thiếu:

- Ngành hàng.
- Nền tảng.
- Ngân sách.
- Follower mong muốn.

Bot có thể hỏi:

```txt
Bạn muốn tìm KOL cho ngành hàng nào? Ví dụ: thời trang, mỹ phẩm, ăn uống, công nghệ hoặc du lịch.
```

### UC-03: Chatbot nhớ ngữ cảnh nhiều lượt

Ví dụ:

```txt
User: Tôi cần KOL thời trang follower trên 100k.
Bot: Bạn muốn ưu tiên nền tảng nào?
User: TikTok, ngân sách dưới 10 triệu.
```

Kết quả criteria cuối cùng:

```json
{
  "category": "fashion",
  "minFollowers": 100000,
  "platforms": ["tiktok"],
  "maxBudget": 10000000
}
```

## 5. Functional Requirements

### FR-01: Chat API

Hệ thống phải cung cấp API để nhận message từ người dùng và trả về phản hồi chatbot.

Endpoint:

```http
POST /api/v1/chat
```

### FR-02: Conversation Memory

Hệ thống phải lưu:

- Conversation ID.
- Brand ID.
- Message của user.
- Message của assistant.
- Current criteria.
- Metadata của mỗi lượt chat.

### FR-03: Intent Extraction

Hệ thống phải phân loại ý định người dùng:

```txt
recommend_kol
compare_kol
explain_kol
booking_help
general_question
```

MVP chỉ cần xử lý tốt `recommend_kol`.

### FR-04: Criteria Extraction

Hệ thống phải trích xuất được:

```txt
category
platforms
minFollowers
maxFollowers
minBudget
maxBudget
location
gender
campaignGoal
serviceType
```

### FR-05: Criteria Merging

Hệ thống phải merge criteria mới với criteria cũ trong conversation.

Ví dụ:

Criteria cũ:

```json
{
  "category": "fashion",
  "minFollowers": 100000
}
```

Message mới:

```txt
TikTok, ngân sách dưới 10 triệu
```

Criteria mới sau merge:

```json
{
  "category": "fashion",
  "minFollowers": 100000,
  "platforms": ["tiktok"],
  "maxBudget": 10000000
}
```

### FR-06: KOL Retrieval

Hệ thống phải lấy danh sách KOL thật từ backend chính hoặc database.

Khuyến nghị MVP:

```txt
AI Service → Spring Boot API → PostgreSQL
```

### FR-07: Ranking

Hệ thống phải tính `matchScore` cho từng KOL.

Điểm phải dựa trên:

- Category match.
- Platform match.
- Follower match.
- Budget match.
- Engagement rate.
- Rating.
- Booking performance.

### FR-08: Explainable Recommendation

Mỗi KOL đề xuất nên có `reason`.

Ví dụ:

```txt
Phù hợp vì thuộc lĩnh vực thời trang, có 230k follower trên TikTok, giá nằm trong ngân sách và rating cao.
```

## 6. Non-Functional Requirements

### NFR-01: Security

- AI Service không tự xác thực user cuối nếu Spring Boot đã làm gateway.
- Spring Boot nên truyền `brandId` đã xác thực sang AI Service.
- Không để LLM chạy SQL trực tiếp.
- Không gửi dữ liệu nhạy cảm không cần thiết vào prompt.

### NFR-02: Performance

MVP nên đáp ứng:

```txt
Chat response: 3-8 giây tùy LLM
KOL retrieval: < 1 giây
Ranking: < 500ms cho vài trăm KOL
```

### NFR-03: Reliability

Nếu LLM lỗi:

- Trả về message thân thiện.
- Không crash service.
- Có thể fallback sang rule-based extraction đơn giản.

### NFR-04: Maintainability

Code phải tách rõ:

```txt
controller
service
client
repository
schema
prompt
graph
```

## 7. MVP Scope

Nên làm trước:

- Chat API.
- Lưu hội thoại.
- Extract criteria.
- Merge criteria theo conversation.
- Gọi backend lấy KOL.
- Rank KOL.
- Trả về top 5.

Chưa cần làm ngay:

- Vector search.
- Multi-agent phức tạp.
- Fine-tuning model riêng.
- Payment/booking bằng AI.
- Tự động gửi booking.
