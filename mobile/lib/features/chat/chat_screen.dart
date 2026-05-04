import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/router/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/models/place.dart';
import '../auth/auth_providers.dart';
import '../home/home_tab_index.dart';
import '../places/map_focus_provider.dart';
import '../places/widgets/facility_modal_sheet.dart';
import 'chat_history_drawer.dart';
import 'chat_providers.dart';
import 'chat_state.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _inputCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();

  @override
  void dispose() {
    _inputCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _send([String? overrideText]) async {
    final text = (overrideText ?? _inputCtrl.text).trim();
    if (text.isEmpty) return;
    if (overrideText == null) _inputCtrl.clear();

    final auth = ref.read(authProvider);
    final petId = auth is AuthAuthenticated
        ? auth.user.primaryPetId ?? auth.user.primaryPet?.id
        : null;

    final outcome = await ref
        .read(chatProvider.notifier)
        .sendUserMessage(text, petId: petId);
    _scrollToBottom();

    if (outcome == ChatTurnOutcome.triggerDiary) {
      if (mounted) context.push(AppRoutes.diaryDraft);
    } else if (outcome == ChatTurnOutcome.failed) {
      final err = ref.read(chatProvider).error;
      if (err != null) Fluttertoast.showToast(msg: err);
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  /// 채팅 닫기 — 홈 탭으로 복귀.
  void _closeChat() {
    if (context.canPop()) {
      context.pop();
    } else {
      context.go(AppRoutes.home);
    }
  }

  /// 지도 탭으로 빠져나가기 (Bug #2 — 채팅 → 지도 연결).
  void _openMapTab() {
    ref.read(homeTabIndexProvider.notifier).state = 2;
    _closeChat();
  }

  /// 챗봇 응답 카드의 장소 이름 탭 → 지도 탭으로 이동 + 해당 장소 focus + 모달
  /// (Bug #6 — 웹 동작 1:1 매핑).
  void _focusPlaceOnMap(PlaceCard place) {
    ref.read(mapFocusProvider.notifier).requestFocus(place);
    ref.read(homeTabIndexProvider.notifier).state = 2;
    _closeChat();
  }

  /// 다이어리 작성으로 빠져나가기 (Bug #3 — 채팅 → 다이어리 연결).
  void _openDiaryDraft() {
    context.push(AppRoutes.diaryDraft);
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(chatProvider);
    return Scaffold(
      drawer: const ChatHistoryDrawer(),
      appBar: AppBar(
        title: const Text('AI 멍봇'),
        backgroundColor: Colors.white,
        foregroundColor: AppColors.darkBrown,
        elevation: 0,
        // 사용자 요청 (Bug #6 정정, 2026-05-04 저녁):
        //  - leading = 햄버거 (drawer 진입 — 새 채팅·채팅방 목록 권위)
        //  - actions = X 닫기 (홈 복귀)
        //  - 우측 새채팅 IconButton 은 제거 (drawer 안 "+ 새 채팅" 으로 충분)
        leading: Builder(
          builder: (ctx) => IconButton(
            tooltip: '메뉴',
            icon: const Icon(LucideIcons.menu),
            onPressed: () => Scaffold.of(ctx).openDrawer(),
          ),
        ),
        actions: [
          IconButton(
            tooltip: '닫기',
            icon: const Icon(LucideIcons.x),
            onPressed: _closeChat,
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: state.messages.isEmpty
                ? const _Welcome()
                : ListView.builder(
                    controller: _scrollCtrl,
                    padding: const EdgeInsets.all(12),
                    itemCount: state.messages.length,
                    itemBuilder: (_, i) => _BubbleView(
                      bubble: state.messages[i],
                      onTapButton: _send,
                      onOpenMap: _openMapTab,
                      onOpenDiary: _openDiaryDraft,
                      onPlaceTapToMap: _focusPlaceOnMap,
                    ),
                  ),
          ),
          if (state.isSending) const LinearProgressIndicator(minHeight: 2),
          _QuickNavBar(
            onMapTap: _openMapTab,
            onDiaryTap: _openDiaryDraft,
          ),
          _Composer(
            controller: _inputCtrl,
            onSubmit: () => _send(),
            disabled: state.isSending,
          ),
        ],
      ),
    );
  }
}

class _Welcome extends StatelessWidget {
  const _Welcome();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            LucideIcons.messageCircle,
            size: 56,
            color: AppColors.brandOrange,
          ),
          const SizedBox(height: 16),
          const Text(
            '안녕하세요! 저는 우리 아이의 반짝이는 하루와\n소중한 추억을 차곡차곡 담아드리는 AI 멍봇이에요',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              color: AppColors.darkBrown,
              height: 1.6,
            ),
          ),
          const SizedBox(height: 24),
          const Text(
            '오늘은 어떤 하루를 남겨볼까요?',
            style: TextStyle(color: AppColors.subBrown2),
          ),
        ],
      ),
    );
  }
}

