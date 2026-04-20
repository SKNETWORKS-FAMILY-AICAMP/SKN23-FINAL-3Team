import { api } from './apiClient'

export interface ImageRecord {
  id: number
  url: string
  created_at: string
}

/** POST /images — multipart/form-data */
export function uploadImage(file: File): Promise<ImageRecord> {
  return api.upload('/images', file)
}

/** GET /images/{id} */
export function getImage(id: number): Promise<ImageRecord> {
  return api.get(`/images/${id}`)
}

/** DELETE /images/{id} */
export function deleteImage(id: number): Promise<void> {
  return api.delete(`/images/${id}`)
}
