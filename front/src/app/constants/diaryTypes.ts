export type DiaryTypeId = 'dog' | 'owner' | 'memory' | 'daily'

export interface DiaryTypeInfo {
  id: DiaryTypeId
  label: string
  description: string
  icon: string
  questions: string[]
  additionalPerspective: DiaryTypeId
  perspectiveSuggestion: string
  additionalQuestions: string[]
  typeFocus: string
}

export const DIARY_TYPES: DiaryTypeInfo[] = [
  {
    id: 'dog',
    label: '강아지 시점',
    description: '강아지 눈으로 본 하루',
    icon: '🐶',
    questions: [
      '오늘 {petName}는 어디를 다녀왔나요? 어떤 하루였는지 편하게 말씀해주세요!',
      '오늘 {petName}가 가장 신나했던 순간이 있었나요?',
      '오늘 {petName}의 컨디션은 어땠나요? (먹은 것, 잠, 기분 등)',
    ],
    additionalPerspective: 'owner',
    perspectiveSuggestion:
      '오늘 보호자 눈에 {petName}는 어떻게 보였나요? 보호자 시점의 기억도 함께 남겨볼까요?',
    additionalQuestions: [
      '오늘 {petName}가 어떤 감정이었는지 한 단어로 표현하면요?',
      '보호자의 행동 중 {petName}가 가장 좋아했던 것은 무엇인가요?',
    ],
    typeFocus: '강아지 1인칭 시점, 냄새·소리·촉감 등 감각적 묘사 중심',
  },
  {
    id: 'owner',
    label: '보호자 시점',
    description: '보호자가 바라본 우리 아이',
    icon: '🧡',
    questions: [
      '오늘 {petName}와 함께한 시간 중 가장 기억에 남는 장면은 무엇인가요?',
      '오늘 {petName}를 보면서 어떤 감정이 들었나요?',
      '오늘 {petName}와 가장 가깝게 교감한 순간은 언제였나요?',
    ],
    additionalPerspective: 'dog',
    perspectiveSuggestion:
      '그 순간 {petName}는 어떤 기분이었을까요? 강아지 마음도 상상해볼까요?',
    additionalQuestions: [
      '오늘 {petName}가 보여준 행동 중 귀엽거나 인상적인 것이 있었나요?',
      '{petName}가 오늘 특히 신나거나 행복해 보인 순간이 있었나요?',
    ],
    typeFocus: '보호자의 감정과 애정, 관찰자 시점의 따뜻한 묘사',
  },
  {
    id: 'memory',
    label: '특별한 순간',
    description: '잊고 싶지 않은 그날의 기록',
    icon: '📸',
    questions: [
      '오늘 {petName}와 어떤 특별한 일이 있었나요?',
      '그 순간 {petName}는 어떤 반응을 보였나요?',
      '그 장면을 묘사해주세요. 어떤 장소, 어떤 분위기였나요?',
      '왜 그 순간이 특별하게 느껴지나요?',
    ],
    additionalPerspective: 'dog',
    perspectiveSuggestion:
      '{petName} 입장에서는 어떤 경험이었을지도 남겨볼까요?',
    additionalQuestions: [
      '그 순간 {petName}가 느꼈을 감각적인 경험을 상상해본다면요? (냄새, 소리, 느낌 등)',
      '그날의 분위기를 색깔이나 날씨로 표현하면 어떤가요?',
    ],
    typeFocus: '특별한 순간의 생생한 묘사, 오래 기억하고 싶은 장면 포착',
  },
  {
    id: 'daily',
    label: '일상 기록',
    description: '평범하지만 소중한 하루',
    icon: '☀️',
    questions: [
      '오늘 하루 {petName}와 어떻게 시작했나요?',
      '오늘 {petName}의 일상 중 가장 귀여웠던 순간은요?',
      '오늘 하루를 보내고 어떤 느낌이 드나요?',
    ],
    additionalPerspective: 'dog',
    perspectiveSuggestion:
      '{petName}가 오늘 하루를 어떻게 느꼈을지 강아지 시점으로도 써볼까요?',
    additionalQuestions: [
      '오늘 {petName}와 함께여서 따뜻했던 순간이 있었나요?',
      '오늘 {petName}가 가장 행복해 보인 순간은 언제였나요?',
    ],
    typeFocus: '소소한 일상의 따뜻함, 반복되는 일상 속 특별함 포착',
  },
]
