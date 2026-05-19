-- ============================================================
-- 반려견 AI 프로필 분석 결과 테이블
-- GPT-4o Vision 으로 반려견 사진을 분석한 구조화된 외형 JSON 저장.
-- 일기 그림 생성 시 english_prompt / must_include_keywords 활용.
-- ============================================================

CREATE TABLE IF NOT EXISTS `pet_profiles` (
  `id`           BIGINT       NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `pet_id`       BIGINT       NOT NULL COMMENT 'pets.id FK (1:1)',
  `image_id`     BIGINT       NULL     COMMENT 'images.id — 분석에 사용된 사진',
  `profile_json` JSON         NOT NULL COMMENT 'GPT-4o Vision 분석 결과 전체 JSON',
  `analyzed_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '분석 일시',
  `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_pet_profiles_pet_id` (`pet_id`),
  CONSTRAINT `fk_pet_profiles_pet`  FOREIGN KEY (`pet_id`)   REFERENCES `pets`(`id`)   ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT `fk_pet_profiles_img`  FOREIGN KEY (`image_id`) REFERENCES `images`(`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='반려견 AI 프로필 분석 결과';