class _BubbleView extends StatelessWidget {
  const _BubbleView({
    required this.bubble,
    required this.onTapButton,
    required this.onOpenMap,
    required this.onOpenDiary,
    required this.onPlaceTapToMap,
  });

  final ChatBubble bubble;
  final ValueChanged<String> onTapButton;
  final VoidCallback onOpenMap;
  final VoidCallback onOpenDiary;
  final ValueChanged<PlaceCard> onPlaceTapToMap;

  @override
  Widget build(BuildContext context) {
    final isUser = bubble.isUser;
    // React commit 033a2db 정합성 — bot 메시지 좌측에 chatbot_logo prefix.
    // Row(items-end) 패턴: prefix 32×32 + 8px gap + bubble Column.
    // user 메시지는 prefix 없음. maxWidth 는 prefix 공간 고려 80% (assistant) /
    // 88% (user). 기존 88% 유지하면 prefix 추가 시 우측 잘림 가능.
    final bubbleMaxWidth =
        MediaQuery.of(context).size.width * (isUser ? 0.88 : 0.80);
    final bubbleColumn = ConstrainedBox(
      constraints: BoxConstraints(maxWidth: bubbleMaxWidth),
      child: Column(
        crossAxisAlignment:
            isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          if (bubble.text.isNotEmpty)
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 14,
                vertical: 10,
              ),
              decoration: BoxDecoration(
                color: isUser ? AppColors.brandOrange : Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: isUser
                    ? null
                    : [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.06),
                          blurRadius: 4,
                          offset: const Offset(0, 1),
                        ),
                      ],
              ),
              child: _BubbleText(
                text: bubble.text,
                isUser: isUser,
                // Bug #9 — places 첨부된 assistant 응답은 본문 안 "1. <장소명> 📍"
                // 패턴 line 을 클릭 가능한 링크로 렌더 (web ChatBot.tsx 1:1).
                places: !isUser ? bubble.places : null,
                onPlaceTap: onPlaceTapToMap,
              ),
            ),
          if (bubble.buttons.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (var i = 0; i < bubble.buttons.length; i++)
                    _InlineButton(
                      label: bubble.buttons[i],
                      primary: i == 0,
                      onTap: () => onTapButton(bubble.buttons[i]),
                    ),
                ],
              ),
            ),
          if (bubble.facility != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: _FacilityCardSummary(facility: bubble.facility!),
            ),
        ],
      ),
    );
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            if (!isUser) ...[
              Padding(
                padding: const EdgeInsets.only(bottom: 2),
                child: Image.asset(
                  'assets/chatbot_logo.png',
                  width: 32,
                  height: 32,
                ),
              ),
              const SizedBox(width: 8),
            ],
            Flexible(child: bubbleColumn),
          ],
        ),
      ),
    );
  }
}

class _InlineButton extends StatelessWidget {
  const _InlineButton({
    required this.label,
    required this.primary,
    required this.onTap,
  });

  final String label;
  final bool primary;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return primary
        ? FilledButton(
            onPressed: onTap,
            style: FilledButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              backgroundColor: AppColors.brandOrange,
            ),
            child: Text(label),
          )
        : OutlinedButton(
            onPressed: onTap,
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              side: const BorderSide(color: AppColors.beige),
              foregroundColor: AppColors.subBrown2,
            ),
            child: Text(label),
          );
  }
}

