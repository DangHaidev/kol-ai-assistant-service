# 10 - Frontend UI Guidance for KOL AI Assistant

## 1. Mục tiêu giao diện

Frontend cần xây dựng một trải nghiệm chat giúp Brand tìm KOL bằng ngôn ngữ tự nhiên. Giao diện không nên giống landing page hay trang giới thiệu tính năng. Màn hình đầu tiên phải là công cụ làm việc thật: người dùng vào là có thể nhập yêu cầu, xem tiêu chí AI đã hiểu, xem danh sách KOL được đề xuất và tiếp tục tinh chỉnh cuộc hội thoại.

Mục tiêu chính:

- Giúp Brand mô tả nhu cầu tìm KOL nhanh chóng.
- Hiển thị rõ AI đã hiểu những tiêu chí nào.
- Cho phép người dùng bổ sung hoặc sửa tiêu chí qua hội thoại.
- Trình bày kết quả KOL theo cách dễ so sánh.
- Giữ được `conversationId` để cuộc trò chuyện có ngữ cảnh qua nhiều lượt.

## 2. Đối tượng người dùng

Người dùng chính là Brand hoặc nhân sự marketing đang cần tìm KOL cho chiến dịch. Họ quan tâm đến tốc độ ra quyết định, độ phù hợp của KOL và thông tin có thể so sánh được.

Giao diện nên có cảm giác:

- Gọn, rõ ràng, thực dụng.
- Ưu tiên dữ liệu và thao tác hơn trang trí.
- Dễ scan trên desktop.
- Vẫn dùng tốt trên mobile, nhưng desktop là trải nghiệm chính.

Không nên:

- Làm hero section lớn.
- Dùng quá nhiều card trang trí.
- Dùng gradient nền phức tạp.
- Che mất nội dung chính bằng animation hoặc intro.
- Biến chatbot thành giao diện quá “marketing”.

## 3. Bố cục đề xuất

Màn hình chính nên chia thành 3 vùng:

```txt
┌────────────────────────────────────────────────────────────┐
│ Header: tên module, trạng thái AI service, brand context    │
├───────────────────┬────────────────────────────────────────┤
│ Chat panel        │ Results / Recommendation panel          │
│                   │                                        │
│ - Messages        │ - Criteria summary                     │
│ - Clarification   │ - KOL result list                      │
│ - Input box       │ - Sort/filter controls                 │
│                   │ - Selected KOL detail                  │
└───────────────────┴────────────────────────────────────────┘
```

Tỷ lệ desktop hợp lý:

- Chat panel: khoảng 35-40% chiều rộng.
- Result panel: khoảng 60-65% chiều rộng.

Trên mobile:

- Dùng tab hoặc segmented control: `Chat` và `Kết quả`.
- Sau khi có recommendations, tự chuyển hoặc highlight tab `Kết quả`, nhưng vẫn cho quay lại chat dễ dàng.

## 4. Header

Header nên nhỏ gọn, không chiếm nhiều chiều cao.

Nên có:

- Tên màn hình: `AI KOL Assistant` hoặc `Tìm KOL bằng AI`.
- Trạng thái kết nối: `Sẵn sàng`, `Đang xử lý`, `Lỗi backend`, `Dùng dữ liệu mẫu`.
- Nút tạo cuộc trò chuyện mới.
- Nếu đã có Brand login, hiển thị tên Brand hoặc campaign hiện tại.

Không nên dùng header dạng marketing hero.

## 5. Chat panel

Chat panel là nơi người dùng nhập yêu cầu và tương tác với AI.

### Thành phần cần có

- Danh sách message theo thứ tự thời gian.
- Message của user căn phải hoặc có style riêng.
- Message của assistant căn trái hoặc có style riêng.
- Khu vực câu hỏi làm rõ khi `needClarification = true`.
- Input box nhiều dòng.
- Nút gửi có icon.
- Trạng thái loading khi đang chờ API.

### Input

Placeholder nên là ví dụ thực tế:

```txt
Ví dụ: Tôi cần KOL thời trang trên TikTok, trên 100k follower, ngân sách dưới 10 triệu
```

Nên hỗ trợ:

