import { api } from './apiClient'

export interface Breed {
  id: number
  name_ko: string
  name_en: string
  top10: boolean
  created_at: string
}

/** GET /breeds — 전체 목록 */
export function getAllBreeds(): Promise<Breed[]> {
  return api.get('/breeds')
}

/** GET /breeds?top10=true — 인기 TOP 10 */
export function getTop10Breeds(): Promise<Breed[]> {
  return api.get('/breeds?top10=true')
}

/** GET /breeds?search={term} — 한글 검색 */
export function searchBreeds(term: string): Promise<Breed[]> {
  return api.get(`/breeds?search=${encodeURIComponent(term)}`)
}

/** GET /breeds/{id} */
export function getBreed(id: number): Promise<Breed> {
  return api.get(`/breeds/${id}`)
}
