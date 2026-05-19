import type { DiaryTypeId } from '../constants/diaryTypes'

export interface DiaryGenerationInput {
  petName: string
  breed?: string
  birthDate?: string
  personalities?: string[]
  ownerName?: string
  ownerGender?: string
  diaryType: DiaryTypeId
  typeFocus: string
  mainAnswers: string[]
  additionalAnswers: string[]
  emotionEmoji: string
  emotionTone: string
}

export interface GeneratedDiary {
  title: string
  content: string
  summary: string
  emotion?: string          // 챗봇에서 선택한 감정 이모지
  image_prompt?: string
  session_id?: string
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('access_token')
  return token
    ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' }
}

export async function generateDiary(input: DiaryGenerationInput): Promise<GeneratedDiary> {
  const res = await fetch(`/api/diary/generate`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      pet_name: input.petName,
      breed: input.breed ?? '강아지',
      birth_date: input.birthDate ?? null,
      personalities: input.personalities ?? [],
      owner_name: input.ownerName ?? '',
      owner_gender: input.ownerGender ?? '',
      main_answers: input.mainAnswers,
      additional_answers: input.additionalAnswers,
      diary_type: input.diaryType,
      emotion_emoji: input.emotionEmoji,
    }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string }
    throw new Error(err.detail ?? `일기 API 오류 ${res.status}`)
  }

  const data = await res.json()
  return {
    title: data.title,
    content: data.content,
    summary: data.summary,
    image_prompt: data.image_prompt,
    session_id: data.session_id,
  }
}

export async function generateDiaryImage(imagePrompt: string, sessionId?: string): Promise<string> {
  const res = await fetch(`/api/diary/generate-image`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ image_prompt: imagePrompt, session_id: sessionId ?? '' }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string }
    throw new Error(err.detail ?? `이미지 API 오류 ${res.status}`)
  }
  const data = await res.json() as { image_base64: string }
  return `data:image/png;base64,${data.image_base64}`
}

export type PhotoStyleResult =
  | { type: 'image_diary'; content: string; imageUrl: string }
  | { type: 'bot_text';    content: string }

export async function photoStyle(
  file: File,
  chatRoomId?: number,
  dogId?: number,
): Promise<PhotoStyleResult> {
  const formData = new FormData()
  formData.append('file', file)
  if (chatRoomId != null) formData.append('chat_room_id', String(chatRoomId))
  if (dogId != null)      formData.append('dog_id',       String(dogId))

  const token = localStorage.getItem('access_token')
  const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {}

  const res = await fetch('/api/diary/photo-style', {
    method: 'POST',
    headers,
    body: formData,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string }
    throw new Error(err.detail ?? `사진 변환 API 오류 ${res.status}`)
  }

  const data = await res.json() as { type: string; content: string; image_url?: string }

  if (data.type === 'image_diary' && data.image_url) {
    return { type: 'image_diary', content: data.content, imageUrl: data.image_url }
  }
  return { type: 'bot_text', content: data.content }
}

// ── Mock ─────────────────────────────────────────────
const OPENERS: Record<string, string> = {
  '😊': '오늘은 정말 신나는 하루였다! 멍!',
  '😌': '오늘은 조용하고 포근한 하루였다.',
  '🥹': '오늘은 왠지 뭉클하고 감사한 하루였다.',
  '😴': '오늘은 나른하고 늘어지는 하루였다.',
  '😟': '오늘은 조금 마음이 쓰이는 하루였다.',
  '🤍': '오늘은 보호자가 유난히 소중하게 느껴진 하루였다.',
}
const CLOSERS: Record<string, string> = {
  '😊': '내일도 이렇게 신나면 정말 좋겠다!',
  '😌': '이런 하루가 계속되면 좋겠다.',
  '🥹': '보호자랑 함께라면 매일이 특별하다.',
  '😴': '오늘도 보호자 옆에서 편하게 잠들 것 같다.',
  '😟': '그래도 보호자가 곁에 있으니 괜찮다.',
  '🤍': '보호자, 오늘도 고마워. 내가 더 사랑해.',
}

function mockGenerateDiary(input: DiaryGenerationInput): GeneratedDiary {
  const { petName, emotionEmoji, mainAnswers, additionalAnswers } = input
  const allAnswers = [...mainAnswers, ...additionalAnswers].filter((a) => a.trim())
  const opener = OPENERS[emotionEmoji] ?? '오늘은 특별한 하루였다.'
  const closer = CLOSERS[emotionEmoji] ?? `${petName}의 소중한 하루가 끝났다.`
  const middle = allAnswers.length > 0
    ? allAnswers.slice(0, 3).map((a) => a.trim().replace(/[.。]$/, '')).join('. 그리고 ') + '.'
    : '보호자와 함께 평범하지만 소중한 시간을 보냈다.'
  return {
    title: `${petName}의 오늘 하루`,
    content: `${opener} ${middle} ${closer}`,
    summary: `오늘도 ${petName}와 보호자의 소중한 하루.`,
    image_prompt: `A cute ${input.breed ?? 'dog'} named ${petName} having a fun day with its owner, illustrated in a warm pastel picture book style, soft colors, cheerful mood`,
    session_id: 'mock',
  }
}