- Enter để gửi.
- Shift + Enter để xuống dòng.
- Disable nút gửi khi input rỗng hoặc request đang chạy.

### Clarification

Khi API trả:

```json
{
  "needClarification": true,
  "clarificationQuestions": [...]
}
```

Frontend nên hiển thị câu hỏi làm rõ dưới dạng các dòng rõ ràng, kèm quick replies nếu có thể.

Ví dụ:

- “Bạn muốn ưu tiên nền tảng nào?”
- Quick replies: `TikTok`, `Instagram`, `YouTube`, `Facebook`

Quick replies chỉ là tiện ích; người dùng vẫn phải nhập tự do được.

## 6. Criteria summary

Frontend nên hiển thị một khu vực tóm tắt tiêu chí AI đã hiểu. Đây là phần rất quan trọng để người dùng tin tưởng kết quả.

Ví dụ:

```txt
Tiêu chí hiện tại
- Ngành hàng: Thời trang
- Nền tảng: TikTok
- Follower tối thiểu: 100.000
- Ngân sách tối đa: 10.000.000đ
- Khu vực: Chưa xác định
- Giới tính: Không yêu cầu
```

Nên dùng chip hoặc compact rows cho từng tiêu chí.

Trạng thái field:

- Có giá trị: hiển thị rõ.
- Chưa có: hiển thị `Chưa xác định`.
- Đang bị AI hỏi thêm: highlight nhẹ.

Không nên giấu criteria trong JSON thô.

## 7. Recommendation panel

Khi có `recommendations`, frontend cần hiển thị danh sách KOL để Brand so sánh.

Mỗi KOL item nên có:

- Avatar.
- Tên hiển thị.
- Danh mục.
- Nền tảng chính.
- Follower.
- Engagement rate.
- Giá từ.
- Rating.
- Số booking đã hoàn thành.
- Match score.
- Lý do phù hợp (`reason`).

Layout một item đề xuất:

```txt
Avatar | Tên KOL                       Match score
       | Category chips
       | TikTok: 230k followers · ER 4.7%
       | Giá từ: 8.000.000đ · Rating 4.8 · 21 booking
       | Lý do: Phù hợp vì...
```

Nên có:

- Sort theo `matchScore`, follower, giá, rating.
- Nút xem chi tiết.
- Nút chọn KOL hoặc thêm vào shortlist nếu frontend có chức năng booking.

Không nên:

- Chỉ hiển thị text trả lời của AI mà không có danh sách KOL.
- Để match score không có ngữ cảnh.
- Hiển thị quá nhiều thông tin phụ làm rối item.

## 8. Empty states

Trước khi chat:

```txt
Nhập nhu cầu tìm KOL để bắt đầu.
```

Có thể hiển thị 3 ví dụ prompt ngắn:

- `Tìm KOL thời trang trên TikTok, trên 100k follower`
- `Tìm creator làm review mỹ phẩm, ngân sách dưới 8 triệu`
- `Tìm YouTuber công nghệ có engagement tốt`

Khi chưa có kết quả:

```txt
Chưa có KOL đề xuất. AI sẽ hiển thị kết quả sau khi đủ tiêu chí.
```

Khi backend không có KOL phù hợp:

```txt
Chưa tìm thấy KOL phù hợp với tiêu chí hiện tại. Hãy thử mở rộng ngân sách, nền tảng hoặc follower.
```

## 9. Loading states

Khi user gửi message:

- Disable input và nút gửi.
- Hiển thị assistant bubble dạng `Đang phân tích yêu cầu...`.
- Không làm layout nhảy.
- Nếu request lâu hơn 3 giây, hiển thị trạng thái cụ thể hơn: `Đang lấy dữ liệu KOL phù hợp...`.

Nếu request fail:

- Hiển thị lỗi rõ ràng.
- Cho phép gửi lại.
- Không xóa input hoặc conversation hiện tại.

Ví dụ lỗi:

```txt
Không thể lấy đề xuất lúc này. Vui lòng thử lại sau.
```

## 10. API integration

### Chat endpoint

Frontend gọi:

```http
POST /api/v1/chat
```

Request:

