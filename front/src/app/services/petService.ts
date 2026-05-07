import { api } from './apiClient'

export interface Pet {
  id: number
  user_id: number
  breed_id: number
  name: string
  birth_date: string | null
  gender: 'MALE' | 'FEMALE' | null
  is_neutered: boolean | null
  type_id: number | null
  selected_tags: string[]
  image_url: string | null
  created_at: string
  updated_at: string
  age?: number
}

export interface PetCreateInput {
  breed_id: number
  name: string
  birth_date?: string
  gender?: 'MALE' | 'FEMALE'
  is_neutered?: boolean
  type_id?: number
  selected_tags?: string[]
  image_id?: number
}

export interface PetUpdateInput extends Partial<PetCreateInput> {}

/** POST /pets */
export function createPet(data: PetCreateInput): Promise<Pet> {
  return api.post('/pets', data)
}

/** GET /pets?user_id={id} */
export function getPets(userId: number): Promise<Pet[]> {
  return api.get(`/pets?user_id=${userId}`)
}

/** GET /pets/{id} */
export function getPet(id: number): Promise<Pet> {
  return api.get(`/pets/${id}`)
}

/** PATCH /pets/{id} */
export function updatePet(id: number, data: PetUpdateInput): Promise<Pet> {
  return api.patch(`/pets/${id}`, data)
}

/** DELETE /pets/{id} */
export function deletePet(id: number): Promise<void> {
  return api.delete(`/pets/${id}`)
}
