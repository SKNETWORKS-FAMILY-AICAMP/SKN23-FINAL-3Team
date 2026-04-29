# withDOG 시스템 아키텍처 설명

> SKN23-FINAL-3TEAM (케르베로스) — 반려견 동반 장소 추천 챗봇 + AI 그림일기 서비스
> 작성일: 2026-04-29

## 0. 한 줄 요약

withDOG 는 React 프론트엔드 ↔ Nginx ↔ FastAPI ↔ RDB·ChromaDB·S3·OpenAI API 의 **4 계층 구조** 로 동작한다. 사용자 메시지는 KoELECTRA 의도 분류기를 거쳐 다이어리·장소추천·시설정보·기타 4 분기로 라우팅되며, 모든 외부 통신은 HTTPS 기반이다.

## 1. 전체 구성

| 계층 | 구성 |
| --- | --- |
| **1) 클라이언트** | React 18 + TypeScript 5 + Vite 6 / Tailwind CSS v4 / Radix UI 50+ / Kakao Maps SDK / OAuth 2.0 |
| **2) 서비스** | Nginx (Reverse Proxy, HTTPS) + FastAPI 백엔드 (Python 3.10.12) + KoELECTRA 의도 분류기 + AIContainer (DI) + 12 라우터 × 16 서비스 |
| **3) 데이터·AI** | AWS RDS MySQL 8.0 (9 테이블) + ChromaDB Persistent (3 컬렉션) + AWS S3 (이미지) + OpenAI API |
| **4) 외부 연동** | 한국관광공사 OpenAPI / The Dog API / Dog CEO API / OAuth 2.0 (Google·Kakao·Naver) / Kakao Maps SDK |

## 2. 클라이언트 계층 (Client Layer)

### 2-1. 프론트엔드 스택

- **React 18.2 + TypeScript 5 (strict) + Vite 6** (개발 서버 port 3000)
- **Tailwind CSS v4** (OKLch 컬러 + `@theme` 디자인 토큰)
- **Radix UI 50+** 헤드리스 컴포넌트 (`src/app/components/ui/` 에 자체 래퍼, shadcn/ui 패턴)
- **React Router v7** 라우팅
- **Motion (Framer Motion 후속)** 애니메이션, **Recharts** 차트, **react-hook-form** 폼 관리
- 패키지 매니저: pnpm

### 2-2. 화면 구성

- `/` HomePage (탭: 일기 / 지도 / 소개영상)
- `/login` LoginPage — OAuth 3종 버튼
- `/oauth/callback` 토큰 교환 콜백
- `/calendar` 월별 캘린더 (다이어리 핀)
- `/step` 가입 2단계 (보호자 + 반려견 등록)
- `/mypage` 반려견 관리

### 2-3. 인증 흐름

OAuth 2.0 Authorization Code Grant — Google / Kakao / Naver 3종.

```
사용자 → /login → provider redirect → callback (code 수신)
       → POST /api/auth/{provider} → JWT 발급
       → localStorage.access_token 저장 → /home 진입
```

### 2-4. 외부 SDK

- **Kakao Maps SDK** — 지도 렌더링·마커. `index.html` 에서 `VITE_KAKAO_JAVASCRIPT_API_KEY` 로 로드

## 3. 서비스 계층 (Service Layer)

### 3-1. Nginx (Reverse Proxy)

