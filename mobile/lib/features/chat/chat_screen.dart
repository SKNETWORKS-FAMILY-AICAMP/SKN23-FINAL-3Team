import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/router/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/models/place.dart';
import '../auth/auth_providers.dart';
import '../places/widgets/facility_modal_sheet.dart';
import '../places/widgets/place_card_tile.dart';
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
        leading: Builder(
          builder: (ctx) => IconButton(
            tooltip: '채팅방 목록',
            icon: const Icon(LucideIcons.menu),
            onPressed: () => Scaffold.of(ctx).openDrawer(),
          ),
        ),
        actions: [
          IconButton(
            tooltip: '새 채팅',
            icon: const Icon(LucideIcons.plus),
            onPressed: () =>
                ref.read(chatProvider.notifier).resetForNewRoom(),
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
                    ),
                  ),
          ),
          if (state.isSending) const LinearProgressIndicator(minHeight: 2),
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
  const _BubbleView({required this.bubble, required this.onTapButton});

  final ChatBubble bubble;
  final ValueChanged<String> onTapButton;

  @override
  Widget build(BuildContext context) {
    final isUser = bubble.isUser;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.88,
        ),
        margin: const EdgeInsets.symmetric(vertical: 4),
        child: Column(
          crossAxisAlignment:
              isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
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
                child: Text(
                  bubble.text,
                  style: TextStyle(
                    fontSize: 14,
                    color: isUser ? Colors.white : AppColors.darkBrown,
                    height: 1.5,
                  ),
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
            if (bubble.places != null && bubble.places!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: _PlaceList(places: bubble.places!),
              ),
            if (bubble.facility != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: _FacilityCardSummary(facility: bubble.facility!),
              ),
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

class _PlaceList extends StatelessWidget {
  const _PlaceList({required this.places});

  final List<PlaceCard> places;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final p in places) PlaceCardTile(place: p),
      ],
    );
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
