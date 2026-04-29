import { api } from './apiClient'

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

/** POST /images — multipart/form-data */
export function uploadImage(file: File): Promise<ImageRecord> {
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
