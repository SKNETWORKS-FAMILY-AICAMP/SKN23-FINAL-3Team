import { api } from './apiClient'

export interface PlaceResult {
  name: string
  address: string
  category: string
  sub_category: string
  content_id: string
  lat: number
  lng: number
  tel: string
  conditions: string
  pet_zone: string
  pet_size: string
  has_parking: string
  operation: string
  indoor: string
  outdoor: string
  description: string
  firstimage: string
  image?: string
  reason?: string
  similarity: number
  final_score: number
}

interface SearchPlacesResponse {
  places: PlaceResult[]
}

/** GET /places/search?query={q}&category={c}&city={c} */
export function searchPlaces(params: {
  query: string
  category?: string
  city?: string
  pet_id?: number | null
  user_lat?: number
  user_lng?: number
}): Promise<PlaceResult[]> {
  const qs = new URLSearchParams({ query: params.query })
  if (params.category) qs.set('category', params.category)
  if (params.city) qs.set('city', params.city)
  if (params.pet_id != null) qs.set('pet_id', String(params.pet_id))
  if (params.user_lat != null) qs.set('user_lat', String(params.user_lat))
  if (params.user_lng != null) qs.set('user_lng', String(params.user_lng))
  return api
    .get<SearchPlacesResponse>(`/places/search?${qs}`)
    .then((response) => response.places)
}
