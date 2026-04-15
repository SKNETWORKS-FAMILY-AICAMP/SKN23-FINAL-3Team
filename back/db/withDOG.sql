-- 데이터베이스 생성 (필요 시 주석 해제 후 사용)
-- CREATE DATABASE IF NOT EXISTS withdog
--     CHARACTER SET utf8mb4
--     COLLATE utf8mb4_unicode_ci;
-- USE withdog;

SET FOREIGN_KEY_CHECKS = 0;  -- 초기화 시 FK 순서 무관하게 DROP 허용

-- =============================================================
-- 기존 테이블 DROP (재실행 안전)
-- =============================================================
DROP TABLE IF EXISTS `chat_messages`;
DROP TABLE IF EXISTS `diaries`;
DROP TABLE IF EXISTS `chat_rooms`;
DROP TABLE IF EXISTS `pets`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `breeds`;
DROP TABLE IF EXISTS `keywords`;
DROP TABLE IF EXISTS `images`;

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================
-- 1. images (업로드한 이미지)
--    - 참조하는 테이블 없음 → 가장 먼저 생성
-- =============================================================
CREATE TABLE `images` (
    `id`          BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '이미지 ID',
    `file_url`    VARCHAR(500)    NOT NULL                 COMMENT 'AWS S3 파일 URL',
    `file_name`   VARCHAR(255)    NOT NULL                 COMMENT '원본 파일명',
    `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP  COMMENT '생성 일시',
    `deleted_at`  DATETIME        NULL                     COMMENT '삭제 일시',

    PRIMARY KEY (`id`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='이미지 파일 메타데이터 (S3 연동)';


-- =============================================================
-- 2. breeds (견종)
--    - 참조하는 테이블 없음 → 마스터 데이터
-- =============================================================
CREATE TABLE `breeds` (
    `id`          BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '견종 ID',
    `name_ko`     VARCHAR(100)    NOT NULL                 COMMENT '견종명 (한국어)',
    `name_en`     VARCHAR(100)    NOT NULL                 COMMENT '견종명 (영어)',
    `top10`       BOOLEAN         NOT NULL DEFAULT FALSE   COMMENT '인기 견종 TOP10 여부 (화면 노출)',
    `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP  COMMENT '등록 일시',

    PRIMARY KEY (`id`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='견종 마스터 데이터';


-- =============================================================
-- 3. keywords (키워드)
--    - 사용자/반려동물 성향 태그 마스터 데이터
-- =============================================================
CREATE TABLE `keywords` (
    `id`          BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '키워드 ID',
    `category`    VARCHAR(10)     NOT NULL                 COMMENT '분류 (예: USER, PET)',
    `name`        VARCHAR(50)     NOT NULL                 COMMENT '키워드명 (화면 노출용)',
    `description` TEXT            NULL                     COMMENT '키워드 설명',
    `created_at`  DATETIME        NULL DEFAULT CURRENT_TIMESTAMP  COMMENT '등록 일시',

    PRIMARY KEY (`id`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='키워드 마스터 데이터';


-- =============================================================
-- 4. users (사용자)
--    - images(profile_id), keywords(type_id) 참조
-- =============================================================
CREATE TABLE `users` (
    `id`           BIGINT              NOT NULL AUTO_INCREMENT  COMMENT '사용자 ID',
    `email`        VARCHAR(255)        NOT NULL                 COMMENT '이메일 주소',
    `nickname`     VARCHAR(50)         NOT NULL                 COMMENT '닉네임',
    `gender`       ENUM('MALE','FEMALE') NULL                   COMMENT '성별',
    `age`          TINYINT UNSIGNED    NULL                     COMMENT '나이',
    `profile_id`   BIGINT              NOT NULL                 COMMENT '프로필 이미지 ID',
    `provider`     VARCHAR(20)         NOT NULL                 COMMENT '소셜 로그인 제공자 (google/kakao/naver)',
    `provider_id`  VARCHAR(255)        NOT NULL                 COMMENT 'OAuth2.0 제공자 발급 고유 ID',
    `type_id`      BIGINT              NOT NULL                 COMMENT '대표 성향 키워드 ID',
    `selected_tags` JSON               NULL                     COMMENT '선택한 여행 성향 태그 목록',
    `created_at`   DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP          COMMENT '생성 일시',
    `updated_at`   DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  COMMENT '최종 수정 일시',
    `deleted_at`   DATETIME            NULL                     COMMENT '탈퇴 일시 (10일 후 하드딜리트)',

    PRIMARY KEY (`id`),

    -- 소셜 로그인 중복 가입 방지
    UNIQUE KEY `uq_users_provider` (`provider`, `provider_id`),

    -- FK
    CONSTRAINT `fk_users_profile_id`
        FOREIGN KEY (`profile_id`) REFERENCES `images` (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT `fk_users_type_id`
        FOREIGN KEY (`type_id`) REFERENCES `keywords` (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='소셜 로그인 사용자 계정';


-- =============================================================
-- 5. pets (반려동물)
--    - users(user_id), breed(breed_id), keywords(type_id) 참조
-- =============================================================
CREATE TABLE `pets` (
    `id`            BIGINT               NOT NULL AUTO_INCREMENT  COMMENT '반려동물 ID',
    `user_id`       BIGINT               NOT NULL                 COMMENT '사용자 ID',
    `breed_id`      BIGINT               NOT NULL                 COMMENT '견종 ID',
    `name`          VARCHAR(50)          NOT NULL                 COMMENT '반려동물 이름',
    `birth_date`    DATE                 NULL                     COMMENT '생년월일',
    `gender`        ENUM('MALE','FEMALE') NOT NULL                COMMENT '성별',
    `is_neutered`   BOOLEAN              NULL                     COMMENT '중성화 여부 (NULL=미입력)',
    `type_id`       BIGINT               NOT NULL                 COMMENT '대표 성격 키워드 ID',
    `selected_tags` JSON                 NULL                     COMMENT '선택한 성격 태그 목록',
    `created_at`    DATETIME             NOT NULL DEFAULT CURRENT_TIMESTAMP          COMMENT '등록 일시',
    `updated_at`    DATETIME             NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  COMMENT '수정 일시',
    `deleted_at`    DATETIME             NULL                     COMMENT '삭제 일시',

    PRIMARY KEY (`id`),

    -- FK
    CONSTRAINT `fk_pets_user_id`
        FOREIGN KEY (`user_id`)  REFERENCES `users`    (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT `fk_pets_breed_id`
        FOREIGN KEY (`breed_id`) REFERENCES `breeds`   (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT `fk_pets_type_id`
        FOREIGN KEY (`type_id`)  REFERENCES `keywords` (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='반려동물 기본 정보';


-- =============================================================
-- 6. chat_rooms (채팅방)
--    - users(user_id) 참조
-- =============================================================
CREATE TABLE `chat_rooms` (
    `id`          BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '채팅방 ID',
    `user_id`     BIGINT          NOT NULL                 COMMENT '사용자 ID',
    `title`       VARCHAR(200)    NULL                     COMMENT '채팅방 제목 (NULL 시 첫 메시지로 자동 생성)',
    `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP          COMMENT '생성 일시',
    `updated_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  COMMENT '마지막 메시지 발송 일시',
    `deleted_at`  DATETIME        NULL                     COMMENT '삭제 일시',

    PRIMARY KEY (`id`),

    -- FK
    CONSTRAINT `fk_chat_rooms_user_id`
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='AI 챗봇 대화 세션';


-- =============================================================
-- 7. chat_messages (채팅 메시지)
--    - chat_rooms(room_id) 참조
-- =============================================================
CREATE TABLE `chat_messages` (
    `id`          BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '메시지 ID',
    `room_id`     BIGINT          NOT NULL                 COMMENT '채팅방 ID',
    `role`        VARCHAR(10)     NOT NULL                 COMMENT '발신자 구분 (user | assistant | system)',
    `content`     TEXT            NOT NULL                 COMMENT '메시지 본문',
    `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP  COMMENT '발송 일시',

    PRIMARY KEY (`id`),

    -- FK
    CONSTRAINT `fk_chat_messages_room_id`
        FOREIGN KEY (`room_id`) REFERENCES `chat_rooms` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='채팅방 내 대화 메시지';


-- =============================================================
-- 8. diaries (다이어리)
--    - users(user_id), pets(pet_id), images(image_id) 참조
-- =============================================================
CREATE TABLE `diaries` (
    `id`          BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '일기 ID',
    `user_id`     BIGINT          NOT NULL                 COMMENT '사용자 ID',
    `pet_id`      BIGINT          NOT NULL                 COMMENT '반려동물 ID',
    `image_id`    BIGINT          NULL                     COMMENT 'AI 이미지 ID',
    `when_text`   VARCHAR(255)    NULL                     COMMENT '(6하원칙) 언제',
    `where_text`  VARCHAR(255)    NULL                     COMMENT '(6하원칙) 어디서',
    `who_text`    VARCHAR(255)    NULL                     COMMENT '(6하원칙) 누구와',
    `what_text`   TEXT            NULL                     COMMENT '(6하원칙) 무엇을',
    `how_text`    TEXT            NULL                     COMMENT '(6하원칙) 어떻게',
    `why_text`    TEXT            NULL                     COMMENT '(6하원칙) 왜',
    `title`       VARCHAR(200)    NULL                     COMMENT '제목 (AI 자동 생성 가능)',
    `content`     TEXT            NULL                     COMMENT '본문 (AI 자동 작성 가능)',
    `summary`     VARCHAR(300)    NULL                     COMMENT 'AI 생성 요약문',
    `emotion`     VARCHAR(10)     NULL                     COMMENT '감정 이모지',
    `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP          COMMENT '작성 일시',
    `updated_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  COMMENT '수정 일시',
    `deleted_at`  DATETIME        NULL                     COMMENT '삭제 일시',

    PRIMARY KEY (`id`),

    -- FK
    CONSTRAINT `fk_diaries_user_id`
        FOREIGN KEY (`user_id`)  REFERENCES `users`  (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT `fk_diaries_pet_id`
        FOREIGN KEY (`pet_id`)   REFERENCES `pets`   (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT `fk_diaries_image_id`
        FOREIGN KEY (`image_id`) REFERENCES `images` (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='반려동물 동반 기록 다이어리 (6하원칙 구조)';


-- =============================================================
-- 인덱스 (주요 조회 패턴 기반)
-- =============================================================

-- users: 이메일 조회, 소셜 로그인 조회
CREATE INDEX `idx_users_email`        ON `users`         (`email`);

-- pets: 사용자별 반려동물 목록
CREATE INDEX `idx_pets_user_id`       ON `pets`          (`user_id`);

-- chat_rooms: 사용자별 채팅방 목록 (최신순)
CREATE INDEX `idx_chat_rooms_user`    ON `chat_rooms`    (`user_id`, `updated_at` DESC);

-- chat_messages: 채팅방 내 메시지 시간순 (LLM 컨텍스트 조회)
CREATE INDEX `idx_chat_messages_room` ON `chat_messages` (`room_id`, `created_at` ASC);

-- diaries: 사용자별 다이어리 목록, 반려동물별 필터
CREATE INDEX `idx_diaries_user_id`    ON `diaries`       (`user_id`, `deleted_at`);
CREATE INDEX `idx_diaries_pet_id`     ON `diaries`       (`pet_id`);
