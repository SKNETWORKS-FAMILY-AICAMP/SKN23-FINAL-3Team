/// 다이어리 작성 유형 4종 — React `constants/diaryTypes.ts` 1:1 권위.
class DiaryType {
  const DiaryType({
    required this.id,
    required this.label,
    required this.description,
    required this.icon,
    required this.questions,
    required this.typeFocus,
  });

  final String id; // 'dog' | 'owner' | 'memory' | 'daily'
  final String label;
  final String description;
  final String icon;
  final List<String> questions;
  final String typeFocus;

  static const dog = DiaryType(
    id: 'dog',
    label: '강아지 시점',
    description: '강아지 눈으로 본 하루',
    icon: '🐶',
    questions: [
      '오늘 {petName}는 어디를 다녀왔나요? 어떤 하루였는지 편하게 말씀해주세요!',
      '오늘 {petName}가 가장 신나했던 순간이 있었나요?',
      '오늘 {petName}의 컨디션은 어땠나요? (먹은 것, 잠, 기분 등)',
    ],
    typeFocus: '강아지 1인칭 시점, 냄새·소리·촉감 등 감각적 묘사 중심',
  );

  static const owner = DiaryType(
    id: 'owner',
    label: '보호자 시점',
    description: '보호자가 바라본 우리 아이',
    icon: '🧡',
    questions: [
      '오늘 {petName}와 함께한 시간 중 가장 기억에 남는 장면은 무엇인가요?',
      '오늘 {petName}를 보면서 어떤 감정이 들었나요?',
      '오늘 {petName}와 가장 가깝게 교감한 순간은 언제였나요?',
    ],
    typeFocus: '보호자의 감정과 애정, 관찰자 시점의 따뜻한 묘사',
  );

  static const memory = DiaryType(
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
    typeFocus: '특별한 순간의 생생한 묘사, 오래 기억하고 싶은 장면 포착',
  );

  static const daily = DiaryType(
    id: 'daily',
    label: '일상 기록',
    description: '평범하지만 소중한 하루',
    icon: '☀️',
    questions: [
      '오늘 하루 {petName}와 어떻게 시작했나요?',
      '오늘 {petName}의 일상 중 가장 귀여웠던 순간은요?',
      '오늘 하루를 보내고 어떤 느낌이 드나요?',
    ],
    typeFocus: '소소한 일상의 따뜻함, 반복되는 일상 속 특별함 포착',
  );

  static const all = [dog, owner, memory, daily];

  static DiaryType byId(String id) {
    return all.firstWhere((t) => t.id == id, orElse: () => daily);
  }
}

/// 다이어리 작성 톤 — React `constants/emotions.ts` 1:1 권위 (12종).
/// 캘린더 즐겨찾기 셀 표시 6종 (😊😌🤣😪🥺😡) 과 다른 도메인 — 캘린더는 별도 라벨 셋.
class DiaryEmotion {
  const DiaryEmotion({
    required this.emoji,
    required this.label,
    required this.tone,
  });

  final String emoji;
  final String label;
  final String tone;

  static const all = <DiaryEmotion>[
    DiaryEmotion(emoji: '😊', label: '신나고 행복해요', tone: '밝고 신나고 경쾌한 톤'),
    DiaryEmotion(emoji: '😄', label: '기분이 너무 좋아요', tone: '활기찬 하루'),
    DiaryEmotion(emoji: '😂', label: '너무 웃겨요', tone: '신나고 과장된 즐거움'),
    DiaryEmotion(emoji: '😅', label: '살짝 민망했어요', tone: '귀엽게 당황'),
    DiaryEmotion(emoji: '🥰', label: '너무 사랑스러워요', tone: '두근두근 설렘'),
    DiaryEmotion(emoji: '🤍', label: '사랑스럽고 애틋해요', tone: '다정한 애정'),
    DiaryEmotion(emoji: '😌', label: '평온하고 여유로워요', tone: '잔잔한 평온'),
    DiaryEmotion(emoji: '🙂', label: '그냥 만족스러워요', tone: '충분한 행복'),
    DiaryEmotion(emoji: '🥹', label: '뭉클하고 감동적이에요', tone: '여운이 남는 감성'),
    DiaryEmotion(emoji: '😴', label: '나른하고 피곤해요', tone: '담백하고 느릿'),
    DiaryEmotion(emoji: '😟', label: '조금 걱정되거나 불안해요', tone: '조심스러운 세심함'),
    DiaryEmotion(emoji: '😢', label: '슬프고 쓸쓸해요', tone: '잔잔한 울컥'),
  ];
}
