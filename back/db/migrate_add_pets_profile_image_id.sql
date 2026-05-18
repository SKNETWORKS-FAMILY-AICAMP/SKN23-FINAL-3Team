-- Migration: pets 테이블 image_id 컬럼 정리
-- 생성일: 2026-05-07 (수정: 2026-05-12)
-- 설명: 반려견 프로필 사진 저장을 위한 images 테이블 FK 컬럼
--
-- ※ image_id 컬럼이 이미 존재하면 이 마이그레이션은 실행 불필요.
--   아래 SQL 은 이전에 profile_image_id 로 잘못 추가된 경우를 정리합니다.

-- 1) profile_image_id 컬럼이 남아 있으면 제거 (이전 마이그레이션 잔재)
--    실행 전 SHOW COLUMNS FROM pets LIKE 'profile_image_id'; 로 확인 후 필요시만 실행
-- ALTER TABLE `pets` DROP COLUMN `profile_image_id`;

-- 2) image_id 가 아직 없는 경우에만 추가 (이미 있으면 SKIP)
-- ALTER TABLE `pets`
--   ADD COLUMN `image_id` BIGINT NULL COMMENT '프로필 이미지 ID (images.id FK)' AFTER `selected_tags`,
--   ADD CONSTRAINT `fk_pets_image_id`
--     FOREIGN KEY (`image_id`) REFERENCES `images` (`id`)
--     ON UPDATE CASCADE ON DELETE SET NULL;

-- ┌──────────────────────────────────────────────────────────────────┐
-- │  현재 상태 확인용 (DBeaver 에서 실행)                            │
-- │  SHOW COLUMNS FROM pets LIKE '%image%';                         │
-- │  SHOW CREATE TABLE pets;                                        │
-- └──────────────────────────────────────────────────────────────────┘
