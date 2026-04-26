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
}): Promise<PlaceResult[]> {
  const qs = new URLSearchParams({ query: params.query })
  if (params.category) qs.set('category', params.category)
  if (params.city) qs.set('city', params.city)
  return api
    .get<SearchPlacesResponse>(`/places/search?${qs}`)
    .then((response) => response.places)
}
