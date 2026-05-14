-- =============================================================================
-- 2026-05-12: 기존 soft-deleted users.provider_id 에 suffix backfill
--
-- 사유: 회원탈퇴 정책 (가을쥐 결정 2026-05-12) = 동일 소셜 계정 재가입 시 새
--      users.id 로 신규 계정 생성, 기존 데이터 미연결.
--      그러나 UNIQUE (provider, provider_id) 제약 (uq_users_provider) 으로
--      soft-deleted user 가 자리를 차지하고 있으면 IntegrityError 1062 발생.
--
--      직전 라운드에서 user_service.delete_user 가 탈퇴 즉시 provider_id 에
--      `__deleted_<timestamp>` suffix 박도록 정정. 본 SQL 은 코드 정정 이전에
--      이미 soft-deleted 된 운영 RDS row 를 같은 패턴으로 일괄 backfill 한다.
--
-- 적용 효과:
--   - soft-deleted user 의 provider_id = "kakao_12345" → "kakao_12345__deleted_<ts>"
--   - 동일 소셜 계정 재로그인 시 UNIQUE 충돌 없이 신규 user 생성 가능
--   - 10일 후 hard_delete_withdrawn_users 배치가 deleted_at 기준으로 정리하므로
--     mangle 된 provider_id 도 자연 사라짐
--
-- idempotency: provider_id 가 이미 `__deleted_` 패턴 포함하면 skip (재실행 안전).
--
-- 본 파일은 가을쥐가 운영 RDS 에서 직접 실행하며, 적용 후 삭제 가능.
-- =============================================================================


-- =========================================
-- DRY RUN 1: 영향 받는 soft-deleted 사용자 수
-- =========================================
SELECT COUNT(*) AS soft_deleted_users
FROM users
WHERE deleted_at IS NOT NULL
  AND provider_id NOT LIKE '%\_\_deleted\_%' ESCAPE '\\';


-- =========================================
-- DRY RUN 2: 매핑 미리보기
-- 각 row 의 원본 provider_id, 변경될 suffix 값 확인.
-- =========================================
SELECT
  id,
  provider,
  provider_id AS original_provider_id,
  CONCAT(provider_id, '__deleted_', UNIX_TIMESTAMP(deleted_at)) AS new_provider_id,
  deleted_at
FROM users
WHERE deleted_at IS NOT NULL
  AND provider_id NOT LIKE '%\_\_deleted\_%' ESCAPE '\\';


-- =========================================
-- 마이그레이션 실행 (트랜잭션)
-- =========================================

START TRANSACTION;

UPDATE users
SET provider_id = CONCAT(provider_id, '__deleted_', UNIX_TIMESTAMP(deleted_at))
WHERE deleted_at IS NOT NULL
  AND provider_id NOT LIKE '%\_\_deleted\_%' ESCAPE '\\';

COMMIT;
-- 실패 시 ROLLBACK; idempotent 라 재실행 안전.


-- =========================================
-- 검증 SELECT (COMMIT 이후 실행)
-- =========================================

-- 1. soft-deleted user 중 mangle 안 된 row 0건 확인
SELECT COUNT(*) AS remaining_unmangled
FROM users
WHERE deleted_at IS NOT NULL
  AND provider_id NOT LIKE '%\_\_deleted\_%' ESCAPE '\\';
-- 기대: 0

-- 2. mangle 된 row 패턴 확인
SELECT id, provider, provider_id, deleted_at
FROM users
WHERE deleted_at IS NOT NULL
  AND provider_id LIKE '%\_\_deleted\_%' ESCAPE '\\';

-- 3. 활성 user 중 mangle suffix 가 잘못 박힌 row 0건 확인 (정합 보호)
SELECT COUNT(*) AS active_with_mangle_suffix
FROM users
WHERE deleted_at IS NULL
  AND provider_id LIKE '%\_\_deleted\_%' ESCAPE '\\';
-- 기대: 0
