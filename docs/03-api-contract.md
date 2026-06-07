# 03 - API Contract

## 1. Chat API

### Endpoint

```http
POST /api/v1/chat
```

### Mục đích

Nhận message từ người dùng, xử lý hội thoại có ngữ cảnh và trả về phản hồi chatbot.

### Request

```json
{
  "brandId": 1,
  "conversationId": "1b19cb80-5d56-4f1e-a993-b11b9c42b002",
  "message": "Tôi muốn tìm KOL thời trang follower trên 100k"
}
```

### Field description

| Field | Type | Required | Description |
|---|---|---|---|
| brandId | number | true | ID của Brand đã xác thực ở backend chính |
| conversationId | string/null | false | Null nếu tạo conversation mới |
| message | string | true | Nội dung người dùng nhập |

### Response khi cần hỏi thêm

```json
{
  "conversationId": "1b19cb80-5d56-4f1e-a993-b11b9c42b002",
  "reply": "Bạn muốn ưu tiên nền tảng nào: TikTok, Instagram, Facebook hay YouTube?",
  "intent": "recommend_kol",
  "criteria": {
    "category": "fashion",
    "platforms": [],
    "minFollowers": 100000,
    "maxFollowers": null,
    "minBudget": null,
    "maxBudget": null,
    "location": null,
    "gender": null,
    "campaignGoal": null,
    "serviceType": null
  },
  "recommendations": [],
  "needClarification": true,
  "clarificationQuestions": [
    "Bạn muốn ưu tiên nền tảng nào?",
    "Bạn có ngân sách dự kiến không?"
  ]
}
```

### Response khi có recommendation

```json
{
  "conversationId": "1b19cb80-5d56-4f1e-a993-b11b9c42b002",
  "reply": "Tôi tìm thấy 3 KOL phù hợp với ngành thời trang, follower trên 100k, ưu tiên TikTok và ngân sách dưới 10 triệu.",
  "intent": "recommend_kol",
  "criteria": {
    "category": "fashion",
    "platforms": ["tiktok"],
    "minFollowers": 100000,
    "maxFollowers": null,
    "minBudget": null,
    "maxBudget": 10000000,
    "location": null,
    "gender": null,
    "campaignGoal": null,
    "serviceType": null
  },
  "recommendations": [
    {
      "kolId": 12,
      "displayName": "Nguyễn A",
      "avatarUrl": "https://example.com/avatar.jpg",
      "categories": ["fashion", "beauty"],
      "platforms": [
        {
          "platform": "tiktok",
          "followers": 230000,
          "engagementRate": 0.047
        }
      ],
      "priceFrom": 8000000,
      "rating": 4.8,
      "completedBookingCount": 21,
      "matchScore": 92,
      "reason": "Phù hợp vì thuộc lĩnh vực thời trang, có 230k follower trên TikTok, giá nằm trong ngân sách và rating cao."
    }
  ],
  "needClarification": false,
  "clarificationQuestions": []
}
```

## 2. Recommendation API nội bộ

Endpoint này dùng khi frontend hoặc backend đã có criteria rõ ràng và chỉ muốn lấy recommendation.

### Endpoint

```http
POST /api/v1/recommendations
```

### Request

```json
{
  "brandId": 1,
  "criteria": {
    "category": "fashion",
    "platforms": ["tiktok"],
    "minFollowers": 100000,
    "maxBudget": 10000000
  },
  "topK": 5
}
```

### Response

```json
{
  "criteria": {
    "category": "fashion",
    "platforms": ["tiktok"],
    "minFollowers": 100000,
    "maxBudget": 10000000
  },
  "recommendations": [
    {
      "kolId": 12,
      "displayName": "Nguyễn A",
      "matchScore": 92,
      "reason": "Phù hợp với yêu cầu."
    }
  ]
}
```

## 3. Health Check API

```http
GET /api/v1/health
```

Response:

```json
{
  "status": "ok",
  "service": "kol-ai-assistant-service"
}
```

## 4. API Spring Boot cần cung cấp cho AI Service

AI Service cần lấy KOL candidates từ backend chính.

### Endpoint đề xuất

```http
POST /api/internal/kols/search-candidates
```

### Request từ AI Service sang Spring Boot

```json
{
  "category": "fashion",
  "platforms": ["tiktok"],
  "minFollowers": 100000,
  "maxFollowers": null,
  "minBudget": null,
  "maxBudget": 10000000,
  "location": null,
  "gender": null,
  "serviceType": null,
  "limit": 50
}
```

### Response từ Spring Boot

```json
{
  "items": [
    {
      "kolId": 12,
      "displayName": "Nguyễn A",
      "avatarUrl": "https://example.com/avatar.jpg",
      "bio": "Fashion creator focused on Gen Z style.",
      "location": "Hồ Chí Minh",
      "gender": "female",
      "categories": ["fashion", "beauty"],
      "platforms": [
        {
          "platform": "tiktok",
          "profileUrl": "https://tiktok.com/@example",
          "followers": 230000,
          "engagementRate": 0.047,
          "averageViews": 50000
        }
      ],
      "priceFrom": 8000000,
      "averageRating": 4.8,
      "completedBookingCount": 21,
      "bookingAcceptanceRate": 0.86
    }
  ]
}
```

## 5. Error Response chuẩn

```json
{
  "error": {
    "code": "LLM_TIMEOUT",
    "message": "LLM provider timeout",
    "details": null
  }
}
```

Một số error code:

```txt
INVALID_REQUEST
CONVERSATION_NOT_FOUND
LLM_TIMEOUT
LLM_INVALID_OUTPUT
BACKEND_UNAVAILABLE
RECOMMENDATION_FAILED
```
