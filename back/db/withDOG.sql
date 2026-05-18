-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: withdog
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '';

--
-- Table structure for table `breeds`
--

DROP TABLE IF EXISTS `breeds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `breeds` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '견종 ID',
  `name_ko` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '견종명 (한국어)',
  `name_en` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '견종명 (영어)',
  `top10` tinyint(1) NOT NULL DEFAULT '0' COMMENT '인기 견종 TOP10 여부 (화면 노출)',
  `size` enum('small','medium','large') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '견종 크기 분류 (소형:<10kg, 중형:10~25kg, 대형:>25kg)',
  `activity_level` enum('low','medium','high') COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '활동량 수준 (추천 점수 계산 활용)',
  `temperament` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '성격 태그 문자열 (쉼표 구분, 영문 원본)',
  `breed_group` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '견종 그룹 (Toy/Sporting/Herding/Hound 등)',
  `image_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '견종 대표 이미지 URL (Dog CEO API 캐싱)',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '등록 일시',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=171 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='견종 마스터 데이터';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `chat_messages`
--

DROP TABLE IF EXISTS `chat_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chat_messages` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '메시지 ID',
  `room_id` bigint NOT NULL COMMENT '채팅방 ID',
  `role` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '발신자 구분 (user | assistant | system)',
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '메시지 본문',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '발송 일시',
  PRIMARY KEY (`id`),
  KEY `idx_chat_messages_room` (`room_id`,`created_at`),
  CONSTRAINT `fk_chat_messages_room_id` FOREIGN KEY (`room_id`) REFERENCES `chat_rooms` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='채팅방 내 대화 메시지';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `chat_rooms`
--

DROP TABLE IF EXISTS `chat_rooms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chat_rooms` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '채팅방 ID',
  `user_id` bigint NOT NULL COMMENT '사용자 ID',
  `title` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '채팅방 제목 (NULL 시 첫 메시지로 자동 생성)',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 일시',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '마지막 메시지 발송 일시',
  `deleted_at` datetime DEFAULT NULL COMMENT '삭제 일시',
  PRIMARY KEY (`id`),
  KEY `idx_chat_rooms_user` (`user_id`,`updated_at` DESC),
  CONSTRAINT `fk_chat_rooms_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI 챗봇 대화 세션';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `diaries`
--

DROP TABLE IF EXISTS `diaries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `diaries` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '일기 ID',
  `user_id` bigint NOT NULL COMMENT '사용자 ID',
  `pet_id` bigint NOT NULL COMMENT '반려동물 ID',
  `image_id` bigint DEFAULT NULL,
  `when_text` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '(6하원칙) 언제',
  `where_text` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '(6하원칙) 어디서',
  `who_text` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '(6하원칙) 누구와',
  `what_text` text COLLATE utf8mb4_unicode_ci COMMENT '(6하원칙) 무엇을',
  `how_text` text COLLATE utf8mb4_unicode_ci COMMENT '(6하원칙) 어떻게',
  `why_text` text COLLATE utf8mb4_unicode_ci COMMENT '(6하원칙) 왜',
  `title` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '제목 (AI 자동 생성 가능)',
  `content` text COLLATE utf8mb4_unicode_ci COMMENT '본문 (AI 자동 작성 가능)',
  `summary` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'AI 생성 요약문',
  `emotion` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '감정 이모지',
  `diary_date` date NOT NULL COMMENT '일기 날짜 YYYY-MM-DD (현재 KST 자동 입력, 추후 사용자 선택 가능)',
  `is_favorite` tinyint(1) NOT NULL DEFAULT '0' COMMENT '즐겨찾기 여부 (0/1). 하루 1개 제약은 application-level SWAP.',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '작성 일시',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 일시',
  `deleted_at` datetime DEFAULT NULL COMMENT '삭제 일시',
  PRIMARY KEY (`id`),
  KEY `fk_diaries_image_id` (`image_id`),
  KEY `idx_diaries_user_id` (`user_id`,`deleted_at`),
  KEY `idx_diaries_pet_id` (`pet_id`),
  KEY `idx_diaries_user_date` (`user_id`,`diary_date`,`deleted_at`),
  KEY `idx_diaries_user_favorite` (`user_id`,`is_favorite`,`deleted_at`),
  CONSTRAINT `fk_diaries_image_id` FOREIGN KEY (`image_id`) REFERENCES `images` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_diaries_pet_id` FOREIGN KEY (`pet_id`) REFERENCES `pets` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_diaries_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='반려동물 동반 기록 다이어리 (6하원칙 구조)';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `favorite_places`
--

DROP TABLE IF EXISTS `favorite_places`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `favorite_places` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `place_id` bigint NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_favorite_places_user_place` (`user_id`,`place_id`),
  KEY `idx_favorite_places_user` (`user_id`,`created_at`),
  CONSTRAINT `fk_favorite_places_place` FOREIGN KEY (`place_id`) REFERENCES `places` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_favorite_places_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='사용자별 즐겨찾기 장소 (N:M)';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `images`
