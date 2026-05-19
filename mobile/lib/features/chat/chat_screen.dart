import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/router/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/models/pet.dart';
import '../../shared/models/place.dart';
import '../auth/auth_providers.dart';
import '../diary/diary_types.dart';
import '../home/home_tab_index.dart';
import '../places/map_focus_provider.dart';
import '../places/place_providers.dart';
import '../places/widgets/facility_modal_sheet.dart';
import '../mypage/widgets/primary_pet_change_modal.dart';
import '../onboarding/onboarding_providers.dart';
import 'chat_history_drawer.dart';
import 'chat_providers.dart';
import 'chat_state.dart';

// ── 챗봇 전용 색상 팔레트 ──────────────────────────────────────────────────────
class _CC {
  const _CC._();

  static const bg          = Color(0xFFFFF8F3); // 크림/베이지 배경
  static const primary     = Color(0xFFFF7A4D); // 주황
  static const primaryDark = Color(0xFFFF6B3D); // 진한 주황
  static const border      = Color(0xFFFFD2C2); // 연한 주황 border
  static const card        = Colors.white;
}

// ── ChatScreen ────────────────────────────────────────────────────────────────
class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _inputCtrl  = TextEditingController();
  final _scrollCtrl = ScrollController();
  bool _diarySaved = false;

  @override
  void dispose() {
    _inputCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  // ── 헬퍼 ──────────────────────────────────────────────────────────────────

  String _petName(dynamic auth) {
    if (auth is AuthAuthenticated) {
      return auth.user.primaryPet?.name ?? '반려견';
    }
    return '반려견';
  }

  // ── 액션 ──────────────────────────────────────────────────────────────────

  Future<void> _send([String? overrideText]) async {
    final text = (overrideText ?? _inputCtrl.text).trim();
    if (text.isEmpty) return;

    if (text == '일기 쓰기') { _triggerDiaryFlow(); return; }
    if (text == '일기 새로 쓰기') {
      ref.read(chatProvider.notifier).resetForNewRoom();
      return;
    }
    // 자유채팅 일기 인라인 버튼 가로채기
    if (text == '그림일기로 만들어줘') {
      _handleDiaryImageButton();
      return;
    }
    if (text == '일기 다시 쓰고 싶어') {
      _triggerDiaryFlow();
      return;
    }
    // 사진 일러스트 → 일기 작성 플로우 진입
    if (text == '응 일기 쓸래') {
      _startPhotoDiaryFlow();
      return;
    }

    if (overrideText == null) _inputCtrl.clear();

    final chatState = ref.read(chatProvider);
    final auth      = ref.read(authProvider);

    if (chatState.phase == ChatPhase.mainQuestions) {
      ref.read(chatProvider.notifier).submitMainAnswer(text, _petName(auth));
      _scrollToBottom();
      return;
    }

    if (chatState.phase == ChatPhase.additionalQuestions) {
      ref.read(chatProvider.notifier).submitAdditionalAnswer(text, _petName(auth));
      _scrollToBottom();
      return;
    }

    final petId = auth is AuthAuthenticated
        ? auth.user.primaryPetId ?? auth.user.primaryPet?.id
        : null;
    final outcome = await ref
        .read(chatProvider.notifier)
        .sendUserMessage(text, petId: petId);
    _scrollToBottom();

    if (outcome == ChatTurnOutcome.triggerDiary) {
      if (mounted) _triggerDiaryFlow();
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

  void _startDiaryMiniFlow() {
    setState(() => _diarySaved = false);
    final auth = ref.read(authProvider);
    ref.read(chatProvider.notifier).startDiaryFlow(_petName(auth));
    _scrollToBottom();
  }

  void _triggerDiaryFlow() {
    setState(() => _diarySaved = false);
    final auth = ref.read(authProvider);
    ref.read(chatProvider.notifier).triggerDiaryFlow(_petName(auth));
    _scrollToBottom();
  }

  /// "그림일기로 만들어줘" 인라인 버튼 처리.
  /// mini-flow (generatedDiary 있음) → 클라이언트 이미지 생성
  /// 자유채팅 (generatedDiary 없음) → 백엔드 이미지 생성 + 자동 저장
  Future<void> _handleDiaryImageButton() async {
    setState(() => _diarySaved = false);
    final chatState = ref.read(chatProvider);
    if (chatState.generatedDiary != null) {
      // mini-flow: 기존 클라이언트 사이드 이미지 생성
      ref.read(chatProvider.notifier).generateDiaryImageInChat();
    } else {
      // 자유채팅: 백엔드가 이미지 생성 + 자동 저장
      final auth = ref.read(authProvider);
      final petId = auth is AuthAuthenticated
          ? auth.user.primaryPetId ?? auth.user.primaryPet?.id
          : null;
      await ref.read(chatProvider.notifier).sendDiaryImageRequest(petId: petId);
    }
    _scrollToBottom();
  }

  /// 사진 일러스트 → 일기 작성 플로우 진입.
  /// 기존 다이어리 미니플로우를 그대로 사용하되, photoStyleImageUrl 유지.
  void _startPhotoDiaryFlow() {
    setState(() => _diarySaved = false);
    final auth = ref.read(authProvider);
    ref.read(chatProvider.notifier).startPhotoDiaryFlow(_petName(auth));
    _scrollToBottom();
  }

  void _openPetPicker(AuthAuthenticated auth) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => PrimaryPetChangeModal(user: auth.user),
    );
  }

  void _openMapTab()     => ref.read(homeTabIndexProvider.notifier).state = 2;
  void _openDiaryDraft() => context.push(AppRoutes.diaryDraft);
  void _goToLogin()      => ref.read(homeTabIndexProvider.notifier).state = 3;

  Future<void> _pickAndSendPhoto() async {
    final chatState = ref.read(chatProvider);
    if (chatState.isSending) return;

    final picker = ImagePicker();
    final picked = await picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 1920,
      maxHeight: 1920,
      imageQuality: 85,
    );
    if (picked == null) return;

    // 5MB 사전 검증
    final fileSize = await File(picked.path).length();
    if (fileSize > 5 * 1024 * 1024) {
      Fluttertoast.showToast(msg: '5MB 이하 이미지만 업로드할 수 있어요');
      return;
    }

    await ref.read(chatProvider.notifier).sendPhotoStyle(picked.path);
    _scrollToBottom();
  }

  void _focusPlaceOnMap(PlaceCard place) {
    ref.read(mapFocusProvider.notifier).requestFocus(place);
    ref.read(homeTabIndexProvider.notifier).state = 2;
  }

  Future<void> _focusPlaceByName(String name) async {
    try {
      final facility = await ref.read(placeApiProvider).byName(name);
      final place = PlaceCard(
        name: facility.name,
        address: facility.address,
        category: facility.category,
        subCategory: facility.subCategory,
        contentId: facility.contentId,
        lat: facility.lat,
        lng: facility.lng,
        tel: facility.tel,
        conditions: facility.conditions,
        hasParking: facility.hasParking,
        operation: facility.operation,
        indoor: facility.indoor,
        outdoor: facility.outdoor,
        description: facility.description,
      );
      if (!mounted) return;
      ref.read(mapFocusProvider.notifier).requestFocus(place);
      ref.read(homeTabIndexProvider.notifier).state = 2;
    } catch (_) {
      if (mounted) Fluttertoast.showToast(msg: '장소 정보를 찾을 수 없어요');
    }
  }

  // ── 다이어리 액션 패널 ────────────────────────────────────────────────────

  Widget _buildActionPanel(ChatState state, String petName) {
    switch (state.phase) {
      case ChatPhase.typeSelect:
        return _DiaryTypePanel(
          onSelect: (type) {
            ref.read(chatProvider.notifier).selectDiaryType(type, petName);
            _scrollToBottom();
          },
        );
      case ChatPhase.additionalPrompt:
        return _AdditionalPromptPanel(
          onAccept: () {
            ref.read(chatProvider.notifier).respondToAdditionalPrompt(true, petName);
            _scrollToBottom();
          },
          onDecline: () {
            ref.read(chatProvider.notifier).respondToAdditionalPrompt(false, petName);
            _scrollToBottom();
          },
        );
      case ChatPhase.emotionSelect:
        return _EmotionPanel(
          onSelect: (emotion) {
            ref.read(chatProvider.notifier).selectDiaryEmotion(emotion, petName);
            _scrollToBottom();
          },
        );
      case ChatPhase.textDiaryResult:
        final hasPhotoIllustration = state.photoStyleImageUrl != null;
        return _TextDiaryResultPanel(
          isSending: state.isSending,
          isPhotoDiary: hasPhotoIllustration,
          onGenerateImage: hasPhotoIllustration
              ? () async {
                  // 사진 일러스트를 그대로 사용하여 저장
                  final ok = await ref
                      .read(chatProvider.notifier)
                      .saveDiaryFromChat();
                  if (ok) setState(() => _diarySaved = true);
                  _scrollToBottom();
                }
              : () {
                  ref.read(chatProvider.notifier).generateDiaryImageInChat();
                  _scrollToBottom();
                },
          onRestart: () {
            ref.read(chatProvider.notifier).restartDiaryFlow(petName);
            _scrollToBottom();
          },
        );
      case ChatPhase.diaryResult:
        // diaryResult 는 채팅 리스트 안 인라인 말풍선으로 표시
        return const SizedBox.shrink();
      default:
        return const SizedBox.shrink();
    }
  }

  // ── 채팅 리스트 ───────────────────────────────────────────────────────────

  Widget _buildChatList(ChatState state, bool isAuth) {
    final msgs       = state.messages;
    final hasMessages = msgs.isNotEmpty;
    final showDiaryCard = state.phase == ChatPhase.diaryResult;

    int headerCount = 2;
    if (!isAuth) {
      headerCount += 2;
    } else if (!hasMessages) {
      headerCount += 1;
    }

    final totalCount = headerCount + msgs.length + (showDiaryCard ? 1 : 0);

    return ListView.builder(
      controller: _scrollCtrl,
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 16),
      itemCount: totalCount,
      itemBuilder: (_, i) {
        if (i == 0) {
          return const Padding(
            padding: EdgeInsets.only(bottom: 10),
            child: _WelcomeBubble(
              text: '안녕하세요! 저는 우리 아이의 반짝이는 하루와 소중한 추억을 차곡차곡 담아드리는 AI 멍봇이에요.'
                  ' 추억을 함께 기록하고, 어울리는 장소도 추천해드릴게요.',
            ),
          );
        }
        if (i == 1) {
          return const Padding(
            padding: EdgeInsets.only(bottom: 16),
            child: _WelcomeBubble(text: '오늘은 어떤 하루를 남겨볼까요?'),
          );
        }
        if (!isAuth) {
          if (i == 2) {
            return const Padding(
              padding: EdgeInsets.only(bottom: 16),
              child: _LockMessageBubble(),
            );
          }
          if (i == 3) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 16, left: 52),
              child: Align(
                alignment: Alignment.centerLeft,
                child: FilledButton.icon(
                  onPressed: _goToLogin,
                  icon: const Icon(LucideIcons.logIn, size: 16),
                  label: const Text('로그인 하러 가기'),
                  style: FilledButton.styleFrom(
                    backgroundColor: _CC.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 10),
                    minimumSize: Size.zero,
                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    shape: const StadiumBorder(),
                  ),
                ),
              ),
            );
          }
        }
        if (isAuth && !hasMessages && i == 2) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 16, left: 52),
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _QuickChip(
                  label: '그림일기',
                  icon: LucideIcons.pencil,
                  onTap: _startDiaryMiniFlow,
                ),
                _QuickChip(
                  label: '장소 추천',
                  icon: LucideIcons.mapPin,
                  onTap: () => _send('장소 추천'),
                ),
              ],
            ),
          );
        }
        final msgIdx = i - headerCount;

        // 마지막 아이템: 인라인 그림일기 결과 카드
        if (showDiaryCard && msgIdx == msgs.length) {
          final auth = ref.read(authProvider);
          final petName = _petName(auth);
          return _DiaryResultBubble(
            state: state,
            petName: petName,
            saved: _diarySaved,
            onRestart: () {
              setState(() => _diarySaved = false);
              ref.read(chatProvider.notifier).restartDiaryFlow(petName);
              _scrollToBottom();
            },
            onSave: () async {
              if (state.diaryAutoSaved) {
                if (mounted) {
                  setState(() => _diarySaved = true);
                  Fluttertoast.showToast(msg: '일기가 저장됐어요!');
                }
                return;
              }
              final ok = await ref.read(chatProvider.notifier).saveDiaryFromChat();
              if (ok && mounted) {
                setState(() => _diarySaved = true);
                Fluttertoast.showToast(msg: '일기가 저장됐어요!');
              } else if (!ok && mounted) {
                final err = ref.read(chatProvider).error;
                if (err != null) Fluttertoast.showToast(msg: err);
              }
            },
            onGoToDiary: () {
              ref.read(homeTabIndexProvider.notifier).state = 1;
            },
          );
        }

        return _BubbleView(
          bubble: msgs[msgIdx],
          onTapButton: _send,
          onOpenMap: _openMapTab,
          onOpenDiary: _openDiaryDraft,
          onPlaceTapToMap: _focusPlaceOnMap,
          onPlaceNameTap: _focusPlaceByName,
        );
      },
    );
  }

  // ── build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    // 홈 미니 챗봇에서 전달된 텍스트 → 바로 전송
    ref.listen<String?>(pendingChatTextProvider, (prev, next) {
      if (next != null && next.isNotEmpty) {
        ref.read(pendingChatTextProvider.notifier).state = null;
        _send(next);
      }
    });

    // 지도탭 장소 카드 → 챗봇 일기 작성 플로우 자동 진입
    ref.listen<PlaceCard?>(pendingPlaceProvider, (prev, next) {
      if (next != null) {
        setState(() => _diarySaved = false);
        final auth0 = ref.read(authProvider);
        ref.read(chatProvider.notifier).startDiaryFlowWithPlace(
              _petName(auth0),
              next,
            );
        ref.read(pendingPlaceProvider.notifier).state = null;
        _scrollToBottom();
      }
    });

    final state  = ref.watch(chatProvider);
    final auth   = ref.watch(authProvider);
    final isAuth = auth is AuthAuthenticated;
    final authUser = auth is AuthAuthenticated ? auth : null;
    final pet    = authUser?.user.primaryPet;
    final petName = pet?.name ?? '반려견';

    // subtitle: "이름 · 견종" 형태 or 기본 문구
    final pets = isAuth ? ref.watch(userPetsProvider) : null;
    final petList = pets?.valueOrNull ?? const <Pet>[];
    final hasManyPets = petList.length > 1;
    final subtitle = pet != null
        ? '${pet.name} · ${pet.breedName ?? '반려견'}'
        : '반려견 AI 도우미';

    final showComposer = state.phase == ChatPhase.welcome ||
        state.phase == ChatPhase.mainQuestions ||
        state.phase == ChatPhase.additionalQuestions;
    final composerHint = (state.phase == ChatPhase.mainQuestions ||
            state.phase == ChatPhase.additionalQuestions)
        ? '답변을 입력해주세요...'
        : null;

    return Scaffold(
      backgroundColor: _CC.bg,
      resizeToAvoidBottomInset: false,
      drawer: const ChatHistoryDrawer(),
      appBar: AppBar(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.white,
        foregroundColor: AppColors.darkBrown,
        elevation: 0,
        scrolledUnderElevation: 0,
        toolbarHeight: 64,
        automaticallyImplyLeading: false,
        titleSpacing: 12,
        // 왼쪽: 챗봇 아이콘 + "AI 멍봇" + 부제목
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image.asset(
              'assets/icon/chatbot_logo.png',
              width: 44,
              height: 44,
            ),
            const SizedBox(width: 10),
            Flexible(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'AI 멍봇',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: AppColors.darkBrown,
                    ),
                  ),
                  GestureDetector(
                    onTap: (authUser != null && hasManyPets)
                        ? () => _openPetPicker(authUser)
                        : null,
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Flexible(
                          child: Text(
                            subtitle,
                            style: const TextStyle(
                              fontSize: 11,
                              color: AppColors.subBrown2,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (isAuth && hasManyPets) ...[
                          const SizedBox(width: 3),
                          const Icon(
                            LucideIcons.chevronDown,
                            size: 12,
                            color: AppColors.subBrown2,
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        // 오른쪽: "+ 새 채팅" (outline) + "채팅 기록" (filled)
        actions: [
          Builder(
            builder: (ctx) => Padding(
              padding: const EdgeInsets.only(right: 12),
              child: FittedBox(
                fit: BoxFit.scaleDown,
                alignment: Alignment.centerRight,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    _PillButton.outline(
                      label: '+ 새 채팅',
                      onTap: () => ref
                          .read(chatProvider.notifier)
                          .resetForNewRoom(),
                    ),
                    const SizedBox(width: 8),
                    _PillButton.filled(
                      label: '채팅 기록',
                      onTap: () => Scaffold.of(ctx).openDrawer(),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
        bottom: const PreferredSize(
          preferredSize: Size.fromHeight(1),
          child: Divider(
            height: 1,
            color: Color(0xFFFFE8DC),
          ),
        ),
      ),
      body: Column(
        children: [
          Expanded(child: _buildChatList(state, isAuth)),
          // 다이어리 미니 플로우 패널
          if (isAuth) _buildActionPanel(state, petName),
          // 전송 진행 표시
          if (state.isSending)
            LinearProgressIndicator(
              minHeight: 2,
              backgroundColor: _CC.bg,
              valueColor: const AlwaysStoppedAnimation<Color>(_CC.primary),
            ),
          // 입력창
          if (showComposer)
            _Composer(
              controller: _inputCtrl,
              onSubmit: () => _send(),
              disabled: state.isSending,
              locked: !isAuth,
              hintText: composerHint,
              onImagePick: isAuth ? _pickAndSendPhoto : null,
            ),
        ],
      ),
    );
  }
}

// ── AppBar 좌측 타이틀 ──────────────────────────────────────────────────────────
// (build 메서드에 인라인으로 두면 rebuild 비용이 높아서 분리)
//  → 실제로는 _ChatScreenState.build 에 인라인 구현됨. 아래는 참고용.

// ── Pill 버튼 (상단 헤더 전용) ─────────────────────────────────────────────────
class _PillButton extends StatelessWidget {
  const _PillButton._({
    required this.label,
    required this.onTap,
    required this.filled,
  });

  factory _PillButton.outline({
    required String label,
    required VoidCallback onTap,
  }) =>
      _PillButton._(label: label, onTap: onTap, filled: false);

  factory _PillButton.filled({
    required String label,
    required VoidCallback onTap,
  }) =>
      _PillButton._(label: label, onTap: onTap, filled: true);

  final String label;
  final VoidCallback onTap;
  final bool filled;

  @override
  Widget build(BuildContext context) {
    const textStyle = TextStyle(fontSize: 12, fontWeight: FontWeight.w600);
    const shape     = StadiumBorder();
    const padding   = EdgeInsets.symmetric(horizontal: 12, vertical: 7);

    if (filled) {
      return FilledButton(
        onPressed: onTap,
        style: FilledButton.styleFrom(
          backgroundColor: _CC.primary,
          foregroundColor: Colors.white,
          padding: padding,
          shape: shape,
          minimumSize: Size.zero,
          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        ),
        child: Text(label, style: textStyle),
      );
    }
    return OutlinedButton(
      onPressed: onTap,
      style: OutlinedButton.styleFrom(
        foregroundColor: _CC.primary,
        side: const BorderSide(color: _CC.primary),
        padding: padding,
        shape: shape,
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        backgroundColor: Colors.white,
      ),
      child: Text(label, style: textStyle),
    );
  }
}

// ── 웰컴 말풍선 ───────────────────────────────────────────────────────────────
class _WelcomeBubble extends StatelessWidget {
  const _WelcomeBubble({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 2),
          child: Image.asset(
            'assets/icon/chatbot_logo.png',
            width: 44,
            height: 44,
          ),
        ),
        const SizedBox(width: 8),
        Flexible(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: _CC.card,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(4),
                topRight: Radius.circular(20),
                bottomLeft: Radius.circular(20),
                bottomRight: Radius.circular(20),
              ),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFFFF7A4D).withValues(alpha: 0.08),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Text(
              text,
              style: const TextStyle(
                fontSize: 14,
                color: AppColors.darkBrown,
                height: 1.6,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

// ── 로그인 유도 말풍선 ─────────────────────────────────────────────────────────
class _LockMessageBubble extends StatelessWidget {
  const _LockMessageBubble();

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 2),
          child: Image.asset(
            'assets/icon/chatbot_logo.png',
            width: 44,
            height: 44,
          ),
        ),
        const SizedBox(width: 8),
        Flexible(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: _CC.card,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(4),
                topRight: Radius.circular(20),
                bottomLeft: Radius.circular(20),
                bottomRight: Radius.circular(20),
              ),
              border: Border.all(color: _CC.border),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFFFF7A4D).withValues(alpha: 0.06),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: const Text(
              '🔒 로그인 후 이용 가능한 서비스예요.\n로그인하고 우리 아이의 일기와 장소 추천을 함께 만들어봐요!',
              style: TextStyle(
                fontSize: 14,
                color: AppColors.darkBrown,
                height: 1.6,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

// ── 퀵 액션 칩 (아이콘 + 주황 outline) ────────────────────────────────────────
class _QuickChip extends StatelessWidget {
  const _QuickChip({
    required this.label,
    required this.icon,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(999),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: _CC.primary),
          borderRadius: BorderRadius.circular(999),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 14, color: _CC.primary),
            const SizedBox(width: 6),
            Text(
              label,
              style: const TextStyle(
                fontSize: 13,
                color: _CC.primary,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── 채팅 말풍선 컨테이너 ──────────────────────────────────────────────────────
class _BubbleView extends StatelessWidget {
  const _BubbleView({
    required this.bubble,
    required this.onTapButton,
    required this.onOpenMap,
    required this.onOpenDiary,
    required this.onPlaceTapToMap,
    required this.onPlaceNameTap,
  });

  final ChatBubble bubble;
  final ValueChanged<String> onTapButton;
  final VoidCallback onOpenMap;
  final VoidCallback onOpenDiary;
  final ValueChanged<PlaceCard> onPlaceTapToMap;
  final ValueChanged<String> onPlaceNameTap;

  @override
  Widget build(BuildContext context) {
    final isUser = bubble.isUser;
    final bubbleMaxWidth =
        MediaQuery.of(context).size.width * (isUser ? 0.78 : 0.80);

    final bubbleColumn = ConstrainedBox(
      constraints: BoxConstraints(maxWidth: bubbleMaxWidth),
      child: Column(
        crossAxisAlignment:
            isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          if (bubble.text.isNotEmpty)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: isUser ? _CC.primary : _CC.card,
                borderRadius: isUser
                    ? const BorderRadius.only(
                        topLeft:     Radius.circular(20),
                        topRight:    Radius.circular(4),
                        bottomLeft:  Radius.circular(20),
                        bottomRight: Radius.circular(20),
                      )
                    : const BorderRadius.only(
                        topLeft:     Radius.circular(4),
                        topRight:    Radius.circular(20),
                        bottomLeft:  Radius.circular(20),
                        bottomRight: Radius.circular(20),
                      ),
                boxShadow: isUser
                    ? null
                    : [
                        BoxShadow(
                          color: const Color(0xFFFF7A4D).withValues(alpha: 0.08),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
              ),
              child: _BubbleText(
                text: bubble.text,
                isUser: isUser,
                places: !isUser ? bubble.places : null,
                onPlaceTap: onPlaceTapToMap,
                onPlaceNameTap: onPlaceNameTap,
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
                  'assets/icon/chatbot_logo.png',
                  width: 44,
                  height: 44,
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

// ── 인라인 버튼 (다이어리 플로우 등) ─────────────────────────────────────────
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
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              backgroundColor: _CC.primary,
              shape: const StadiumBorder(),
            ),
            child: Text(label),
          )
        : OutlinedButton(
            onPressed: onTap,
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              side: const BorderSide(color: _CC.border),
              foregroundColor: AppColors.subBrown2,
              shape: const StadiumBorder(),
            ),
            child: Text(label),
          );
  }
}

// ── 말풍선 텍스트 렌더러 ──────────────────────────────────────────────────────
class _BubbleText extends StatelessWidget {
  const _BubbleText({
    required this.text,
    required this.isUser,
    this.places,
    required this.onPlaceTap,
    required this.onPlaceNameTap,
  });

  final String text;
  final bool isUser;
  final List<PlaceCard>? places;
  final ValueChanged<PlaceCard> onPlaceTap;
  final ValueChanged<String> onPlaceNameTap;

  static final _hideLinePatterns = <RegExp>[
    RegExp(r'^_요약_:'),
    RegExp(r'^[-\s]*_id\s*[:=]', caseSensitive: false),
    RegExp(r'^[-\s]*_?score\s*[:=]', caseSensitive: false),
    RegExp(r'^[-\s]*content_id\s*[:=]', caseSensitive: false),
    RegExp(r'^[-\s]*session_id\s*[:=]', caseSensitive: false),
    RegExp(r'^[-\s]*image_prompt', caseSensitive: false),
  ];

  static final _imageMarkdownRegex = RegExp(
    r'^!\[(.*?)\]\(((?:https?|file):\/\/[^\)]+)\)',
  );

  static final _placeLineRegex = RegExp(
    r'^(\d+)[.)]\s*(?:\*\*)?(.+?)(?:\*\*)?\s*(?:📍\s*)?$',
  );

  /// 텍스트에 "주소:" 패턴이 있으면 장소 추천 메시지로 간주 (채팅 기록 복원 시).
  static final _addressPattern = RegExp(r'주소:');

  @override
  Widget build(BuildContext context) {
    final color    = isUser ? Colors.white : AppColors.darkBrown;
    final placeMap = <String, PlaceCard>{
      for (final p in places ?? const <PlaceCard>[]) p.name: p,
    };

    final lines = text
        .split('\n')
        .where((l) => !_hideLinePatterns.any((re) => re.hasMatch(l.trim())))
        .toList();

    // placeMap 비어 있으면 텍스트 기반으로 장소 메시지 여부 판별 (기록 복원).
    final isPlaceMsg = placeMap.isEmpty && _addressPattern.hasMatch(text);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < lines.length; i++)
          _renderLine(
            context,
            lines[i],
            color,
            placeMap,
            isPlaceMessage: isPlaceMsg,
            isLast: i == lines.length - 1,
          ),
      ],
    );
  }

  Widget _renderLine(
    BuildContext context,
    String line,
    Color color,
    Map<String, PlaceCard> placeMap, {
    required bool isPlaceMessage,
    required bool isLast,
  }) {
    final padding = EdgeInsets.only(bottom: isLast ? 0 : 4);

    final imgMatch = _imageMarkdownRegex.firstMatch(line.trim());
    if (imgMatch != null) {
      final url = imgMatch.group(2)!;
      final isLocalFile = url.startsWith('file://');
      return Padding(
        padding: padding,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: isLocalFile
              ? Image.file(
                  File(url.replaceFirst('file://', '')),
                  fit: BoxFit.cover,
                  width: double.infinity,
                  errorBuilder: (_, _, _) => const SizedBox.shrink(),
                )
              : Image.network(
                  url,
                  fit: BoxFit.cover,
                  errorBuilder: (_, _, _) => const SizedBox.shrink(),
                ),
        ),
      );
    }

    final placeMatch = _placeLineRegex.firstMatch(line);
    if (placeMatch != null) {
      final num  = placeMatch.group(1)!;
      final name = placeMatch.group(2)!.trim();

      // 1순위: placeMap 에서 PlaceCard 매칭 (현재 대화)
      if (placeMap.isNotEmpty) {
        final place = placeMap[name] ?? _bestMatch(name, placeMap);
        if (place != null) {
          return _placeLinkWidget(padding, num, name, () => onPlaceTap(place));
        }
      }

      // 2순위: 장소 메시지인데 placeMap 없음 (채팅 기록) → 이름으로 검색
      if (isPlaceMessage) {
        return _placeLinkWidget(padding, num, name, () => onPlaceNameTap(name));
      }
    }

    return Padding(
      padding: padding,
      child: RichText(
        text: TextSpan(
          style: TextStyle(fontSize: 14, color: color, height: 1.6),
          children: _boldSpans(line, color),
        ),
      ),
    );
  }

  Widget _placeLinkWidget(
    EdgeInsets padding,
    String num,
    String name,
    VoidCallback onTap,
  ) {
    return Padding(
      padding: padding,
      child: InkWell(
        onTap: onTap,
        child: RichText(
          text: TextSpan(
            style: const TextStyle(
              fontSize: 14,
              color: _CC.primary,
              fontWeight: FontWeight.w600,
              decoration: TextDecoration.underline,
              decorationColor: _CC.primary,
              height: 1.5,
            ),
            children: [TextSpan(text: '$num. $name 📍')],
          ),
        ),
      ),
    );
  }

  PlaceCard? _bestMatch(String name, Map<String, PlaceCard> placeMap) {
    for (final entry in placeMap.entries) {
      if (entry.key.contains(name) || name.contains(entry.key)) {
        return entry.value;
      }
    }
    return null;
  }

  List<TextSpan> _boldSpans(String line, Color color) {
    final spans   = <TextSpan>[];
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
    if (spans.isEmpty) {
      return [TextSpan(text: line, style: TextStyle(color: color))];
    }
    return spans;
  }
}

// ── 장소 카드 요약 ──────────────────────────────────────────────────────────
class _FacilityCardSummary extends StatelessWidget {
  const _FacilityCardSummary({required this.facility});

  final FacilityCard facility;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(14),
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
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: _CC.border),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFFFF7A4D).withValues(alpha: 0.06),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: _CC.bg,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                LucideIcons.building2,
                color: _CC.primary,
                size: 18,
              ),
            ),
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

// ── 하단 입력창 ────────────────────────────────────────────────────────────────
class _Composer extends StatelessWidget {
  const _Composer({
    required this.controller,
    required this.onSubmit,
    required this.disabled,
    this.locked = false,
    this.hintText,
    this.onImagePick,
  });

  final TextEditingController controller;
  final VoidCallback onSubmit;
  final bool disabled;
  final bool locked;
  final String? hintText;
  final VoidCallback? onImagePick;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
      decoration: const BoxDecoration(
        color: _CC.bg,
        border: Border(top: BorderSide(color: Color(0xFFFFE8DC))),
      ),
      child: locked
          ? Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: _CC.border),
              ),
              child: const Row(
                children: [
                  Icon(Icons.lock_outline, size: 16, color: _CC.primary),
                  SizedBox(width: 8),
                  Text(
                    '로그인 후 사용 가능합니다',
                    style: TextStyle(color: AppColors.subBrown2, fontSize: 14),
                  ),
                ],
              ),
            )
          : Row(
              children: [
                // 이미지 첨부 버튼 — rounded square, 주황 outline
                InkWell(
                  onTap: disabled ? null : onImagePick,
                  borderRadius: BorderRadius.circular(10),
                  child: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      border: Border.all(color: _CC.border),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(
                      LucideIcons.image,
                      size: 20,
                      color: _CC.primary,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                // 텍스트 입력 — pill 형태, 주황 border
                Expanded(
                  child: TextField(
                    controller: controller,
                    enabled: !disabled,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => onSubmit(),
                    style: const TextStyle(fontSize: 14),
                    decoration: InputDecoration(
                      hintText: hintText ?? '편하게 말씀해주세요...',
                      hintStyle: const TextStyle(
                        color: AppColors.mutedForeground,
                        fontSize: 14,
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 11,
                      ),
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: const BorderSide(color: _CC.border),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: const BorderSide(color: _CC.border),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: const BorderSide(
                            color: _CC.primary, width: 1.5),
                      ),
                      disabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: const BorderSide(color: _CC.border),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                // 전송 버튼 — 라운드 사각형 주황
                GestureDetector(
                  onTap: disabled ? null : onSubmit,
                  child: Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: disabled
                          ? const Color(0xFFFFB49A)
                          : _CC.primary,
                      borderRadius: BorderRadius.circular(14),
                      boxShadow: disabled
                          ? null
                          : [
                              BoxShadow(
                                color: _CC.primary.withValues(alpha: 0.35),
                                blurRadius: 8,
                                offset: const Offset(0, 3),
                              ),
                            ],
                    ),
                    child: const Icon(
                      LucideIcons.send,
                      size: 20,
                      color: Colors.white,
                    ),
                  ),
                ),
              ],
            ),
    );
  }
}

// ── 다이어리 유형 선택 패널 ───────────────────────────────────────────────────
class _DiaryTypePanel extends StatelessWidget {
  const _DiaryTypePanel({required this.onSelect});

  final ValueChanged<DiaryType> onSelect;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: _CC.bg,
        border: Border(top: BorderSide(color: Color(0xFFFFE8DC))),
      ),
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '유형을 선택해주세요',
            style: TextStyle(
              fontSize: 12,
              color: AppColors.subBrown2,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: DiaryType.all
                .map(
                  (type) => Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 4),
                      child: _TypeCard(
                        type: type,
                        onTap: () => onSelect(type),
                      ),
                    ),
                  ),
                )
                .toList(),
          ),
        ],
      ),
    );
  }
}