- AWS EC2 동일 호스트, Docker Compose 컨테이너
- **HTTPS (Let's Encrypt 인증서, `withdog.kro.kr` 도메인)** → 내부는 HTTP 로 FastAPI 에 `proxy_pass`
- `/api/*` 만 백엔드 라우팅, 그 외는 React `dist/` 정적 자산 + SPA fallback
- gzip 압축

### 3-2. FastAPI 백엔드

- **Python 3.10.12** (AWS EC2 운영 검증), FastAPI, port 8000
- **SQLAlchemy 2.0 (async) + aiomysql** — 비동기 DB 액세스
- **APScheduler** — 매일 03:00 KST 탈퇴 사용자 hard delete 배치

### 3-3. AI 컴포넌트

| 컴포넌트 | 역할 |
| --- | --- |
| **KoELECTRA 의도 분류기** | 사용자 메시지를 4 라벨로 분류 — 다이어리 / 장소추천 / 시설정보 / 기타. 자체 학습 (1117 샘플 / 정확도 0.9955, 4 카테고리) |
| **AIContainer (DI 컨테이너)** | PlacesChain, DiaryChain, Retrievers, QueryParser 를 의존성 주입으로 관리 |
| **12 라우터 × 16 서비스** | chat / diary / place / auth / image / facility 등 도메인별 분리. 각 서비스가 RDB·ChromaDB·OpenAI API 를 조합 |

### 3-4. 비동기 패턴

모든 블로킹 호출 (RAG 검색·LLM 호출·임베딩) 은 `asyncio.to_thread` 로 스레드 풀에 위임 → FastAPI 이벤트 루프가 논블로킹 유지.

### 3-5. 의도 분기 흐름

```
사용자 메시지
  → KoELECTRA → 4 라벨
       │
       ├── 장소추천  → PlacesChain → ChromaDB top_k 검색
       │                          → MySQL JOIN (places 메타)
       │                          → DogScorer/OwnerScorer 재순위
       │                          → gpt-4.1-mini 추천 이유 생성
       │
       ├── 다이어리  → DiaryChain → 6하원칙 수집 (follow-up)
       │                          → gpt-4.1-mini 본문 생성
       │                          → gpt-image-1 이미지 생성
       │                          → AWS S3 업로드
       │                          → MySQL diaries 적재 (2-phase)
       │
       ├── 시설정보  → FacilityQueryParser → MySQL places 조회
       │                                   → 카드 응답
       │
       └── 기타       → gpt-4.1-mini 일반 챗봇 응답
```

## 4. 데이터 + AI 계층 (Data + AI Layer)

### 4-1. 관계형 DB (AWS RDS MySQL 8.0)

**9 테이블** — `users`, `pets`, `breeds`, `keywords`, `chat_rooms`, `chat_messages`, `diaries`, `images`, `places`.

- charset `utf8mb4_unicode_ci`, InnoDB, 시간대 `Asia/Seoul`
- Soft Delete 정책: 5 테이블 (`users`·`pets`·`chat_rooms`·`diaries`·`images`) `deleted_at` 적용
- `users` 만 10일 후 hard delete (APScheduler)
- 컬럼·관계 상세는 별도 [데이터베이스 설계문서] 참조

### 4-2. 벡터 DB (ChromaDB Persistent)

로컬 영속 저장 (`data/chroma_db/`), Python 클라이언트 in-process 통합 — 별도 컨테이너 불요.

| 컬렉션 | 규모 | 출처 |
| --- | --- | --- |
| **places** | 21,130건 | 한국관광공사 OpenAPI 시드 |
| **dog_breeds** | 357종 | The Dog API 시드 |
| **diaries** | incremental | 사용자 다이어리 생성 시 누적 임베딩 |

- 임베딩 모델: **`jhgan/ko-sroberta-multitask`** (한국어 특화 sentence-transformers, 384 차원)
- 운영 시 다른 벡터 DB (Pinecone/Qdrant) 로 교체 가능한 추상화 (`vector_store` base class) 유지

### 4-3. 이미지 저장소 (AWS S3)

- 다이어리 이미지 + 프로필 사진
- 이미지 메타 (`file_url`, `file_name`) 만 RDB `images` 테이블에 기록
- 흐름: 이미지 생성 → S3 업로드 → DB PATCH 의 **2-phase 저장** (RDB 트랜잭션과 비동기 이미지 처리 분리)

### 4-4. AI 모델 (OpenAI API)

- **텍스트**: `gpt-4.1-mini` — 다이어리 본문, 추천 이유 생성, 일반 응답
- **이미지 (다층 전략)**:
  - 메인 `gpt-image-1` (무료+유료, quality flat-rate, 그림체 일관성 우위)
  - 유료 플랜 서브 `gpt-image-2` + huggingface 호스팅 diffusion 모델 (FLUX/Stable Diffusion 계열)
  - 추가 고도화 후보: ComfyUI 워크플로우 + Civitai LoRA

## 5. 외부 연동 (External Integrations)

| 외부 시스템 | 용도 | 호출 시점 |
| --- | --- | --- |
| **한국관광공사 OpenAPI** | 반려동물 동반 장소 데이터 (21,130건) | 1회성 시드 |
| **The Dog API** | 견종 357종 마스터 데이터 + 영문 temperament | 1회성 시드 |
| **Dog CEO API** | 견종 대표 이미지 | 가입 단계 + 캐시 |
| **OAuth 2.0** (Google / Kakao / Naver) | 소셜 로그인 | 매 로그인 |
| **Kakao Maps SDK** | 프론트 지도 렌더링 | 지도 화면 진입 |

## 6. 핵심 설계 결정 (요약)

자세한 사유는 별도 의사결정 문서·위키 참조.

- **ChromaDB 채택** (vs Pinecone) — 로컬·무료·빠른 실험 반복. 운영 시 다른 벡터 DB 로 교체 가능한 추상화 유지로 락인 회피
- **KoELECTRA 의도 분류** (vs LLM zero-shot) — 한국어 특화 사전학습 + 비용·레이턴시·온프레미스 가능성. 매 메시지마다 LLM 호출 회피
- **OpenAI SDK 직호출** (vs LangChain) — DiaryChain 등 자체 체인 추상으로 운영 중. LangChain 도입은 멀티 에이전트 확장 시점에 LangGraph 와 함께 검토 (발표 후 고도화 1순위)
- **2-phase 다이어리 저장** — 이미지 생성·S3 업로드의 비동기 특성을 RDB 트랜잭션과 분리. `image_id` nullable 로 행 먼저 생성 후 PATCH 바인딩
- **다층 이미지 모델 전략** — 무료 사용자에게는 안정적 그림체 (gpt-image-1) 제공, 유료에서는 다양성 옵션 (gpt-image-2 / diffusion). 비용 절감 (-66%) 보다 그림체 균질성 우선

## 7. 요청 흐름 예시 — 장소 추천

```
사용자 "강아지 데리고 갈 카페 추천"
  → 브라우저 → HTTPS (port 443)
  → Nginx → proxy_pass → FastAPI (port 8000)
  → KoELECTRA 의도 분류 → "장소추천" (확률 > 임계값)
  → PlacesChain
       ├── 임베딩 (jhgan/ko-sroberta-multitask)
       ├── ChromaDB places 컬렉션 top_k=5 검색
       ├── MySQL JOIN — places 메타 (sub_category, entrance_fee_type 등)
       ├── DogScorer / OwnerScorer 재순위 (성향 점수 가중)
       └── gpt-4.1-mini 추천 이유 생성 (asyncio.to_thread)
  → JSON 응답
  → React 카드 렌더링 + Kakao Maps 마커 표시
```

## 8. 보안·운영

- **HTTPS 전체 구간** — Let's Encrypt 인증서, withdog.kro.kr
- **인증** — OAuth 2.0 + JWT (`Authorization: Bearer`). 401 응답 시 자동 로그아웃 + `auth-change` 이벤트
- **비밀 키 관리** — `.env` (gitignore + .dockerignore), 운영 EC2 별도 배치
- **시드 1회성 분리** — 한국관광공사·The Dog API 는 1회 적재 후 운영 호출 없음 → 외부 의존성 최소화
- **소프트 삭제 + 10일 grace** — 사용자 탈퇴 후 10일 내 복구 가능, APScheduler 가 03:00 KST hard delete

## 9. 데이터 규모 스냅샷 (2026-04 시점)

| 항목 | 규모 |
| --- | --- |
| 견종 마스터 (`breeds` + ChromaDB `dog_breeds`) | 357종 |
| 장소 (`places` + ChromaDB `places`) | 21,130건 (한국관광공사 2025-03-24 데이터) |
| 의도 분류 학습 샘플 | 1117 샘플 (4 카테고리, 정확도 0.9955) |

---

*본 문서는 wiki 권위 (`wiki/01-arch/arch-overview.md`, `wiki/01-arch/arch-system.md`, `wiki/03-db/db-schema.md`, 의사결정 문서) 와 시스템 아키텍처 다이어그램을 통합해 작성되었다. 다이어그램 일부 표기 (Python 버전·이미지 모델·테이블 개수) 는 본 문서가 최신 권위.*
