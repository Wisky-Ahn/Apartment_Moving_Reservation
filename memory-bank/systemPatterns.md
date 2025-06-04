# 시스템 패턴 (System Patterns)

## 🏗️ **시스템 아키텍처**

### **전체 구조**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Docker        │
                    │   Compose       │
                    └─────────────────┘
```

### **프로젝트 디렉토리 구조**
```
fnm-main/
├── frontend/              # Next.js 애플리케이션
│   ├── src/
│   │   ├── app/           # App Router 페이지
│   │   │   ├── admin/     # 관리자 전용 페이지
│   │   │   ├── auth/      # 인증 관련 페이지
│   │   │   └── user/      # 사용자 페이지
│   │   ├── components/    # React 컴포넌트
│   │   │   ├── ui/        # 재사용 가능한 UI 컴포넌트
│   │   │   └── admin/     # 관리자 전용 컴포넌트
│   │   └── lib/           # 유틸리티 및 설정
├── backend/               # FastAPI 애플리케이션
│   ├── app/
│   │   ├── api/           # API 라우터
│   │   ├── models/        # SQLAlchemy 모델
│   │   ├── core/          # 핵심 설정
│   │   └── middleware/    # 미들웨어
├── .taskmaster/           # TaskMaster 프로젝트 관리
└── memory-bank/           # Memory Bank 문서
```

## 🔧 **주요 기술적 결정사항**

### **프론트엔드 아키텍처**
1. **Next.js 14 App Router**: 파일 기반 라우팅과 서버 컴포넌트 활용
2. **컴포넌트 패턴**: 
   - 페이지별 디렉토리 구조 (`/admin`, `/user`)
   - 재사용 가능한 UI 컴포넌트 (`/components/ui`)
   - 도메인별 컴포넌트 분리 (`/components/admin`)

### **백엔드 아키텍처**
1. **FastAPI**: 자동 문서 생성 및 타입 안전성
2. **SQLAlchemy ORM**: 데이터베이스 추상화 및 관계 관리
3. **Pydantic 스키마**: 데이터 검증 및 직렬화

### **인증 시스템**
1. **NextAuth.js**: 프론트엔드 세션 관리
2. **JWT 토큰**: 백엔드 API 인증
3. **역할 기반 권한**: 일반 사용자, 관리자, 슈퍼관리자

## 📊 **디자인 패턴**

### **API 디자인 패턴**
```python
# RESTful API 구조
GET    /api/notices/        # 목록 조회
POST   /api/notices/        # 신규 생성
GET    /api/notices/{id}    # 상세 조회
PUT    /api/notices/{id}    # 전체 수정
DELETE /api/notices/{id}    # 삭제
```

### **컴포넌트 패턴**
```typescript
// 컨테이너-프레젠테이션 패턴
const NoticesPage = () => {
  // 로직 처리 (Container)
  const [notices, setNotices] = useState([]);
  
  return (
    <NoticesList 
      notices={notices}     // 데이터 전달
      onEdit={handleEdit}   // 이벤트 핸들러
    />
  );
};
```

### **상태 관리 패턴**
1. **useState**: 로컬 컴포넌트 상태
2. **useSession**: 인증 상태 관리
3. **API 호출**: fetch/axios를 통한 서버 상태

### **에러 처리 패턴**
```typescript
// 프론트엔드 에러 처리
try {
  await apiCall();
  toast.success("성공 메시지");
} catch (error) {
  console.error("에러 로깅", error);
  toast.error("사용자 친화적 메시지");
}
```

```python
# 백엔드 에러 처리
@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "입력 데이터가 올바르지 않습니다."}
    )
```

## 🔄 **데이터 플로우**

### **인증 플로우**
```
1. 사용자 로그인 → NextAuth → JWT 토큰 생성
2. 프론트엔드 → Authorization Header → 백엔드
3. 백엔드 → JWT 검증 → 사용자 권한 확인
4. API 응답 → 프론트엔드 → UI 업데이트
```

### **CRUD 플로우**
```
1. 사용자 액션 → 컴포넌트 이벤트
2. API 호출 → 백엔드 엔드포인트
3. 데이터 검증 → 데이터베이스 작업
4. 응답 생성 → 프론트엔드 상태 업데이트
```

## 🛡️ **보안 패턴**

### **인증 보안**
- JWT 토큰 만료 시간 설정
- HTTPS 통신 강제
- CORS 정책 설정

### **데이터 검증**
- 프론트엔드: 실시간 폼 검증
- 백엔드: Pydantic 스키마 검증
- 데이터베이스: 제약 조건 설정

### **권한 관리**
```python
# 데코레이터 패턴으로 권한 검사
@admin_required
async def admin_only_endpoint():
    pass
```

## ⚡ **성능 패턴**

### **프론트엔드 최적화**
- 컴포넌트 지연 로딩 (React.lazy)
- 이미지 최적화 (Next.js Image)
- 번들 크기 최적화

### **백엔드 최적화**
- 데이터베이스 쿼리 최적화
- 응답 캐싱 (Redis 예정)
- 비동기 처리 (async/await)

### **현재 성능 이슈** ⚠️
- POST 요청 68초 응답시간
- 데이터베이스 연결 풀 문제 가능성
- 무한 루프 또는 블로킹 작업 의심 