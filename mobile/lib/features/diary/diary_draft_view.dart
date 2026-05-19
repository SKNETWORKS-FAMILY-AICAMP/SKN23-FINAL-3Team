import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/theme/app_colors.dart';
import '../../shared/models/place.dart';
import '../auth/auth_providers.dart';
import 'diary_draft_provider.dart';
import 'diary_draft_state.dart';
import 'diary_types.dart';

/// 다이어리 작성 공통 위젯 — 두 진입점 (챗봇 trigger / 외부 라우트) 재사용.
/// `onCompleted` 가 호출되면 호출자가 라우트 pop 또는 후속 화면 결정.
class DiaryDraftView extends ConsumerStatefulWidget {
  const DiaryDraftView({super.key, this.contextPlace, this.onCompleted});

  final PlaceCard? contextPlace;
  final VoidCallback? onCompleted;

  @override
  ConsumerState<DiaryDraftView> createState() => _DiaryDraftViewState();
}

class _DiaryDraftViewState extends ConsumerState<DiaryDraftView> {
  final _answerCtrls = <TextEditingController>[];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(diaryDraftProvider.notifier).start(place: widget.contextPlace);
    });
  }

  @override
  void dispose() {
    for (final c in _answerCtrls) {
      c.dispose();
    }
    super.dispose();
  }

  void _ensureControllers(int count) {
    while (_answerCtrls.length < count) {
      _answerCtrls.add(TextEditingController());
    }
    while (_answerCtrls.length > count) {
      _answerCtrls.removeLast().dispose();
    }
  }

  String _resolvePetName() {
    final auth = ref.read(authProvider);
    if (auth is AuthAuthenticated) {
      return auth.user.primaryPet?.name ?? '아이';
    }
    return '아이';
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(diaryDraftProvider);
    final notifier = ref.read(diaryDraftProvider.notifier);

    if (state.error != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        Fluttertoast.showToast(msg: state.error!);
      });
    }

    return switch (state.phase) {
      DiaryDraftPhase.typeSelect => _TypeSelector(
        onSelected: notifier.selectType,
      ),
      DiaryDraftPhase.mainQuestions => _Questions(
        state: state,
        petName: _resolvePetName(),
        controllers: _answerCtrls,
        ensureControllers: _ensureControllers,
        onAnswerChanged: notifier.setAnswer,
        onNext: notifier.goEmotion,
      ),
      DiaryDraftPhase.emotionSelect => _EmotionSelector(
        state: state,
        onSelected: notifier.selectEmotion,
        onGenerate: notifier.generate,
      ),
      DiaryDraftPhase.generating => const _LoadingPanel(
        message: 'AI 가 일기를 만들고 있어요...',
      ),
      DiaryDraftPhase.result => _ResultPanel(
        state: state,
        onRegenerateImage: notifier.generateImage,
        onSave: () async {
          final ok = await notifier.saveDiary();
          if (ok && context.mounted) {
            Fluttertoast.showToast(msg: '일기가 저장됐어요 🐾');
            widget.onCompleted?.call();
          }
        },
      ),
      DiaryDraftPhase.saving => const _LoadingPanel(message: '저장 중...'),
      DiaryDraftPhase.saved => _ResultPanel(
        state: state,
        onRegenerateImage: notifier.generateImage,
        onSave: null, // 이미 저장됨
      ),
    };
  }
}

class _TypeSelector extends StatelessWidget {
  const _TypeSelector({required this.onSelected});

