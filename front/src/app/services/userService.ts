import { api } from './apiClient'

export interface PrimaryPet {
  id: number
  user_id: number
  breed_id: number
  name: string
  birth_date: string | null
  gender: 'MALE' | 'FEMALE' | null
  is_neutered: boolean | null
  type_id: number | null
  selected_tags: string[]
  age: number | null
}

export interface UserProfile {
  id: number
  email: string
  nickname: string
  gender: 'MALE' | 'FEMALE' | null
  birth_date: string | null
  profile_id: number | null
  profile_image_url: string | null
  provider: string
  type_id: number | null
  selected_tags: string[]
  created_at: string
  updated_at: string
  age: number | null
  primary_pet_id: number | null
  primary_pet: PrimaryPet | null
}

export interface UserUpdateInput {
  nickname?: string
  gender?: 'MALE' | 'FEMALE'
  birth_date?: string
  age?: number
  type_id?: number
  selected_tags?: string[]
  profile_id?: number
  primary_pet_id?: number
}

/** GET /users/me */
export function getMe(): Promise<UserProfile> {
  return api.get('/users/me')
}

/** GET /users/{id} */
export function getUser(id: number): Promise<UserProfile> {
  return api.get(`/users/${id}`)
}

/** PATCH /users/{id} */
export function updateUser(id: number, data: UserUpdateInput): Promise<UserProfile> {
  return api.patch(`/users/${id}`, data)
}

/** DELETE /users/{id} */
export function deleteUser(id: number): Promise<void> {
  return api.delete(`/users/${id}`)
}