class _TypeCard extends StatelessWidget {
  const _TypeCard({required this.type, required this.onTap});

  final DiaryType type;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 4),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: _CC.border),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFFFF7A4D).withValues(alpha: 0.07),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(type.icon, style: const TextStyle(fontSize: 22)),
            const SizedBox(height: 4),
            Text(
              type.label,
              style: const TextStyle(
                fontSize: 10,
                color: AppColors.darkBrown,
                fontWeight: FontWeight.w600,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
            ),
          ],
        ),
      ),
    );
  }
}

// ── 감정 선택 패널 ────────────────────────────────────────────────────────────
class _EmotionPanel extends StatelessWidget {
  const _EmotionPanel({required this.onSelect});

  final ValueChanged<DiaryEmotion> onSelect;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: _CC.bg,
        border: Border(top: BorderSide(color: Color(0xFFFFE8DC))),
      ),
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '오늘의 감정을 선택해주세요',
            style: TextStyle(
              fontSize: 12,
              color: AppColors.subBrown2,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: DiaryEmotion.all
                .map((e) => _EmotionChip(
                      emotion: e,
                      onTap: () => onSelect(e),
                    ))
                .toList(),
          ),
        ],
      ),
    );
  }
}

class _EmotionChip extends StatelessWidget {
  const _EmotionChip({required this.emotion, required this.onTap});