--

DROP TABLE IF EXISTS `images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `images` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '이미지 ID',
  `file_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'AWS S3 파일 URL',
  `file_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '원본 파일명',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 일시',
  `deleted_at` datetime DEFAULT NULL COMMENT '삭제 일시',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='이미지 파일 메타데이터 (S3 연동)';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `keywords`
--

DROP TABLE IF EXISTS `keywords`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `keywords` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '키워드 ID',
  `category` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '분류 (예: USER, PET)',
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '키워드명 (화면 노출용)',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '키워드 설명',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '등록 일시',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='키워드 마스터 데이터';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pets`
--

DROP TABLE IF EXISTS `pets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pets` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '반려동물 ID',
  `user_id` bigint NOT NULL COMMENT '사용자 ID',
  `breed_id` bigint NOT NULL COMMENT '견종 ID',
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '반려동물 이름',
  `birth_date` date DEFAULT NULL COMMENT '생년월일',
  `gender` enum('MALE','FEMALE') COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '성별',
  `is_neutered` tinyint(1) DEFAULT NULL COMMENT '중성화 여부 (NULL=미입력)',
  `type_id` bigint NOT NULL COMMENT '대표 성격 키워드 ID',
  `selected_tags` json DEFAULT NULL COMMENT '선택한 성격 태그 목록',
  `image_id` bigint DEFAULT NULL COMMENT '프로필 이미지 ID (images.id FK)',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '등록 일시',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 일시',
  `deleted_at` datetime DEFAULT NULL COMMENT '삭제 일시',
  PRIMARY KEY (`id`),
  KEY `fk_pets_breed_id` (`breed_id`),
  KEY `fk_pets_type_id` (`type_id`),
  KEY `idx_pets_user_id` (`user_id`),
  KEY `idx_pets_image_id` (`image_id`),
  CONSTRAINT `fk_pets_breed_id` FOREIGN KEY (`breed_id`) REFERENCES `breeds` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_pets_image_id` FOREIGN KEY (`image_id`) REFERENCES `images` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_pets_type_id` FOREIGN KEY (`type_id`) REFERENCES `keywords` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_pets_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='반려동물 기본 정보';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `places`
--

