-- =============================================================================
-- 2026-05-07: users.profile_id (잘못 박힌 반려견 사진) -> pets.image_id 마이그레이션
--
-- 사유: Step2Page 가 반려견 사진을 users.profile_id 로 박아왔던 흐름의 운영 데이터
--       정정 (외부팀 QA #67 후속). 직전 라운드에서 코드 흐름은 정정 완료
--       (보호자 사진 = users.profile_id / 반려견 사진 = pets.image_id) 했고,
--       본 SQL 은 이미 박혀있는 운영 데이터를 정책에 맞게 옮긴다.
--
-- 매핑 정책 (가을쥐 결정 2026-05-07):
--   1. 사용자별 가장 최근 활성 pet (MAX(pet.id), deleted_at IS NULL) 의 image_id 로 옮김
--   2. 단, 해당 pet 의 image_id 가 이미 박혀있으면 덮어쓰지 않음 (정상 업로드 보호)
--   3. 반려견 0마리 사용자 = 매핑 대상 없음, users.profile_id NULL 만 적용
--   4. 마이그레이션 후 모든 users.profile_id 를 NULL 로 일괄 unset (cleanup all)
--
-- MySQL 8 호환성: 동일 테이블 셀프 참조 UPDATE 는 ERROR 1093 위험. 임시 테이블 패턴
--                으로 매핑을 미리 계산해 회피한다 (derived table 회피 옵티마이저
--                merge 룰 회피 목적).
--
-- 본 파일은 가을쥐가 운영 RDS 에서 직접 실행하며, 적용 후 삭제 가능 (직전 라운드 패턴).
-- =============================================================================


-- =========================================
-- DRY RUN 1: 영향 받는 사용자 수
-- =========================================
SELECT COUNT(*) AS users_with_profile_id
FROM users
WHERE profile_id IS NOT NULL;


-- =========================================
-- DRY RUN 2: 매핑 미리보기 (옵션 c 기준)
-- 각 사용자별 옮길 image_id, 대상 pet, 분기 액션 표시.
-- =========================================
SELECT
  u.id AS user_id,
  u.profile_id AS image_to_move,
  latest.id AS target_pet_id,
  latest.image_id AS existing_pet_image_id,
  CASE
    WHEN latest.id IS NULL THEN 'no_active_pet -- skip mapping, NULL only'
    WHEN latest.image_id IS NOT NULL THEN 'pet already has image -- skip mapping (protect normal upload)'
    ELSE 'will migrate'
  END AS action
FROM users u
LEFT JOIN (
  SELECT p.user_id, p.id, p.image_id
  FROM pets p
  WHERE p.deleted_at IS NULL
    AND p.id = (
      SELECT MAX(p2.id)
      FROM pets p2
      WHERE p2.user_id = p.user_id AND p2.deleted_at IS NULL
    )
) latest ON latest.user_id = u.id
WHERE u.profile_id IS NOT NULL;


-- =========================================
-- 마이그레이션 실행 (영구 테이블 + 트랜잭션 분리 패턴)
--
-- 이전 임시 테이블 패턴은 일부 클라이언트 (DBeaver / Workbench script-mode 등) 에서
-- 각 statement 를 별도 connection 으로 실행하면 임시 테이블이 안 보여 ERROR 1146
-- (Unknown table) 발생. 영구 테이블로 변경해 connection 분리 무관하게 동작.
--
-- DDL (CREATE/DROP TABLE) 은 implicit commit 발생 → 트랜잭션 일관성 위해 UPDATE 만
-- 트랜잭션으로 감싼다 (Step 2). Step 1·3 은 트랜잭션 외부.
-- =========================================

-- ── Step 1: 매핑 영구 테이블 신설 + 데이터 채움 (트랜잭션 외부, DDL) ──────────
DROP TABLE IF EXISTS _migrate_user_to_pet;
CREATE TABLE _migrate_user_to_pet (
  user_id        BIGINT NOT NULL,
  image_to_move  BIGINT NOT NULL,
  latest_pet_id  BIGINT NULL,
  PRIMARY KEY (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO _migrate_user_to_pet (user_id, image_to_move, latest_pet_id)
SELECT
  u.id,
  u.profile_id,
  (
    SELECT MAX(p.id)
    FROM pets p
    WHERE p.user_id = u.id AND p.deleted_at IS NULL
  )
FROM users u
WHERE u.profile_id IS NOT NULL;


-- ── Step 2: UPDATE 들을 트랜잭션으로 보호 ──────────────────────────────────────
START TRANSACTION;

-- UPDATE 1: pets.image_id 채우기
-- - 영구 테이블의 latest_pet_id 와 일치하는 pet 만 갱신
-- - 정상 업로드 보호: pets.image_id IS NULL 만 갱신 (이미 박힌 pet 사진 미덮어씀)
-- - 반려견 0마리 사용자는 latest_pet_id IS NULL -> JOIN 매치 X 자동 skip
UPDATE pets p
JOIN _migrate_user_to_pet m ON m.latest_pet_id = p.id
SET p.image_id = m.image_to_move
WHERE p.image_id IS NULL
  AND p.deleted_at IS NULL;

-- UPDATE 2: users.profile_id 일괄 NULL (cleanup all)
UPDATE users
SET profile_id = NULL
WHERE profile_id IS NOT NULL;

COMMIT;
-- 실패 시: ROLLBACK; 후 _migrate_user_to_pet 테이블 그대로 남음 → Step 3 실행하거나
--         재시도. UPDATE 들이 idempotent 라 Step 2 만 다시 실행 가능.


-- ── Step 3: 매핑 테이블 정리 (트랜잭션 외부, DDL) ──────────────────────────────
DROP TABLE IF EXISTS _migrate_user_to_pet;


-- =========================================
-- 검증 SELECT (COMMIT 이후 실행)
-- =========================================

-- 1. users.profile_id 모두 NULL 확인
SELECT COUNT(*) AS remaining_users_with_profile_id
FROM users
WHERE profile_id IS NOT NULL;
-- 기대: 0

-- 2. 활성 pet 중 image_id 박힌 수
SELECT COUNT(*) AS pets_with_image
FROM pets
WHERE image_id IS NOT NULL AND deleted_at IS NULL;

-- 3. FK 무결성 — pets.image_id 가 가리키는 image 가 모두 존재 (FK 정의로 자동 보호되지만 명시 검증)
SELECT p.id AS pet_id, p.image_id
FROM pets p
LEFT JOIN images i ON i.id = p.image_id
WHERE p.image_id IS NOT NULL AND i.id IS NULL;
-- 기대: 0 행 (FK 위반 없음)

-- 4. 활성 pet 이 soft-deleted image 를 가리키지 않는지
SELECT p.id AS pet_id, p.image_id, i.deleted_at AS image_deleted_at
FROM pets p
JOIN images i ON i.id = p.image_id
WHERE p.image_id IS NOT NULL
  AND p.deleted_at IS NULL
  AND i.deleted_at IS NOT NULL;
-- 기대: 0 행 (활성 pet 이 soft-deleted image 미참조)
