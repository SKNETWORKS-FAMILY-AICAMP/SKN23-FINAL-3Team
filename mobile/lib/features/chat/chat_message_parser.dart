/// 백엔드 assistant 메시지의 마커 파싱 권위 (`ChatBot.tsx:12-21` 1:1).
///
/// - `%%BUTTONS%%버튼1|버튼2|...` → `text` 와 `buttons` 분리
/// - `%%TRIGGER:START_DIARY%%` 단독 메시지 = 다이어리 작성 흐름 시작 트리거
class ChatMessageParser {
  static const buttonsMarker = '%%BUTTONS%%';
  static const diaryFlowTrigger = '%%TRIGGER:START_DIARY%%';

  /// 트리거 메시지 여부.
  static bool isDiaryTrigger(String content) =>
      content.trim() == diaryFlowTrigger;

  /// 인라인 버튼 분리.
  static ParsedMessage parse(String content) {
    final idx = content.indexOf(buttonsMarker);
    if (idx == -1) return ParsedMessage(text: content, buttons: const []);
    final text = content.substring(0, idx).trim();
    final btnPart = content.substring(idx + buttonsMarker.length);
    final buttons = btnPart
        .split('|')
        .map((b) => b.trim())
        .where((b) => b.isNotEmpty)
        .toList();
    return ParsedMessage(text: text, buttons: buttons);
  }
}

class ParsedMessage {
  const ParsedMessage({required this.text, required this.buttons});

  final String text;
  final List<String> buttons;
}