  final ValueChanged<DiaryType> onSelected;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const Text(
          '오늘의 하루를 어떤 유형으로 기록할까요?',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: AppColors.darkBrown,
          ),
        ),
        const SizedBox(height: 16),
        for (final type in DiaryType.all)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: () => onSelected(type),
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  border: Border.all(color: AppColors.beige),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  children: [
                    Text(type.icon, style: const TextStyle(fontSize: 28)),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            type.label,
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              color: AppColors.darkBrown,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            type.description,
                            style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.subBrown2,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Icon(
                      LucideIcons.chevronRight,
                      color: AppColors.mutedForeground,
                    ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _Questions extends StatelessWidget {
  const _Questions({
    required this.state,
    required this.petName,
    required this.controllers,
    required this.ensureControllers,
    required this.onAnswerChanged,
    required this.onNext,
  });

  final DiaryDraftState state;
  final String petName;
  final List<TextEditingController> controllers;
  final void Function(int) ensureControllers;
  final void Function(int, String) onAnswerChanged;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    final type = state.diaryType;
    if (type == null) return const SizedBox.shrink();
    ensureControllers(type.questions.length);
    // 컨트롤러와 state 동기화 (초기 로드 시)
    for (var i = 0; i < type.questions.length; i++) {
      if (controllers[i].text != state.mainAnswers.elementAtOrNull(i)) {
        final value = state.mainAnswers.elementAtOrNull(i) ?? '';
        if (controllers[i].text != value) {
          controllers[i].text = value;
        }
      }
    }
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Row(
          children: [
            Text(type.icon, style: const TextStyle(fontSize: 24)),
            const SizedBox(width: 8),
            Text(
              type.label,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: AppColors.darkBrown,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        for (var i = 0; i < type.questions.length; i++) ...[
          Text(
            type.questions[i].replaceAll('{petName}', petName),
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: AppColors.darkBrown,
            ),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: controllers[i],
            minLines: 2,
            maxLines: 4,
            onChanged: (v) => onAnswerChanged(i, v),
            decoration: const InputDecoration(hintText: '답변을 입력해주세요'),
          ),
          const SizedBox(height: 16),
        ],
        FilledButton(
          onPressed: state.hasAnswered ? onNext : null,
          style: FilledButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
          child: const Text('다음 — 감정 선택'),
        ),
      ],
    );
  }
}

class _EmotionSelector extends StatelessWidget {
  const _EmotionSelector({
    required this.state,
    required this.onSelected,
    required this.onGenerate,
  });

  final DiaryDraftState state;
  final ValueChanged<DiaryEmotion> onSelected;
  final VoidCallback onGenerate;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const Text(
          '오늘 하루의 감정은 어땠나요?',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: AppColors.darkBrown,
          ),
        ),
        const SizedBox(height: 16),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final e in DiaryEmotion.all)
              ChoiceChip(
                label: Text('${e.emoji} ${e.label}'),
                selected: state.selectedEmotion?.emoji == e.emoji,
                onSelected: (_) => onSelected(e),
                selectedColor: AppColors.peach,
              ),
          ],
        ),
        const SizedBox(height: 24),
        FilledButton.icon(
          onPressed: state.selectedEmotion == null ? null : onGenerate,
          icon: const Icon(LucideIcons.sparkles, size: 18),
          label: const Text('AI 일기 생성하기'),
          style: FilledButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
        ),
      ],
    );
  }
}

class _ResultPanel extends StatelessWidget {
  const _ResultPanel({
    required this.state,
    required this.onRegenerateImage,
    required this.onSave,
  });

  final DiaryDraftState state;
  final VoidCallback onRegenerateImage;
  final VoidCallback? onSave;

  @override
  Widget build(BuildContext context) {
    final generated = state.generated;
    if (generated == null) {
      return const Center(child: Text('생성 결과가 없습니다.'));
    }
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text(
          generated.title,
          // React commit 033a2db 정합성 — 다이어리 영역은 손글씨 폰트 (Gaegu).
          style: GoogleFonts.gaegu(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: AppColors.darkBrown,
          ),
        ),
        const SizedBox(height: 12),
        if (state.imageBase64 != null)
          ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: Image.memory(base64Decode(state.imageBase64!)),
          )
        else
          Container(
            height: 180,
            decoration: BoxDecoration(
              color: AppColors.peach,
              borderRadius: BorderRadius.circular(16),
            ),
            alignment: Alignment.center,
            child: TextButton.icon(
              onPressed: onRegenerateImage,
              icon: const Icon(LucideIcons.image, color: AppColors.brandOrange),
              label: const Text(
                'AI 그림 그리기',
                style: TextStyle(color: AppColors.brandOrange),
              ),
            ),
          ),
        const SizedBox(height: 16),
        Text(
          generated.content,
          style: GoogleFonts.gaegu(
            fontSize: 16,
            color: AppColors.darkBrown,
            height: 1.7,
          ),
        ),
        if (generated.summary.isNotEmpty) ...[
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.peach,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              children: [
                const Icon(
                  LucideIcons.sparkles,
                  size: 14,
                  color: AppColors.brandOrange,
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    generated.summary,
                    style: GoogleFonts.gaegu(
                      fontSize: 12,
                      color: AppColors.brandOrange,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
        const SizedBox(height: 24),
        if (onSave != null)
          FilledButton.icon(
            onPressed: onSave,
            icon: const Icon(LucideIcons.save, size: 18),
            label: const Text('이 일기 저장하기'),
            style: FilledButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
          )
        else
          OutlinedButton(
            onPressed: () => Navigator.of(context).maybePop(),
            child: const Text('닫기'),
          ),
      ],
    );
  }
}

class _LoadingPanel extends StatelessWidget {
  const _LoadingPanel({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(),
          const SizedBox(height: 16),
          Text(message, style: const TextStyle(color: AppColors.subBrown2)),
        ],
      ),
    );
  }
}
