import 'package:flutter_test/flutter_test.dart';
import 'package:withdog_app/features/chat/chat_message_parser.dart';

void main() {
  group('ChatMessageParser Tests', () {
    test('isDiaryTrigger should detect trigger marker', () {
      expect(ChatMessageParser.isDiaryTrigger('%%TRIGGER:START_DIARY%%'), isTrue);
      expect(ChatMessageParser.isDiaryTrigger('%%TRIGGER:START_DIARY%%  '), isTrue);
      expect(ChatMessageParser.isDiaryTrigger('Other text'), isFalse);
    });

    test('parse should extract buttons from marker', () {
      const content = '질문입니다. %%BUTTONS%% 버튼1 | 버튼2 | 버튼3';
      final parsed = ChatMessageParser.parse(content);

      expect(parsed.text, '질문입니다.');
      expect(parsed.buttons, ['버튼1', '버튼2', '버튼3']);
    });

    test('parse should return empty buttons if marker missing', () {
      const content = '버튼 없는 메시지';
      final parsed = ChatMessageParser.parse(content);

      expect(parsed.text, '버튼 없는 메시지');
      expect(parsed.buttons, isEmpty);
    });

    test('parse should handle multiple pipes and whitespace', () {
      const content = '텍스트%%BUTTONS%% A || B |  C  ';
      final parsed = ChatMessageParser.parse(content);

      expect(parsed.text, '텍스트');
      expect(parsed.buttons, ['A', 'B', 'C']);
    });
  });
}
