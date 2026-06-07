# 07 - KOL Ranking Logic

## 1. Mục tiêu ranking

Sau khi retrieve được danh sách KOL candidates từ backend, AI Service cần chấm điểm để sắp xếp KOL phù hợp nhất lên đầu.

Không nên chỉ sort theo follower vì follower cao chưa chắc phù hợp. Ranking nên kết hợp nhiều yếu tố:

- Lĩnh vực.
- Nền tảng.
- Follower.
- Ngân sách.
- Engagement rate.
- Rating.
- Kinh nghiệm booking.

## 2. Công thức MVP

```txt
matchScore =
  categoryScore   * 0.30
+ platformScore   * 0.15
+ followerScore   * 0.20
+ budgetScore     * 0.15
+ engagementScore * 0.10
+ ratingScore     * 0.05
+ bookingScore    * 0.05
```

Tổng điểm từ 0 đến 100.

## 3. Thành phần điểm

### 3.1. Category Score

```txt
100 nếu KOL có category trùng yêu cầu
70 nếu category gần liên quan
0 nếu không liên quan
```

Ví dụ:

```txt
Yêu cầu: fashion
KOL categories: fashion, beauty
=> categoryScore = 100
```

### 3.2. Platform Score

```txt
100 nếu có platform yêu cầu
80 nếu user không yêu cầu platform cụ thể
0 nếu không có platform yêu cầu
```

### 3.3. Follower Score

Nếu user có `minFollowers`:

```txt
followers >= minFollowers => 100
followers >= minFollowers * 0.8 => 70
followers >= minFollowers * 0.5 => 40
else => 0
```

Nếu user không có follower requirement:

```txt
followerScore = min(100, log_scale_followers)
```

MVP đơn giản:

```txt
>= 1,000,000 => 100
>= 500,000 => 90
>= 100,000 => 80
>= 50,000 => 60
>= 10,000 => 40
else => 20
```

### 3.4. Budget Score

Nếu user có `maxBudget`:

```txt
price <= maxBudget => 100
price <= maxBudget * 1.2 => 70
price <= maxBudget * 1.5 => 40
else => 0
```

Nếu user không nhập ngân sách:

```txt
budgetScore = 80
```

### 3.5. Engagement Score

```txt
engagementRate >= 5% => 100
engagementRate >= 3% => 80
engagementRate >= 1% => 50
else => 20
```

### 3.6. Rating Score

```txt
rating >= 4.8 => 100
rating >= 4.5 => 90
rating >= 4.0 => 75
rating >= 3.5 => 50
else => 20
```

Nếu chưa có rating:

```txt
ratingScore = 60
```

### 3.7. Booking Score

```txt
completedBookingCount >= 20 => 100
completedBookingCount >= 10 => 80
completedBookingCount >= 3 => 60
completedBookingCount > 0 => 40
else => 20
```

## 4. Pseudo-code

```python
def calculate_match_score(kol, criteria):
    category_score = calculate_category_score(kol, criteria)
    platform_score = calculate_platform_score(kol, criteria)
    follower_score = calculate_follower_score(kol, criteria)
    budget_score = calculate_budget_score(kol, criteria)
    engagement_score = calculate_engagement_score(kol)
    rating_score = calculate_rating_score(kol)
    booking_score = calculate_booking_score(kol)

    score = (
        category_score * 0.30
        + platform_score * 0.15
        + follower_score * 0.20
        + budget_score * 0.15
        + engagement_score * 0.10
        + rating_score * 0.05
        + booking_score * 0.05
    )

    return round(score)
```

## 5. Reason generation không cần LLM vẫn làm được

MVP có thể tự sinh reason bằng template để tránh tốn token.

```python
def generate_reason(kol, criteria):
    reasons = []

    if criteria.category and criteria.category in kol.categories:
        reasons.append(f"thuộc lĩnh vực {criteria.category}")

    best_platform = get_best_matching_platform(kol, criteria)
    if best_platform:
        reasons.append(f"có {best_platform.followers:,} follower trên {best_platform.platform}")

    if criteria.maxBudget and kol.priceFrom and kol.priceFrom <= criteria.maxBudget:
        reasons.append("giá nằm trong ngân sách")

    if kol.averageRating and kol.averageRating >= 4.5:
        reasons.append(f"rating cao {kol.averageRating}/5")

    if not reasons:
        return "KOL này có thông tin tương đối phù hợp với yêu cầu tìm kiếm."

    return "Phù hợp vì " + ", ".join(reasons) + "."
```

## 6. Output recommendation DTO

```json
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
  "reason": "Phù hợp vì thuộc lĩnh vực fashion, có 230,000 follower trên TikTok, giá nằm trong ngân sách và rating cao 4.8/5."
}
```

## 7. Ranking rule nâng cao sau MVP

Sau MVP có thể thêm:

- Semantic similarity giữa campaign goal và bio/portfolio của KOL.
- Historical booking success rate.
- Brand industry match.
- Audience demographics.
- Location priority.
- Availability.
- Response time.
