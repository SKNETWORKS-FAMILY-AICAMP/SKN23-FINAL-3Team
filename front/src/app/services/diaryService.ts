import type { DiaryTypeId } from '../constants/diaryTypes'

export interface DiaryGenerationInput {
  petName: string
  breed?: string
  birthDate?: string
  personalities?: string[]
  ownerName?: string
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

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export async function generateDiary(input: DiaryGenerationInput): Promise<GeneratedDiary> {
  try {
    const res = await fetch(`${API_BASE}/api/diary/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pet_name: input.petName,
        breed: input.breed ?? '강아지',
        birth_date: input.birthDate ?? null,
        personalities: input.personalities ?? [],
        owner_name: input.ownerName ?? '',
        main_answers: input.mainAnswers,
        additional_answers: input.additionalAnswers,
        diary_type: input.diaryType,
        emotion_emoji: input.emotionEmoji,
      }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({})) as { detail?: string }
      throw new Error(err.detail ?? `API 오류 ${res.status}`)
    }

    const data = await res.json()
    return {
      title: data.title,
      content: data.content,
      summary: data.summary,
      image_prompt: data.image_prompt,
      session_id: data.session_id,
    }
  } catch (e) {
    console.warn('[diaryService] API 호출 실패, mock으로 대체합니다.', e)
    await new Promise((r) => setTimeout(r, 1500))
    return mockGenerateDiary(input)
  }
}

export async function generateDiaryImage(imagePrompt: string, sessionId?: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/diary/generate-image`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_prompt: imagePrompt, session_id: sessionId ?? '' }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string }
    throw new Error(err.detail ?? `이미지 API 오류 ${res.status}`)
  }
  const data = await res.json() as { image_base64: string }
  return `data:image/png;base64,${data.image_base64}`
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
  }
}
