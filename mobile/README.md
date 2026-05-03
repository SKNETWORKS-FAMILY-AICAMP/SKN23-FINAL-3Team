# withdog_app — Flutter 모바일 앱

withDOG = 반려견 동반 장소 추천 챗봇 (메인) + AI 그림일기 (보조). React 웹 풀 기능 포팅 — 5/20 시연 데모용.

권위 wiki: `D:/Obsidian/withDOG/wiki/04-feature/feature-flutter-app.md`

## 환경 설정 — monorepo 최상위 `.env` 단일 source

본 디렉토리(`mobile/`)에는 별도 `.env` 를 두지 않는다. 대신 **저장소 root 의 `.env`** (`D:/SKN AI/Project/SKN23-FINAL-3TEAM/.env`) 를 모든 환경(front·mobile·back) 이 공유한다.

front (vite) 도 같은 패턴: `front/vite.config.ts` 의 `envDir: '../'` 가 `../​.env` 를 올린다.

### 키 prefix 규약

- `VITE_*` — 웹(front) 전용. Vite 가 자동 노출
- `MOBILE_*` — 앱(mobile) 전용. `--dart-define-from-file` 로 주입
- prefix 없음 — 백엔드 공용

### 모바일에서 사용하는 키

| 키 | 기본값 (`Env` 클래스) | 비고 |
| --- | --- | --- |
| `MOBILE_API_BASE_URL` | `https://withdog.kro.kr/api` | FastAPI 운영 endpoint |
| `MOBILE_OAUTH_CALLBACK_URL` | `https://withdog.kro.kr/oauth/callback` | OAuth WebView 가로채기 콜백 URL |
| `VITE_KAKAO_JAVASCRIPT_API_KEY` | (필수) | 카카오맵 JS SDK 임베드용. front 와 공유 |

기본값은 `lib/core/env/env.dart` 의 `String.fromEnvironment(..., defaultValue: ...)` 에 박혀 있어 root `.env` 가 비어 있어도 운영 endpoint 로 동작한다. Kakao key 만 root `.env` 에 있어야 지도 탭이 작동한다.

## 빌드·실행

### CLI

```bash
# 디버그 (Android 에뮬레이터)
cd mobile
flutter run --dart-define-from-file=../.env

# release 검증
flutter run --release --dart-define-from-file=../.env

# 분석·테스트 (env 주입 없이도 동작 — 기본값)
flutter analyze
flutter test
```

### VS Code 디버거

`.vscode/launch.json` (저장소 root) 에 등록된 두 구성:

- **withdog_app (debug, monorepo .env)** — 일반 개발용
- **withdog_app (release, monorepo .env)** — 시연 직전 검증용

둘 다 `cwd = mobile`, `--dart-define-from-file=../.env` 자동 주입.

## 앱 식별자

- Android applicationId / namespace / Kotlin package = `com.withdog.app`
- iOS bundle id = `com.withdog.withdogApp` (default 잔존, iOS 진입 시 정정 예정)
- 앱 라벨 = `withDOG`
- minSdk = 21 (`flutter_inappwebview` 6.x 요구)