/// Bug #9 (web ChatBot.tsx 1:1) — assistant 응답 본문 텍스트 렌더.
///
/// `places` 가 있으면 본문 line 중 "숫자. 장소명 📍" 패턴을 검출 → 그 부분을
/// 오렌지 underlined InkWell 로 감싸서 탭 → `onPlaceTap(place)` (지도 라우팅).
/// `**bold**` 마크다운 처리 + `_요약_:` / 이미지 markdown line 필터 (React 1:1).
/// `_id:`·`_score:` 등 백엔드 내부 메타가 본문에 섞여 들어와도 가시화 차단 (Bug #8).
class _BubbleText extends StatelessWidget {
  const _BubbleText({
    required this.text,
    required this.isUser,
    this.places,
    required this.onPlaceTap,
  });

  final String text;
  final bool isUser;
  final List<PlaceCard>? places;
  final ValueChanged<PlaceCard> onPlaceTap;

  // 본문에서 숨겨야 할 line — 백엔드가 디버그·메타 정보를 흘려보낼 가능성 차단.
  // React 의 `renderBotText` 도 `_요약_:` 와 image markdown 을 제거.
  // 백엔드 chat_response_service `_format_place_list_response` 가 `- _id: <hex>`
  // 를 명시적으로 emit (line 308-309) — `-`/공백 prefix 도 매칭 (Bug #8 정정).
  static final _hideLinePatterns = <RegExp>[
    RegExp(r'^_요약_:'),
    RegExp(r'^[-\s]*_id\s*[:=]', caseSensitive: false),
    RegExp(r'^[-\s]*_?score\s*[:=]', caseSensitive: false),
    RegExp(r'^[-\s]*content_id\s*[:=]', caseSensitive: false),
    RegExp(r'^[-\s]*session_id\s*[:=]', caseSensitive: false),
    RegExp(r'^[-\s]*image_prompt', caseSensitive: false),
  ];

  // 이미지 markdown (`![alt](url)`) — Image.network 으로 렌더 (Bug #7 정정,
  // 백엔드 `_finalize_diary_and_save` 가 그림일기 완성 시 image_url 을 markdown 으로 emit)
  static final _imageMarkdownRegex = RegExp(r'^!\[(.*?)\]\((https?:\/\/[^\)]+)\)');

  // "1. 장소명" / "1) 장소명" / "1. **장소명**" / 끝에 📍 옵션 (Bug #9 정정 —
  // 운영 백엔드 `_format_place_list_response` 가 📍 emoji 미사용)
  static final _placeLineRegex =
      RegExp(r'^(\d+)[.)]\s*(?:\*\*)?(.+?)(?:\*\*)?\s*(?:📍\s*)?$');

  @override
  Widget build(BuildContext context) {
    final color = isUser ? Colors.white : AppColors.darkBrown;
    final placeMap = <String, PlaceCard>{
      for (final p in places ?? const <PlaceCard>[]) p.name: p,
    };

    final lines = text
        .split('\n')
        .where((l) => !_hideLinePatterns.any((re) => re.hasMatch(l.trim())))
        .toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < lines.length; i++)
          _renderLine(context, lines[i], color, placeMap, isLast: i == lines.length - 1),
      ],
    );
  }

  Widget _renderLine(
    BuildContext context,
    String line,
    Color color,
    Map<String, PlaceCard> placeMap, {
    required bool isLast,
  }) {
    final padding = EdgeInsets.only(bottom: isLast ? 0 : 4);

    // 이미지 markdown — `![alt](url)` 을 Image.network 으로 렌더 (Bug #7 정정).
    final imgMatch = _imageMarkdownRegex.firstMatch(line.trim());
    if (imgMatch != null) {
      final url = imgMatch.group(2)!;
      return Padding(
        padding: padding,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: Image.network(
            url,
            fit: BoxFit.cover,
            errorBuilder: (_, _, _) => const SizedBox.shrink(),
          ),
        ),
      );
    }

    final placeMatch = _placeLineRegex.firstMatch(line);
    if (placeMatch != null && placeMap.isNotEmpty) {
      final num = placeMatch.group(1)!;
      final name = placeMatch.group(2)!.trim();
      final place = placeMap[name] ?? _bestMatch(name, placeMap);
      if (place != null) {
        return Padding(
          padding: padding,
          child: InkWell(
            onTap: () => onPlaceTap(place),
            child: RichText(
              text: TextSpan(
                style: TextStyle(
                  fontSize: 14,
                  color: AppColors.brandOrange,
                  fontWeight: FontWeight.w600,
                  decoration: TextDecoration.underline,
                  decorationColor: AppColors.brandOrange,
                  height: 1.5,
                ),
                children: [
                  TextSpan(text: '$num. $name 📍'),
                ],
              ),
            ),
          ),
        );
      }
    }

    // 일반 line — `**bold**` 처리
    return Padding(
      padding: padding,
      child: RichText(
        text: TextSpan(
          style: TextStyle(fontSize: 14, color: color, height: 1.5),
          children: _boldSpans(line, color),
        ),
      ),
    );
  }

  /// 부분 문자열 일치로 PlaceCard 찾기 — bullet 패턴 변형 대응.
  PlaceCard? _bestMatch(String name, Map<String, PlaceCard> placeMap) {
    for (final entry in placeMap.entries) {
      if (entry.key.contains(name) || name.contains(entry.key)) {
        return entry.value;
      }
    }
    return null;
  }

  List<TextSpan> _boldSpans(String line, Color color) {
    final spans = <TextSpan>[];
    final pattern = RegExp(r'\*\*(.+?)\*\*');
    int last = 0;
    for (final m in pattern.allMatches(line)) {
      if (m.start > last) {
        spans.add(TextSpan(text: line.substring(last, m.start)));
      }
      spans.add(TextSpan(
        text: m.group(1),
        style: const TextStyle(fontWeight: FontWeight.bold),
      ));
      last = m.end;
    }
    if (last < line.length) {
      spans.add(TextSpan(text: line.substring(last)));
    }
    if (spans.isEmpty) return [TextSpan(text: line, style: TextStyle(color: color))];
    return spans;
  }
}

