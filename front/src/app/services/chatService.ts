import { api } from './apiClient'

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

export interface ChatTurnResponse {
  user_message: ChatMessage
  assistant_message: ChatMessage
  intent: { intent: string; confidence: number }
}

/** POST /chat-rooms/{roomId}/messages — 의도분류 + AI 응답 포함 */
export function sendMessageWithResponse(
  roomId: number,
  content: string,
  petId?: number | null,
): Promise<ChatTurnResponse> {
  return api.post(`/chat-rooms/${roomId}/messages`, {
    role: 'user',
    content,
    pet_id: petId ?? null,
  })
}

/** POST /chat-rooms/{roomId}/messages */
export function saveMessage(
  roomId: number,
  role: 'user' | 'assistant',
  content: string,
): Promise<ChatMessage> {
  return api.post(`/chat-rooms/${roomId}/messages`, { role, content })
}

/** GET /chat-rooms/{roomId}/messages */
export function getMessages(roomId: number): Promise<ChatMessage[]> {
  return api.get(`/chat-rooms/${roomId}/messages`)
}

/** GET /chat-rooms/{roomId}/messages?last_n={n} */
export function getRecentMessages(roomId: number, n: number): Promise<ChatMessage[]> {
  return api.get(`/chat-rooms/${roomId}/messages?last_n=${n}`)
}
