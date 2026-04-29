export interface EmotionInfo {
  emoji: string
  label: string
  tone: string
}

export const EMOTIONS: EmotionInfo[] = [
  { emoji: '😊', label: '신나고 행복해요', tone: '밝고 신나고 경쾌한 톤. 짧고 통통 튀는 문장.' },
  { emoji: '😄', label: '기분이 너무 좋아요', tone: '밝고 환한 톤. 활기차고 기분 좋은 하루.' },
  { emoji: '😂', label: '너무 웃겨요', tone: '신나고 과장되게 즐거운 톤. 참을 수 없이 웃긴 상황.' },
  { emoji: '😅', label: '살짝 민망했어요', tone: '살짝 민망하고 쑥스러운 톤. 귀엽게 당황한 느낌.' },
  { emoji: '🥰', label: '너무 사랑스러워요', tone: '두근두근 설레고 사랑스러운 톤. 달달한 문장.' },
  { emoji: '🤍', label: '사랑스럽고 애틋해요', tone: '다정하고 애틋한 톤. 보호자에 대한 사랑이 묻어남.' },
  { emoji: '😌', label: '평온하고 여유로워요', tone: '잔잔하고 평온한 톤. 느긋하고 부드럽게 흘러가는 문장.' },
  { emoji: '🙂', label: '그냥 만족스러워요', tone: '잔잔하고 만족스러운 톤. 충분히 행복한 느낌.' },
  { emoji: '🥹', label: '뭉클하고 감동적이에요', tone: '감성적이고 뭉클한 톤. 여운이 남는 문장.' },
  { emoji: '😴', label: '나른하고 피곤해요', tone: '나른하고 졸린 톤. 담백하고 느릿한 문장.' },
  { emoji: '😟', label: '조금 걱정되거나 불안해요', tone: '살짝 걱정되고 세심한 톤. 조심스럽지만 부드럽게 마무리.' },
  { emoji: '😢', label: '슬프고 쓸쓸해요', tone: '슬프고 쓸쓸한 톤. 잔잔하게 울컥하는 느낌.' },
]