  final DiaryEmotion emotion;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: _CC.border),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFFFF7A4D).withValues(alpha: 0.07),
              blurRadius: 4,
              offset: const Offset(0, 1),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(emotion.emoji, style: const TextStyle(fontSize: 15)),
            const SizedBox(width: 5),
            Text(
              emotion.label,
              style: const TextStyle(
                fontSize: 12,
                color: AppColors.darkBrown,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── 추가 질문 여부 패널 ──────────────────────────────────────────────────────
class _AdditionalPromptPanel extends StatelessWidget {
  const _AdditionalPromptPanel({
    required this.onAccept,
    required this.onDecline,
  });

  final VoidCallback onAccept;
  final VoidCallback onDecline;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: _CC.bg,
        border: Border(top: BorderSide(color: Color(0xFFFFE8DC))),
      ),
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
      child: Row(
        children: [
          Expanded(
            child: FilledButton(
              onPressed: onAccept,
              style: FilledButton.styleFrom(
                backgroundColor: _CC.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: const StadiumBorder(),
              ),
              child: const Text('네, 좋아요!',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: OutlinedButton(
              onPressed: onDecline,
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.subBrown2,
                side: const BorderSide(color: _CC.border),
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: const StadiumBorder(),
              ),
              child: const Text('괜찮아요',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
            ),
          ),
        ],
      ),
    );
  }
}

// ── 텍스트 일기 결과 패널 (그림일기로 만들어줘 / 일기 다시 쓰고싶어) ──────────
class _TextDiaryResultPanel extends StatelessWidget {
  const _TextDiaryResultPanel({
    required this.isSending,
    required this.onGenerateImage,
    required this.onRestart,
    this.isPhotoDiary = false,
  });

  final bool isSending;
  final VoidCallback onGenerateImage;
  final VoidCallback onRestart;
  /// true 이면 사진 일러스트를 이미 보유 → "그림일기로 저장하기" 버튼 표시.
  final bool isPhotoDiary;

  @override
  Widget build(BuildContext context) {
    final primaryLabel = isPhotoDiary
        ? (isSending ? '저장하는 중...' : '그림일기로 저장하기')
        : (isSending ? '그림 그리는 중...' : '그림일기로 만들어줘');
    final primaryIcon = isPhotoDiary ? LucideIcons.save : LucideIcons.image;

    return Container(
      decoration: const BoxDecoration(
        color: _CC.bg,
        border: Border(top: BorderSide(color: Color(0xFFFFE8DC))),
      ),
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
      child: Row(
        children: [
          Expanded(
            child: FilledButton.icon(
              onPressed: isSending ? null : onGenerateImage,
              icon: Icon(primaryIcon, size: 14),
              label: Text(
                primaryLabel,
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
              ),
              style: FilledButton.styleFrom(
                backgroundColor: _CC.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: const StadiumBorder(),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: OutlinedButton.icon(
              onPressed: onRestart,
              icon: const Icon(LucideIcons.refreshCcw, size: 14),
              label: const Text('일기 다시 쓰고싶어',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.subBrown2,
                side: const BorderSide(color: _CC.border),
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: const StadiumBorder(),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── 다이어리 결과 인라인 말풍선 (그림 완성 → 이미지 카드 + 저장) ─────────────
class _DiaryResultBubble extends StatelessWidget {
  const _DiaryResultBubble({
    required this.state,
    required this.onRestart,
    required this.onSave,
    required this.onGoToDiary,
    required this.saved,
    required this.petName,
  });

  final ChatState state;
  final VoidCallback onRestart;
  final VoidCallback onSave;
  final VoidCallback onGoToDiary;
  final bool saved;
  final String petName;

  @override
  Widget build(BuildContext context) {
    final diary = state.generatedDiary;
    final bubbleMaxWidth = MediaQuery.of(context).size.width * 0.80;

    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Image.asset(
                'assets/icon/chatbot_logo.png',
                width: 44,
                height: 44,
              ),
            ),
            const SizedBox(width: 8),
            Flexible(
              child: ConstrainedBox(
                constraints: BoxConstraints(maxWidth: bubbleMaxWidth),
                child: Container(
                  decoration: BoxDecoration(
                    color: _CC.card,
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(4),
                      topRight: Radius.circular(20),
                      bottomLeft: Radius.circular(20),
                      bottomRight: Radius.circular(20),
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFFFF7A4D).withValues(alpha: 0.08),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // 제목 영역
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 14, 16, 0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              diary?.title ?? '오늘의 그림일기',
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: AppColors.darkBrown,
                              ),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 2),
                            Text(
                              '$petName와 함께한 하루',
                              style: const TextStyle(
                                fontSize: 12,
                                color: AppColors.subBrown2,
                              ),
                            ),
                          ],
                        ),
                      ),
                      // 이미지 (base64 또는 URL)
                      if (state.imageBase64 != null || state.imageUrl != null)
                        Padding(
                          padding: const EdgeInsets.fromLTRB(12, 10, 12, 0),
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(14),
                            child: Container(
                              color: const Color(0xFFFFF5EF),
                              width: double.infinity,
                              child: state.imageBase64 != null
                                  ? Image.memory(
                                      base64Decode(state.imageBase64!),
                                      fit: BoxFit.contain,
                                    )
                                  : Image.network(
                                      state.imageUrl!,
                                      fit: BoxFit.contain,
                                      errorBuilder: (_, __, ___) =>
                                          const Padding(
                                        padding: EdgeInsets.all(24),
                                        child: Icon(LucideIcons.image,
                                            size: 48,
                                            color: AppColors.subBrown2),
                                      ),
                                    ),
                            ),
                          ),
                        ),
                      // 일기 내용
                      if (diary != null && diary.content.isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.fromLTRB(16, 10, 16, 14),
                          child: Text(
                            diary.content,
                            style: const TextStyle(
                              fontSize: 13,
                              color: AppColors.darkBrown,
                              height: 1.7,
                            ),
                          ),
                        ),
                      // 버튼 영역
                      Padding(
                        padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
                        child: saved
                            ? SizedBox(
                                width: double.infinity,
                                child: FilledButton.icon(
                                  onPressed: onGoToDiary,
                                  icon: const Icon(LucideIcons.bookOpen,
                                      size: 14),
                                  label: const Text('일기장으로 가기',
                                      style: TextStyle(
                                          fontSize: 13,
                                          fontWeight: FontWeight.w600)),
                                  style: FilledButton.styleFrom(
                                    backgroundColor: _CC.primary,
                                    foregroundColor: Colors.white,
                                    padding: const EdgeInsets.symmetric(
                                        vertical: 13),
                                    shape: const StadiumBorder(),
                                  ),
                                ),
                              )
                            : Row(
                                children: [
                                  Expanded(
                                    child: OutlinedButton.icon(
                                      onPressed: onRestart,
                                      icon: const Icon(LucideIcons.refreshCcw,
                                          size: 14),
                                      label: const Text('다시쓰기',
                                          style: TextStyle(fontSize: 12)),
                                      style: OutlinedButton.styleFrom(
                                        foregroundColor: AppColors.subBrown2,
                                        side: const BorderSide(
                                            color: _CC.border),
                                        padding: const EdgeInsets.symmetric(
                                            vertical: 12),
                                        minimumSize: Size.zero,
                                        shape: const StadiumBorder(),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: FilledButton.icon(
                                      onPressed:
                                          state.isSending ? null : onSave,
                                      icon: state.isSending
                                          ? const SizedBox(
                                              width: 14,
                                              height: 14,
                                              child:
                                                  CircularProgressIndicator(
                                                strokeWidth: 2,
                                                color: Colors.white,
                                              ),
                                            )
                                          : const Icon(LucideIcons.bookPlus,
                                              size: 14),
                                      label: Text(
                                        state.isSending
                                            ? '저장 중...'
                                            : '일기저장',
                                        style: const TextStyle(fontSize: 12),
                                      ),
                                      style: FilledButton.styleFrom(
                                        backgroundColor: _CC.primary,
                                        foregroundColor: Colors.white,
                                        padding: const EdgeInsets.symmetric(
                                            vertical: 12),
                                        shape: const StadiumBorder(),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