DROP TABLE IF EXISTS `places`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `places` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '장소 PK',
  `content_id` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '한국관광공사 콘텐츠 ID (UNIQUE KEY)',
  `content_type_id` varchar(5) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '관광타입 코드 (12:관광지 14:문화시설 28:레포츠 32:숙박 38:쇼핑 39:음식점)',
  `sub_category` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '원본 세부 카테고리 (카페/박물관/동물병원 등)',
  `name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '장소명',
  `address` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '주소',
  `tel` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '전화번호',
  `latitude` decimal(10,7) DEFAULT NULL COMMENT '위도 (GPS Y좌표 / WGS84)',
  `longitude` decimal(10,7) DEFAULT NULL COMMENT '경도 (GPS X좌표 / WGS84)',
  `firstimage` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '대표 이미지 원본 URL (약 500x333, 상세 화면용)',
  `firstimage2` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '대표 이미지 썸네일 URL (약 150x100, 목록 화면용)',
  `is_indoor` tinyint(1) DEFAULT NULL COMMENT '실내 여부 (NULL=미확인)',
  `is_outdoor` tinyint(1) DEFAULT NULL COMMENT '실외 여부 (NULL=미확인)',
  `pet_zone_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '반려동물 동반 가능 구역 유형 (실내구역/실외구역/전구역)',
  `pet_size_limit` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '입장 가능 반려동물 크기/종류 (예: 모두 가능, 소형견, 10kg 미만)',
  `pet_restrictions` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '반려동물 동반 시 제한사항 (예: 목줄 착용, 배변봉투)',
  `has_parking` enum('Y','N') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '주차 가능 여부 (Y/N)',
  `operation_info` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '운영시간 및 휴무일 정보',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '장소 통합 설명 텍스트 (VectorDB ChromaDB 임베딩 소스)',
  `modified_time` datetime DEFAULT NULL COMMENT '한국관광공사 원본 데이터 최종 수정일',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '수집 등록 일시',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수집 갱신 일시',
  `entrance_fee_amount` int DEFAULT NULL COMMENT '입장료(원). NULL=불명/변동/조건부',
  `entrance_fee_type` enum('free','fixed','variable','conditional','unknown') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'unknown' COMMENT '입장료 타입',
  `extra_fee_amount` int DEFAULT NULL COMMENT '강아지 추가요금(원).',
  `extra_fee_type` enum('free','fixed','variable','conditional','unknown') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'unknown' COMMENT '추가요금 타입',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_places_content_id` (`content_id`),
  KEY `idx_places_type` (`content_type_id`),
  KEY `idx_places_location` (`latitude`,`longitude`),
  KEY `idx_places_parking` (`has_parking`),
  KEY `idx_places_sub_category` (`sub_category`),
  KEY `idx_places_indoor_outdoor` (`is_indoor`,`is_outdoor`),
  KEY `idx_places_fee_type` (`entrance_fee_type`),
  KEY `idx_places_extra_fee_type` (`extra_fee_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='반려견 동반 가능 장소';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '사용자 ID',
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '이메일 주소',
  `nickname` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '닉네임',
  `gender` enum('MALE','FEMALE') COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '성별',
  `birth_date` date DEFAULT NULL COMMENT '생년월일',
  `profile_id` bigint DEFAULT NULL COMMENT '프로필 이미지 ID',
  `provider` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '소셜 로그인 제공자 (google/kakao/naver)',
  `provider_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'OAuth2.0 제공자 발급 고유 ID',
  `type_id` bigint DEFAULT NULL COMMENT '대표 성향 키워드 ID',
  `primary_pet_id` bigint DEFAULT NULL COMMENT '대표 반려견 ID (마이페이지 카드·기본 컨텍스트용)',
  `selected_tags` json DEFAULT NULL COMMENT '선택한 여행 성향 태그 목록',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 일시',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '최종 수정 일시',
  `deleted_at` datetime DEFAULT NULL COMMENT '탈퇴 일시 (10일 후 하드딜리트)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_provider` (`provider`,`provider_id`),
  KEY `fk_users_profile_id` (`profile_id`),
  KEY `fk_users_type_id` (`type_id`),
  KEY `fk_users_primary_pet` (`primary_pet_id`),
  KEY `idx_users_email` (`email`),
  CONSTRAINT `fk_users_profile_id` FOREIGN KEY (`profile_id`) REFERENCES `images` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_users_type_id` FOREIGN KEY (`type_id`) REFERENCES `keywords` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_users_primary_pet` FOREIGN KEY (`primary_pet_id`) REFERENCES `pets` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='소셜 로그인 사용자 계정';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'withdog'
--
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-16 12:38:43
