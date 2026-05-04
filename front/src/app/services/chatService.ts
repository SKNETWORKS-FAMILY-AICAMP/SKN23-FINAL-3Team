import { api } from './apiClient'
import type { PlaceResult } from './placeService'

export interface ChatRoom {
  id: number
  title: string
  user_id: number
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: number
  chat_room_id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

// ── 채팅방 ────────────────────────────────────────────

/** POST /chat-rooms */
export function createChatRoom(title: string): Promise<ChatRoom> {
  return api.post('/chat-rooms', { title })
}

/** GET /chat-rooms?user_id={id} */
export function getChatRooms(userId: number): Promise<ChatRoom[]> {
  return api.get(`/chat-rooms?user_id=${userId}`)
}

/** GET /chat-rooms/{id} */
export function getChatRoom(id: number): Promise<ChatRoom> {
  return api.get(`/chat-rooms/${id}`)
}

/** PATCH /chat-rooms/{id}/title */
export function renameChatRoom(id: number, title: string): Promise<ChatRoom> {
  return api.patch(`/chat-rooms/${id}/title`, { title })
}

/** DELETE /chat-rooms/{id} */
export function deleteChatRoom(id: number): Promise<void> {
  return api.delete(`/chat-rooms/${id}`)
}

// ── 메시지 ────────────────────────────────────────────

export interface FacilityCard {
  name: string
  address: string
  category: string
  sub_category: string
  content_id: string
  lat: number
  lng: number
  tel: string
  operation: string
  has_parking: string
  indoor: string
  outdoor: string
  conditions: string
  description: string
  entrance_fee_amount: number | null
  entrance_fee_type: string
  extra_fee_amount: number | null
  extra_fee_type: string
  match_source: 'name_exact' | 'vector' | string
  match_confidence: number
}

export interface ChatTurnResponse {
  user_message: ChatMessage
  assistant_message: ChatMessage
  intent: { intent: string; confidence: number }
  facility: FacilityCard | null
  places: PlaceResult[] | null
}

/** POST /chat-rooms/{roomId}/messages — 의도분류 + AI 응답 포함 */
export function sendMessageWithResponse(
  roomId: number,
  content: string,
  petId?: number | null,
  userLat?: number | null,
  userLng?: number | null,
): Promise<ChatTurnResponse> {
  return api.post(`/chat-rooms/${roomId}/messages`, {
    role: 'user',
    content,
    pet_id: petId ?? null,
    user_lat: userLat ?? null,
    user_lng: userLng ?? null,
  })
}

/** POST /chat-rooms/{roomId}/messages — AI 응답 없이 직접 저장 (그림일기 플로우용) */
export function saveMessageDirect(
  roomId: number,
  role: 'user' | 'assistant',
  content: string,
): Promise<ChatMessage> {
  return api.post(`/chat-rooms/${roomId}/messages/save`, { role, content })
}

/** GET /places/by-name?name={name} */
export function getPlaceByName(name: string): Promise<FacilityCard> {
  return api.get(`/places/by-name?name=${encodeURIComponent(name)}`)
}

/** GET /places/{content_id} */
export function getPlaceByContentId(contentId: string): Promise<FacilityCard> {
  return api.get(`/places/${encodeURIComponent(contentId)}`)
}

/** GET /chat-rooms/{roomId}/messages */
export function getMessages(roomId: number): Promise<ChatMessage[]> {
  return api.get(`/chat-rooms/${roomId}/messages`)
}

/** GET /chat-rooms/{roomId}/messages?last_n={n} */
export function getRecentMessages(roomId: number, n: number): Promise<ChatMessage[]> {
  return api.get(`/chat-rooms/${roomId}/messages?last_n=${n}`)
}

/** PATCH /chat-rooms/{roomId}/messages/{messageId} */
export function updateMessageContent(
  roomId: number,
  messageId: number,
  content: string,
): Promise<ChatMessage> {
  return api.patch(`/chat-rooms/${roomId}/messages/${messageId}`, { content })
}
