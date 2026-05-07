// front/src/app/utils/validation.ts
//
// 입력 검증 공통 함수 — 가을쥐 정책 (#62·#63 마이페이지 입력 검증, 2026-05-07 결정) 권위.
//
// 패턴: 각 함수는 trim 후 검증, 통과 시 null, 실패 시 한국어 메시지 string 을 반환.
// 폼 컴포넌트는 useState + onBlur 로 호출 → 메시지를 setError 로 표시.
//
// 욕설 검사는 백엔드 service 레이어에서 처리 — 프론트는 길이/날짜만 1차 검증, 백엔드 400 응답을
// catch 해서 "부적절한 단어가 포함되어 있습니다" 메시지를 사용자에게 그대로 표시.
//
// 도배(연속 동일 문자) 차단 미적용.

const NICKNAME_MAX = 20;
const PET_NAME_MAX = 20;
const CHAT_ROOM_TITLE_MAX = 50;
const DIARY_TITLE_MAX = 50;
const DIARY_6W_MAX = 100;
const USER_MIN_AGE_YEARS = 14; // 개인정보보호법 만 14세 이상
const PET_MAX_AGE_YEARS = 30;
const USER_MIN_BIRTH_YEAR = 1900;

/** 만 N년 전 날짜 (윤년 2/29 폴백 포함). */
function _yearsAgo(years: number): Date {
  const today = new Date();
  const target = new Date(today);
  try {
    target.setFullYear(today.getFullYear() - years);
  } catch {
    target.setFullYear(today.getFullYear() - years, today.getMonth(), 28);
  }
  // 2/29 → 2/28 자동 보정 (Date.setFullYear 가 자동 처리하지만 일부 브라우저 차이 보정)
  return target;
}

export function validateNickname(value: string): string | null {
  const trimmed = value.trim();
  if (trimmed.length === 0) return "닉네임을(를) 입력해주세요";
  if (trimmed.length > NICKNAME_MAX) return `닉네임은(는) ${NICKNAME_MAX}자 이하로 입력해주세요`;
  return null;
}

export function validatePetName(value: string): string | null {
  const trimmed = value.trim();
  if (trimmed.length === 0) return "반려견 이름을(를) 입력해주세요";
  if (trimmed.length > PET_NAME_MAX) return `반려견 이름은(는) ${PET_NAME_MAX}자 이하로 입력해주세요`;
  return null;
}

/** 채팅방 제목 수정 (1~50). 생성 시 NULL 허용은 서비스에서 처리. */
export function validateChatRoomTitle(value: string): string | null {
  const trimmed = value.trim();
  if (trimmed.length === 0) return "채팅방 제목을(를) 입력해주세요";
  if (trimmed.length > CHAT_ROOM_TITLE_MAX)
    return `채팅방 제목은(는) ${CHAT_ROOM_TITLE_MAX}자 이하로 입력해주세요`;
  return null;
}

/** 다이어리 제목 (1~50). 미입력 시 AI 자동 생성이라 빈 입력 자체는 폼 단에서 허용. */
export function validateDiaryTitle(value: string): string | null {
  const trimmed = value.trim();
  if (trimmed.length === 0) return null; // optional — 빈 OK
  if (trimmed.length > DIARY_TITLE_MAX)
    return `다이어리 제목은(는) ${DIARY_TITLE_MAX}자 이하로 입력해주세요`;
  return null;
}

/** 다이어리 6하원칙 슬롯 (0~100, 빈 입력 OK). */
export function validateDiary6W(value: string): string | null {
  const trimmed = value.trim();
  if (trimmed.length > DIARY_6W_MAX) return `${DIARY_6W_MAX}자 이하로 입력해주세요`;
  return null;
}

/** 사용자 생년월일 (1900-01-01 ~ 오늘 - 14년). 빈 입력은 optional 로 통과. */
export function validateUserBirth(value: string): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (isNaN(date.getTime())) return "올바른 날짜 형식이 아닙니다";
  const min = new Date(`${USER_MIN_BIRTH_YEAR}-01-01`);
  const max = _yearsAgo(USER_MIN_AGE_YEARS);
  if (date < min) return `생년월일은 ${USER_MIN_BIRTH_YEAR}년 이후로 입력해주세요`;
  if (date > max) return `만 ${USER_MIN_AGE_YEARS}세 이상만 가입 가능합니다`;
  return null;
}

/** 반려견 생년월일 (오늘 - 30년 ~ 오늘). 빈 입력은 optional 로 통과. */
export function validatePetBirth(value: string): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (isNaN(date.getTime())) return "올바른 날짜 형식이 아닙니다";
  const min = _yearsAgo(PET_MAX_AGE_YEARS);
  const today = new Date();
  today.setHours(23, 59, 59, 999);
  if (date < min) return `반려견 생년월일은 ${PET_MAX_AGE_YEARS}년 이내로 입력해주세요`;
  if (date > today) return "반려견 생년월일은 오늘 이전이어야 합니다";
  return null;
}

/** 이미지 5MB 사전 검증 (정책 #72-A). null 이면 통과, 메시지 있으면 거부. */
const MAX_IMAGE_BYTES = 5 * 1024 * 1024;

export function validateImageSize(file: File): string | null {
  if (file.size > MAX_IMAGE_BYTES) {
    return "5MB 이하 이미지만 업로드 가능합니다";
  }
  return null;
}

/** 날짜 input 의 max attribute 용 — 사용자 만 14세 미만 차단. ISO yyyy-mm-dd. */
export function userBirthMaxAttr(): string {
  return _yearsAgo(USER_MIN_AGE_YEARS).toISOString().slice(0, 10);
}

/** 날짜 input 의 min attribute 용 — 반려견 30년 이상 차단. ISO yyyy-mm-dd. */
export function petBirthMinAttr(): string {
  return _yearsAgo(PET_MAX_AGE_YEARS).toISOString().slice(0, 10);
}
