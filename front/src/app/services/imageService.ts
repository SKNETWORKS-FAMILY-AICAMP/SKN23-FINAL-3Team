import { api } from './apiClient'
import { validateImageSize } from '../utils/validation'

export interface ImageRecord {
  id: number
  url: string       // file_url 을 url 로 매핑한 값
  file_url: string  // 백엔드 원본 필드
  created_at: string
}

// 백엔드 응답 (file_url 사용)
interface _ImageApiResponse {
  id: number
  file_url: string
  file_name: string
  created_at: string
}

function _mapImage(r: _ImageApiResponse): ImageRecord {
  return { id: r.id, url: r.file_url, file_url: r.file_url, created_at: r.created_at }
}

/** POST /images — multipart/form-data.
 *
 * 정책 #72-A: 5MB 사전 검증 — Nginx client_max_body_size(20M)·백엔드 매직바이트보다 먼저 차단
 * 하여 UX 향상 (큰 파일 업로드 지연·실패 방지). 실패 시 throw 하여 호출처가 catch 후 사용자에게
 * 에러 메시지 표시.
 */
export function uploadImage(file: File): Promise<ImageRecord> {
  const sizeError = validateImageSize(file)
  if (sizeError) {
    return Promise.reject(new Error(sizeError))
  }
  return api.upload<_ImageApiResponse>('/images', file).then(_mapImage)
}

/** GET /images/{id} */
export function getImage(id: number): Promise<ImageRecord> {
  return api.get<_ImageApiResponse>(`/images/${id}`).then(_mapImage)
}

/** DELETE /images/{id} */
export function deleteImage(id: number): Promise<void> {
  return api.delete(`/images/${id}`)
}
