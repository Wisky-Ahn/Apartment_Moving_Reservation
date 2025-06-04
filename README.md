# FNM - 아파트 이사 예약 관리 시스템

## 📁 프로젝트 구조

```
fnm-main/
├── frontend/          # Next.js 프론트엔드
│   ├── src/
│   │   ├── app/       # App Router 페이지
│   │   └── components/ # React 컴포넌트
│   ├── lib/           # 유틸리티 및 설정
│   ├── types/         # TypeScript 타입 정의
│   ├── .env.local     # 프론트엔드 환경변수 (필수)
│   └── package.json   # 프론트엔드 의존성
├── backend/           # FastAPI 백엔드
│   ├── app/
│   │   ├── api/       # API 라우터
│   │   ├── models/    # 데이터베이스 모델
│   │   └── core/      # 핵심 설정
│   ├── .env           # 백엔드 환경변수 (필수)
│   └── requirements.txt # 백엔드 의존성
├── docker-compose.yml # 전체 스택 Docker 설정
└── package.json       # 루트 레벨 스크립트
```

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
npm run install:all
```

### 2. 개발 서버 실행
```bash
# 프론트엔드 + 백엔드 동시 실행
npm run dev

# 또는 개별 실행
npm run dev:frontend  # http://localhost:3000
npm run dev:backend   # http://localhost:8000
```

### 3. Docker로 실행
```bash
docker-compose up -d
```

## ✅ 서버 상태 확인

### 정상 작동 확인
- **프론트엔드**: ✅ http://localhost:3000 (정상 작동)
- **백엔드**: ✅ http://localhost:8000 (정상 작동)
- **데이터베이스**: ✅ PostgreSQL 연결 및 테이블 생성 완료
- **API 문서**: ✅ http://localhost:8000/docs (Swagger UI)

### 해결된 이슈
- ✅ **로딩 문제 해결**: 프론트엔드 무한 로딩 문제 해결 (5초 타임아웃 로직 추가)
- ✅ **의존성 호환성**: pydantic 버전 업데이트로 모듈 오류 해결
- ✅ **환경변수 설정**: NextAuth 및 API 연결 정상화

## 🛠️ 개발 환경 설정

### 프론트엔드 (Next.js)
- **위치**: `frontend/`
- **포트**: 3000
- **기술 스택**: Next.js 14, TypeScript, Tailwind CSS, NextAuth

### 백엔드 (FastAPI)
- **위치**: `backend/`
- **포트**: 8000
- **기술 스택**: FastAPI, SQLAlchemy, PostgreSQL

### 데이터베이스 (PostgreSQL)
- **포트**: 5432
- **데이터베이스**: fnm_db
- **사용자**: fnmuser

## 📋 주요 기능

- ✅ 사용자 인증 (NextAuth + JWT)
- ✅ 회원가입 시스템
- ✅ 예약 관리
- ✅ 공지사항 관리
- ✅ 관리자 대시보드

## 🔧 스크립트 명령어

```bash
npm run dev           # 전체 개발 서버 실행
npm run dev:frontend  # 프론트엔드만 실행
npm run dev:backend   # 백엔드만 실행
npm run build         # 프론트엔드 빌드
npm run install:all   # 모든 의존성 설치
npm run clean         # 캐시 및 빌드 파일 정리
```

## 🐳 Docker 명령어

```bash
docker-compose up -d     # 전체 스택 실행
docker-compose down      # 전체 스택 종료
docker-compose logs -f   # 로그 확인
```

## 📝 API 문서

백엔드 API 문서는 개발 서버 실행 후 다음 주소에서 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔐 환경 변수 설정

### 프론트엔드 환경변수 (frontend/.env.local)
**⚠️ 필수 파일**: 프론트엔드 실행을 위해 반드시 생성해야 합니다.

```bash
# API 연결 설정
NEXT_PUBLIC_API_URL=http://localhost:8000

# NextAuth 설정 (인증 시스템)
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key-change-this-in-production-please-123456789

# 추가 설정 (선택사항)
NODE_ENV=development
```

### 백엔드 환경변수 (backend/.env)
**⚠️ 필수 파일**: 백엔드 서버 실행을 위해 반드시 생성해야 합니다.

```bash
# 데이터베이스 연결
DATABASE_URL=postgresql://fnmuser:fnmpassword@localhost:5432/fnm_db

# 보안 키 설정
SECRET_KEY=your-backend-secret-key-change-this-in-production
NEXTAUTH_SECRET=your-secret-key-change-this-in-production-please-123456789

# CORS 설정 (프론트엔드 연결 허용)
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# 환경 설정
ENVIRONMENT=development
DEBUG=True
```

### 환경변수 파일 생성 방법

1. **프론트엔드 환경변수 생성**:
```bash
touch frontend/.env.local
# 위의 내용을 복사하여 파일에 붙여넣기
```

2. **백엔드 환경변수 생성**:
```bash
touch backend/.env
# 위의 내용을 복사하여 파일에 붙여넣기
```

3. **환경변수 적용 확인**:
```bash
# 개발 서버 재시작
npm run dev
```

## 🤝 기여하기

1. 이 저장소를 포크합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성합니다

