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
│   └── package.json   # 프론트엔드 의존성
├── backend/           # FastAPI 백엔드
│   ├── app/
│   │   ├── api/       # API 라우터
│   │   ├── models/    # 데이터베이스 모델
│   │   └── core/      # 핵심 설정
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

## 🔐 환경 변수

### 프론트엔드 (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key
```

### 백엔드 (.env)
```
DATABASE_URL=postgresql://fnmuser:fnmpassword@localhost:5432/fnm_db
```

## 🤝 기여하기

1. 이 저장소를 포크합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성합니다

