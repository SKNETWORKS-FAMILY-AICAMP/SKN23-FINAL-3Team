-- =============================================================================
-- 2026-05-14: users 테이블에 약관·개인정보처리방침 동의 시점 컬럼 추가
--
-- 사유: 회원가입 시 약관/개인정보 명시 동의 의무 (정보통신망법 제22조).
--      기존에는 가입 화면에 동의 체크박스/링크 자체가 없었음.
--      신규 가입 시 /step 첫 단계에서 두 동의 모두 받고 timestamp 박는 흐름 도입.
--
-- 컬럼:
--   terms_agreed_at   DATETIME NULL  — 서비스 이용약관 동의 시점 (NULL = 미동의)
--   privacy_agreed_at DATETIME NULL  — 개인정보처리방침 동의 시점 (NULL = 미동의)
--
-- 위치: users.selected_tags 다음 (AFTER selected_tags) — created_at 앞.
--      운영 RDS 적용 시점 결정 (가을쥐 2026-05-14). 모델 클래스 컬럼 순서 정합.
--
-- 기존 사용자 정책:
--   - backfill X. 모든 기존 사용자 NULL 유지.
--   - 다음 로그인 시 OAuthCallbackPage 가드가 NULL 감지 → /step 강제 재진입.
--   - 사용자가 약관 동의 후 timestamp 박힘.
--   - → 일시적 사용자 불편 (재로그인 1회) 있지만 법적 의무 충족 우선.
--
-- idempotency:
--   - DRY RUN 1 결과로 컬럼 존재 여부 사전 확인.
--   - 컬럼 없음 → 실행. 컬럼 이미 있음 → 실행 금지 (ALTER 통째 skip).
--   - 재실행 보호는 PROCEDURE 옵션 §대안 참고 (DBeaver/CLI 모두 동작).
--
-- ⚠️ MySQL 의 `ADD COLUMN IF NOT EXISTS` 는 MariaDB 전용 문법. MySQL 8 에서는
--    1064 발생. 본 SQL 은 표준 ALTER 사용 → DRY RUN 으로 사전 점검 필수.
--
-- 본 파일은 가을쥐가 운영 RDS 에서 직접 실행. 적용 후 삭제 가능.
-- =============================================================================


-- =========================================
-- DRY RUN 1: 현재 users 테이블 컬럼 확인
-- =========================================
-- 기대 결과:
--   - 신규 적용 (정상) : 'deleted_at' 1 row 만 반환 (2 신규 컬럼은 0건).
--   - 이미 적용된 경우 : 3 row 모두 반환 → 아래 ALTER 블록 실행 금지 (재실행 X).
SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'users'
  AND COLUMN_NAME IN ('deleted_at', 'terms_agreed_at', 'privacy_agreed_at');


-- =========================================
-- DRY RUN 2: 기존 사용자 수 (모두 NULL 로 backfill 되는 영향 규모)
-- =========================================
SELECT
  COUNT(*) AS total_users,
  SUM(CASE WHEN deleted_at IS NULL     THEN 1 ELSE 0 END) AS active_users,
  SUM(CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END) AS soft_deleted_users
FROM users;
-- 기대: active_users 전원이 다음 로그인 시 /step 재진입 영향 받음.


-- =========================================
-- 마이그레이션 실행 (트랜잭션, 두 컬럼 한 번에 추가)
--
-- ⚠️ DRY RUN 1 결과로 두 컬럼 (terms_agreed_at / privacy_agreed_at) 모두
--    없음을 먼저 확인. 이미 하나라도 있으면 본 블록 실행 X.
--
-- MySQL/MariaDB 표준 문법 — 1064 위험 없음.
-- =========================================

START TRANSACTION;

ALTER TABLE `users`
  ADD COLUMN `terms_agreed_at`   DATETIME NULL
    COMMENT '서비스 이용약관 동의 시점 (KST). NULL = 미동의 → /step 재진입.'
    AFTER `selected_tags`,
  ADD COLUMN `privacy_agreed_at` DATETIME NULL
    COMMENT '개인정보처리방침 동의 시점 (KST). NULL = 미동의 → /step 재진입.'
    AFTER `terms_agreed_at`;

COMMIT;
-- 실패 시 ROLLBACK;
-- 재실행 시 1060 (Duplicate column name) 발생 가능 → 이미 적용된 상태이므로 OK.


-- =========================================
-- 검증 SELECT (COMMIT 이후 실행)
-- =========================================

-- 1. 두 컬럼이 정상 추가됐는지 확인 (2 row 반환 기대)
SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'users'
  AND COLUMN_NAME IN ('terms_agreed_at', 'privacy_agreed_at');

-- 2. 모든 row 가 NULL 인지 확인 (backfill 안 함 정책 정합)
SELECT
  COUNT(*) AS total,
  SUM(CASE WHEN terms_agreed_at   IS NULL THEN 1 ELSE 0 END) AS terms_null,
  SUM(CASE WHEN privacy_agreed_at IS NULL THEN 1 ELSE 0 END) AS privacy_null
FROM users;
-- 기대: total == terms_null == privacy_null

-- 3. 신규 가입 사용자가 동의 흐름을 정상 통과하면 두 컬럼이 NOT NULL 로 채워짐 — 운영 모니터링용
-- (배포 후 24시간 내 신규 가입 표본으로 확인)


-- =============================================================================
-- §대안: PROCEDURE 분기 (idempotent 보장 — 재실행 안전 필요할 때만)
--
-- DBeaver: "SQL Editor → Settings → SQL Processing → Statement Delimiter" 에서
--          `//` 추가 후 아래 블록 실행. 또는 CLI mysql 에서 그대로 실행 가능.
--
-- 위 표준 ALTER 가 1064 외 다른 사유로 부분 적용 후 중단된 케이스에 사용.
-- 정상 흐름 (위 트랜잭션 블록 한 번 실행) 에서는 본 블록 불필요.
-- =============================================================================
--
-- DELIMITER //
--
-- DROP PROCEDURE IF EXISTS add_terms_privacy_columns//
--
-- CREATE PROCEDURE add_terms_privacy_columns()
-- BEGIN
--   IF NOT EXISTS (
--     SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
--     WHERE TABLE_SCHEMA = DATABASE()
--       AND TABLE_NAME = 'users'
--       AND COLUMN_NAME = 'terms_agreed_at'
--   ) THEN
--     ALTER TABLE `users`
--       ADD COLUMN `terms_agreed_at` DATETIME NULL
--         COMMENT '서비스 이용약관 동의 시점 (KST). NULL = 미동의 → /step 재진입.'
--         AFTER `selected_tags`;
--   END IF;
--
--   IF NOT EXISTS (
--     SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
--     WHERE TABLE_SCHEMA = DATABASE()
--       AND TABLE_NAME = 'users'
--       AND COLUMN_NAME = 'privacy_agreed_at'
--   ) THEN
--     ALTER TABLE `users`
--       ADD COLUMN `privacy_agreed_at` DATETIME NULL
--         COMMENT '개인정보처리방침 동의 시점 (KST). NULL = 미동의 → /step 재진입.'
--         AFTER `terms_agreed_at`;
--   END IF;
-- END//
--
-- DELIMITER ;
--
-- CALL add_terms_privacy_columns();
-- DROP PROCEDURE add_terms_privacy_columns;