class _FacilityCardSummary extends StatelessWidget {
  const _FacilityCardSummary({required this.facility});

  final FacilityCard facility;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: () {
        showModalBottomSheet<void>(
          context: context,
          isScrollControlled: true,
          backgroundColor: Colors.white,
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          builder: (_) => FacilityModalSheet(name: facility.name),
        );
      },
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.beige),
        ),
        child: Row(
          children: [
            const Icon(LucideIcons.building2, color: AppColors.brandOrange),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    facility.name,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      color: AppColors.darkBrown,
                    ),
                  ),
                  if (facility.address.isNotEmpty)
                    Text(
                      facility.address,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.mutedForeground,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                ],
              ),
            ),
            const Icon(
              LucideIcons.chevronRight,
              color: AppColors.mutedForeground,
              size: 18,
            ),
          ],
        ),
      ),
    );
  }
}

/// 채팅 → 지도/다이어리 빠른 이동 바 (Composer 위에 상시 표시).
/// 사용자 결정 2026-05-04: 채팅에서 다른 화면으로 이어지는 경로 항시 노출.
class _QuickNavBar extends StatelessWidget {
  const _QuickNavBar({required this.onMapTap, required this.onDiaryTap});

  final VoidCallback onMapTap;
  final VoidCallback onDiaryTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 6, 12, 6),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: AppColors.beige)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextButton.icon(
              onPressed: onMapTap,
              icon: const Icon(LucideIcons.mapPin, size: 16),
              label: const Text('지도'),
              style: TextButton.styleFrom(
                foregroundColor: AppColors.subBrown2,
              ),
            ),
          ),
          Expanded(
            child: TextButton.icon(
              onPressed: onDiaryTap,
              icon: const Icon(LucideIcons.bookOpen, size: 16),
              label: const Text('다이어리'),
              style: TextButton.styleFrom(
                foregroundColor: AppColors.subBrown2,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Composer extends StatelessWidget {
  const _Composer({
    required this.controller,
    required this.onSubmit,
    required this.disabled,
  });

  final TextEditingController controller;
  final VoidCallback onSubmit;
  final bool disabled;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: AppColors.beige)),
        ),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: controller,
                enabled: !disabled,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => onSubmit(),
                decoration: const InputDecoration(
                  hintText: '편하게 말씀해주세요...',
                ),
              ),
            ),
            const SizedBox(width: 8),
            FilledButton(
              onPressed: disabled ? null : onSubmit,
              style: FilledButton.styleFrom(
                shape: const CircleBorder(),
                padding: const EdgeInsets.all(12),
              ),
              child: const Icon(LucideIcons.send, size: 18),
            ),
          ],
        ),
      ),
    );
  }
}
