export interface EmotionInfo {
  emoji: string
  label: string
  tone: string
}

export const EMOTIONS: EmotionInfo[] = [
  { emoji: '😊', label: '신나고 행복해요', tone: '활기차고 신나는 톤, 긍정적이고 에너지 넘침' },
  { emoji: '😌', label: '평온하고 여유로워요', tone: '잔잔하고 따뜻한 톤, 포근하고 안정적' },
  { emoji: '🥹', label: '뭉클하고 감동적이에요', tone: '감동적이고 따뜻한 톤, 진심 어린 감사함' },
  { emoji: '😴', label: '나른하고 피곤해요', tone: '느릿하고 나른한 톤, 편안하게 늘어지는 느낌' },
  { emoji: '😟', label: '조금 걱정되거나 슬퍼요', tone: '조심스럽고 섬세한 톤, 공감 어린 위로' },
  { emoji: '🤍', label: '사랑스럽고 애틋해요', tone: '사랑스럽고 애틋한 톤, 유대감과 애정 강조' },
]
