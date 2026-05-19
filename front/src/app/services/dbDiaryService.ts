/**
 * DB 저장/조회용 다이어리 서비스 (백엔드 /diaries)
 * AI 생성용(diaryService.ts의 generateDiary)과 분리
 */
import { api } from './apiClient'

export interface DiaryRecord {
  id: number
  pet_id: number
  user_id: number
  image_id: number | null
  when_text: string | null
  where_text: string | null
  who_text: string | null
  what_text: string | null
  how_text: string | null
  why_text: string | null
  title: string | null
  content: string | null
  summary: string | null
  emotion: string | null
  is_favorite?: boolean
  created_at: string
  updated_at: string
}

export interface CalendarItem {
  date: string
  diary_id: number
  emotion: string
}

export interface CalendarResponse {
  year: number
  month: number
  items: CalendarItem[]
}

export interface DiaryCreateInput {
  pet_id: number
  when_text?: string
  where_text?: string
  who_text?: string
  what_text?: string
  how_text?: string
  why_text?: string
  title?: string
  content?: string
  summary?: string
  emotion?: string
  image_id?: number
}

export interface DiaryUpdateInput {
  title?: string
  content?: string
  summary?: string
  emotion?: string
  image_id?: number
}

/** POST /diaries */
export function createDiary(data: DiaryCreateInput): Promise<DiaryRecord> {
  return api.post('/diaries', data)
}

/** PATCH /diaries/{id} */
export function updateDiary(id: number, data: DiaryUpdateInput): Promise<DiaryRecord> {
  return api.patch(`/diaries/${id}`, data)
}

/** GET /diaries?user_id={id} */
export function getDiariesByUser(userId: number): Promise<DiaryRecord[]> {
  return api.get(`/diaries?user_id=${userId}`)
}

/** GET /diaries?user_id={id}&pet_id={id} */
export function getDiariesByPet(userId: number, petId: number): Promise<DiaryRecord[]> {
  return api.get(`/diaries?user_id=${userId}&pet_id=${petId}`)
}

/** GET /diaries/{id} */
export function getDiary(id: number): Promise<DiaryRecord> {
  return api.get(`/diaries/${id}`)
}

/** DELETE /diaries/{id} */
export function deleteDiary(id: number): Promise<void> {
  return api.delete(`/diaries/${id}`)
}

/** PATCH /diaries/{id}/favorite — 즐겨찾기 토글 */
export function toggleFavorite(id: number): Promise<DiaryRecord> {
  return api.patch(`/diaries/${id}/favorite`, {})
}

/** GET /diaries/calendar?year=&month= */
export function getDiaryCalendar(year: number, month: number): Promise<CalendarResponse> {
  return api.get(`/diaries/calendar?year=${year}&month=${month}`)
}
