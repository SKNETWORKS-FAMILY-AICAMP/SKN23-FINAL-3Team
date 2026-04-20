import { api } from './apiClient'

export interface Place {
  id?: number
  name: string
  address?: string
  category?: string
  city?: string
  lat?: number
  lng?: number
  [key: string]: unknown
}

/** GET /places/search?query={q}&category={c}&city={c} */
export function searchPlaces(params: {
  query: string
  category?: string
  city?: string
}): Promise<Place[]> {
  const qs = new URLSearchParams({ query: params.query })
  if (params.category) qs.set('category', params.category)
  if (params.city) qs.set('city', params.city)
  return api.get(`/places/search?${qs}`)
}
