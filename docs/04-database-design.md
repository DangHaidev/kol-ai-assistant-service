# 04 - Database Design

## 1. Mục tiêu database AI Service

AI Service cần database riêng hoặc schema riêng để lưu:

- Conversation.
- Messages.
- Current criteria của từng conversation.
- Metadata xử lý AI.
- Log recommendation nếu cần phân tích sau này.

Không nên lưu lại toàn bộ dữ liệu nhạy cảm của backend chính.

## 2. Option triển khai

### Option A: Dùng chung PostgreSQL với backend chính

Tạo schema riêng:

```sql
CREATE SCHEMA IF NOT EXISTS ai_assistant;
```

Ưu điểm:

- Dễ chạy local.
- Không cần thêm database server.
- Phù hợp đồ án.

Nhược điểm:

- Cần quản lý quyền truy cập cẩn thận.

### Option B: Database riêng cho AI Service

Ưu điểm:

- Tách biệt tốt hơn.
- Dễ deploy độc lập.

Nhược điểm:

- Cấu hình nhiều hơn.

MVP nên dùng Option A hoặc một PostgreSQL container riêng đều được.

## 3. Bảng `ai_conversations`

Lưu một phiên hội thoại.

```sql
CREATE TABLE ai_conversations (
    id UUID PRIMARY KEY,
    brand_id BIGINT NOT NULL,
    title VARCHAR(255),
    current_criteria JSONB,
    last_intent VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Field description

| Field | Type | Description |
|---|---|---|
| id | UUID | ID hội thoại |
| brand_id | BIGINT | ID Brand từ backend chính |
| title | VARCHAR | Tiêu đề hội thoại |
| current_criteria | JSONB | Criteria đã merge qua nhiều lượt chat |
| last_intent | VARCHAR | Intent gần nhất |
| created_at | TIMESTAMP | Thời điểm tạo |
| updated_at | TIMESTAMP | Thời điểm cập nhật |

## 4. Bảng `ai_messages`

Lưu từng message trong hội thoại.

```sql
CREATE TABLE ai_messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES ai_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Role hợp lệ

```txt
user
assistant
system
```

### Metadata ví dụ

```json
{
  "intent": "recommend_kol",
  "extractedCriteria": {
    "category": "fashion",
    "minFollowers": 100000
  },
  "recommendationCount": 5
}
```

## 5. Bảng `ai_recommendation_logs`

Không bắt buộc trong MVP, nhưng nên có nếu muốn debug/tối ưu.

```sql
CREATE TABLE ai_recommendation_logs (
    id BIGSERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES ai_conversations(id) ON DELETE SET NULL,
    brand_id BIGINT NOT NULL,
    criteria JSONB NOT NULL,
    kol_results JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

`kol_results` chỉ nên lưu snapshot ngắn:

```json
[
  {
    "kolId": 12,
    "matchScore": 92,
    "reason": "Matched fashion, follower and budget"
  }
]
```

## 6. Optional: bảng `kol_embeddings`

Chỉ dùng nếu sau này làm semantic search.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE kol_embeddings (
    kol_id BIGINT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

MVP chưa cần bảng này.

## 7. Alembic Migration mẫu

File:

```txt
migrations/versions/001_create_ai_conversation_tables.py
```

Nội dung tham khảo:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("brand_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("current_criteria", postgresql.JSONB(), nullable=True),
        sa.Column("last_intent", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "ai_messages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "ai_recommendation_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_conversations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("brand_id", sa.BigInteger(), nullable=False),
        sa.Column("criteria", postgresql.JSONB(), nullable=False),
        sa.Column("kol_results", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )


def downgrade():
    op.drop_table("ai_recommendation_logs")
    op.drop_table("ai_messages")
    op.drop_table("ai_conversations")
```
