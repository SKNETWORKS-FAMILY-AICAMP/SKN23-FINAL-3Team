import { api } from './apiClient'

export interface Keyword {
  id: number
  category: 'PET' | 'USER'
  name: string
  description: string | null
}

/** GET /keywords?category=PET */
export function getPetKeywords(): Promise<Keyword[]> {
  return api.get('/keywords?category=PET')
}

/** GET /keywords?category=USER */
export function getUserKeywords(): Promise<Keyword[]> {
  return api.get('/keywords?category=USER')
}
