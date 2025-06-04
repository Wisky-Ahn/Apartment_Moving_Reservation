# 기술 컨텍스트 (Tech Context)

## 🛠️ **기술 스택**

### **프론트엔드**
```json
{
  "framework": "Next.js 14.0+",
  "language": "TypeScript",
  "styling": "Tailwind CSS",
  "components": "shadcn/ui",
  "icons": "Lucide React",
  "authentication": "NextAuth.js",
  "forms": "React Hook Form",
  "state": "React Hooks (useState, useEffect)",
  "http": "fetch API",
  "routing": "App Router (Next.js 14)"
}
```

### **백엔드**
```json
{
  "framework": "FastAPI",
  "language": "Python 3.11+",
  "orm": "SQLAlchemy 2.0+",
  "database": "PostgreSQL",
  "validation": "Pydantic v2",
  "auth": "JWT (python-jose)",
  "cors": "FastAPI CORS Middleware",
  "logging": "Python logging",
  "async": "asyncio, asyncpg"
}
```

### **개발 도구**
```json
{
  "containerization": "Docker Compose",
  "package_manager_fe": "npm",
  "package_manager_be": "pip",
  "code_quality": "ESLint, Prettier (FE), Black (BE)",
  "project_management": "TaskMaster AI",
  "documentation": "Memory Bank"
}
```

## 🐳 **Docker 구성**

### **docker-compose.yml 구조**
```yaml
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NEXTAUTH_SECRET
      - NEXTAUTH_URL
    
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL
      - JWT_SECRET_KEY
    depends_on: [db]
    
  db:
    image: postgres:15
    ports: ["5432:5432"]
    environment:
      - POSTGRES_DB=fnm_db
      - POSTGRES_USER=fnm_user
      - POSTGRES_PASSWORD
```

## 🗄️ **데이터베이스 설계**

### **주요 엔티티**
```sql
-- 사용자 테이블
Users (
  id: UUID PRIMARY KEY,
  email: VARCHAR UNIQUE,
  name: VARCHAR,
  role: ENUM('user', 'admin', 'super_admin'),
  apartment_unit: VARCHAR,
  phone: VARCHAR,
  is_active: BOOLEAN,
  created_at: TIMESTAMP,
  updated_at: TIMESTAMP
)

-- 예약 테이블
Reservations (
  id: UUID PRIMARY KEY,
  user_id: UUID FOREIGN KEY,
  reservation_date: DATE,
  start_time: TIME,
  end_time: TIME,
  status: ENUM('pending', 'approved', 'rejected', 'cancelled'),
  notes: TEXT,
  created_at: TIMESTAMP,
  updated_at: TIMESTAMP
)

-- 공지사항 테이블
Notices (
  id: UUID PRIMARY KEY,
  title: VARCHAR,
  content: TEXT,
  author_id: UUID FOREIGN KEY,
  is_important: BOOLEAN,
  view_count: INTEGER,
  created_at: TIMESTAMP,
  updated_at: TIMESTAMP
)
```

### **관계 설정**
- Users 1:N Reservations (사용자별 여러 예약)
- Users 1:N Notices (작성자별 여러 공지사항)
- 제약 조건: 동일 시간대 중복 예약 방지

## 🔧 **환경 변수 관리**

### **프론트엔드 (.env.local)**
```bash
# NextAuth 설정
NEXTAUTH_SECRET=your-secret-key
NEXTAUTH_URL=http://localhost:3000

# API 엔드포인트
NEXT_PUBLIC_API_URL=http://localhost:8000

# 기타 설정
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### **백엔드 (.env)**
```bash
# 데이터베이스
DATABASE_URL=postgresql://fnm_user:password@localhost:5432/fnm_db

# JWT 인증
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 설정
CORS_ORIGINS=["http://localhost:3000"]
```

## 📡 **API 설계**

### **인증 엔드포인트**
```python
POST /api/auth/login      # 로그인
POST /api/auth/register   # 회원가입
POST /api/auth/logout     # 로그아웃
GET  /api/auth/me         # 현재 사용자 정보
```

### **예약 관리 엔드포인트**
```python
GET    /api/reservations/           # 예약 목록
POST   /api/reservations/           # 예약 생성
GET    /api/reservations/{id}       # 예약 상세
PUT    /api/reservations/{id}       # 예약 수정
DELETE /api/reservations/{id}       # 예약 삭제
PUT    /api/reservations/{id}/approve  # 예약 승인 (관리자)
```

### **공지사항 엔드포인트**
```python
GET    /api/notices/               # 공지사항 목록
POST   /api/notices/               # 공지사항 생성 (관리자)
GET    /api/notices/{id}           # 공지사항 상세
PUT    /api/notices/{id}           # 공지사항 수정 (관리자)
DELETE /api/notices/{id}           # 공지사항 삭제 (관리자)
```

### **관리자 엔드포인트**
```python
GET    /api/admin/users/           # 사용자 목록 (관리자)
PUT    /api/admin/users/{id}       # 사용자 정보 수정 (관리자)
GET    /api/admin/statistics/      # 통계 데이터 (관리자)
```

## 🧪 **개발 워크플로우**

### **로컬 개발 환경**
1. **초기 설정**:
   ```bash
   git clone [repository]
   cd fnm-main
   docker-compose up -d
   ```

2. **프론트엔드 개발**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **백엔드 개발**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

### **코드 품질 관리**
- **프론트엔드**: ESLint + Prettier 자동 포맷팅
- **백엔드**: Black + isort 코드 스타일
- **타입 체크**: TypeScript (FE), mypy (BE)

## 🔍 **모니터링 및 로깅**

### **로그 시스템**
```python
# 백엔드 로깅 설정
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
```

### **성능 모니터링**
- **API 응답 시간**: middleware를 통한 자동 로깅
- **데이터베이스 쿼리**: SQLAlchemy 로깅
- **프론트엔드 성능**: Web Vitals 측정

## ⚡ **성능 최적화**

### **현재 구현된 최적화**
- Next.js 자동 코드 분할
- SQLAlchemy 연결 풀링
- Static/Dynamic 페이지 분리

### **개선 필요 영역** ⚠️
- **데이터베이스 쿼리 최적화**: N+1 문제 해결
- **API 응답 캐싱**: Redis 도입 필요
- **프론트엔드 번들 최적화**: Dynamic import 확대

## 🛡️ **보안 구현**

### **현재 보안 조치**
- JWT 토큰 기반 인증
- CORS 정책 설정
- SQL Injection 방지 (ORM 사용)
- XSS 방지 (React 기본 보호)

### **추가 보안 계획**
- Rate limiting 구현
- HTTPS 강제 설정
- 입력 데이터 sanitization
- 세션 관리 개선 