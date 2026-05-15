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
  type_name: string | null
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
  type_name: string | null
  selected_tags: string[]
  created_at: string
  updated_at: string
  age: number | null
  primary_pet_id: number | null
  primary_pet: PrimaryPet | null
  /** 서비스 이용약관 동의 시점. null = 미동의 → /step 재진입 필요. */
  terms_agreed_at: string | null
  /** 개인정보처리방침 동의 시점. null = 미동의 → /step 재진입 필요. */
  privacy_agreed_at: string | null
}

export interface UserUpdateInput {
  nickname?: string
  gender?: 'MALE' | 'FEMALE'
  birth_date?: string
  age?: number
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

/**
 * POST /users/me/agreements — 약관·개인정보처리방침 동의 처리.
 *
 * 둘 다 true 여야 백엔드 200. 하나라도 false 면 400 + "이용약관과 개인정보처리방침
 * 모두 동의해야 가입을 완료할 수 있습니다." 응답.
 *
 * 응답 = 갱신된 UserProfile (terms_agreed_at / privacy_agreed_at 채워진 상태).
 */
export function submitAgreements(body: {
  terms_agreed: boolean
  privacy_agreed: boolean
}): Promise<UserProfile> {
  return api.post('/users/me/agreements', body)
}