```json
{
  "brandId": 1,
  "conversationId": null,
  "message": "Tôi muốn tìm KOL thời trang trên TikTok, follower trên 100k"
}
```

Sau response đầu tiên, frontend phải lưu `conversationId` và gửi lại ở các lượt tiếp theo:

```json
{
  "brandId": 1,
  "conversationId": "uuid-tu-response-truoc",
  "message": "Ngân sách dưới 10 triệu"
}
```

Response quan trọng:

```json
{
  "conversationId": "...",
  "reply": "...",
  "intent": "recommend_kol",
  "criteria": {},
  "recommendations": [],
  "needClarification": false,
  "clarificationQuestions": []
}
```

Frontend phải render cả 3 phần:

- `reply` trong chat.
- `criteria` trong criteria summary.
- `recommendations` trong result panel.

### Recommendation endpoint

Nếu frontend đã có form filter riêng, có thể gọi:

```http
POST /api/v1/recommendations
```

Endpoint này phù hợp cho chế độ search/filter truyền thống, không cần hội thoại.

## 11. State management

Frontend nên quản lý các state chính:

- `conversationId`
- `messages`
- `criteria`
- `recommendations`
- `isLoading`
- `error`
- `activePanel` trên mobile

Không nên để `conversationId` mất khi user chuyển tab trong app. Có thể lưu trong route state, local storage ngắn hạn hoặc state manager của frontend.

Khi người dùng bấm “Cuộc trò chuyện mới”:

- Clear `conversationId`.
- Clear messages.
- Clear criteria.
- Clear recommendations.

## 12. Visual style

Giao diện nên theo hướng dashboard/SaaS:

- Nền trung tính.
- Border rõ nhưng nhẹ.
- Typography dễ đọc.
- Spacing đều.
- Card KOL compact, không quá bo tròn.
- Dùng màu nhấn cho match score, trạng thái và CTA.

Gợi ý màu:
theo chuẩn design của project.

## 13. Responsive behavior

Desktop:

- Chat và results hiển thị song song.
- Result panel có thể scroll độc lập.

Tablet:

- Có thể giữ 2 cột nếu đủ rộng.
- Nếu hẹp, chuyển sang tab.

Mobile:

- Dùng một cột.
- Input chat cố định dưới cùng.
- Result mở bằng tab hoặc bottom sheet.
- KOL card phải hiển thị đủ thông tin chính mà không bị tràn chữ.

## 14. Acceptance criteria

Giao diện được xem là đạt MVP nếu:

- User nhập được yêu cầu tìm KOL bằng tiếng Việt.
- Frontend gọi được `/api/v1/chat`.
- Frontend lưu và gửi lại `conversationId`.
- Criteria AI hiểu được hiển thị rõ.
- Nếu thiếu thông tin, frontend hiển thị câu hỏi làm rõ.
- Nếu có recommendations, frontend hiển thị danh sách KOL có match score và reason.
- Có loading state và error state.
- Dùng tốt trên desktop và mobile.
- Không phụ thuộc vào dữ liệu mock trong UI.

## 15. Prompt ngắn cho AI frontend builder

Nếu dùng AI để generate frontend, có thể đưa prompt sau:

```txt
Build a production-ready SaaS-style frontend screen for a KOL AI Assistant.

The screen is not a landing page. It is a working dashboard/chat tool for brands to find KOLs using natural language.

Use a two-panel desktop layout:
- Left: chat conversation with input, assistant replies, clarification questions, and loading/error states.
- Right: criteria summary and KOL recommendation results.

On mobile, use tabs for Chat and Results.

The frontend must call POST /api/v1/chat with brandId, conversationId, and message. It must persist conversationId from the first response and send it in later turns.

Render response.reply in the chat, response.criteria as a compact criteria summary, and response.recommendations as comparable KOL cards.

Each KOL card should show avatar, name, categories, platforms, followers, engagement rate, priceFrom, rating, completedBookingCount, matchScore, and reason.

Design style: clean SaaS dashboard, neutral background, compact cards, clear hierarchy, no marketing hero, no decorative gradients, no oversized landing-page sections.

Include states for empty chat, loading, needClarification, no results, backend error, and successful recommendations.
```

