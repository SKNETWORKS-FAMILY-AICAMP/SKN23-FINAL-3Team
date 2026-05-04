import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../../core/theme/app_colors.dart';
import '../../../shared/models/enums.dart';
import '../../../shared/models/user.dart';
import '../../auth/auth_providers.dart';
import '../../onboarding/onboarding_providers.dart';

/// 사용자 정보 수정 모달 (Bug #5, 2026-05-04 저녁).
///
/// 핵심 필드 3종: 닉네임 / 성별 / 생일. 이메일·provider 는 OAuth 권위라 수정 X.
/// 저장 → `PATCH /api/users/{id}` → `auth.refreshUser()` 로 전체 사용자 동기화.
class UserEditModal extends ConsumerStatefulWidget {
  const UserEditModal({super.key, required this.user});

  final User user;

  @override
  ConsumerState<UserEditModal> createState() => _UserEditModalState();
}

class _UserEditModalState extends ConsumerState<UserEditModal> {
  late final TextEditingController _nicknameCtrl;
  DateTime? _birthDate;
  Gender? _gender;
  late final Set<String> _selectedTags;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _nicknameCtrl = TextEditingController(text: widget.user.nickname);
    _birthDate = widget.user.birthDate;
    _gender = widget.user.gender;
    _selectedTags = (widget.user.selectedTags ?? const [])
        .map((e) => e.toString())
        .toSet();
  }

  @override
  void dispose() {
    _nicknameCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickBirthDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _birthDate ?? DateTime(now.year - 25, now.month, now.day),
      firstDate: DateTime(1930),
      lastDate: now,
    );
    if (picked != null) setState(() => _birthDate = picked);
  }

  Future<void> _save() async {
    final nickname = _nicknameCtrl.text.trim();
    if (nickname.isEmpty) {
      Fluttertoast.showToast(msg: '닉네임을 입력해주세요.');
      return;
    }
    setState(() => _saving = true);
    try {
      await ref.read(userApiProvider).update(
            widget.user.id,
            UserUpdate(
              nickname: nickname == widget.user.nickname ? null : nickname,
              birthDate: _birthDate,
              gender: _gender,
              selectedTags: _selectedTags.toList(),
            ),
          );
      await ref.read(authProvider.notifier).refreshUser();
      if (mounted) {
        Fluttertoast.showToast(msg: '정보가 수정됐어요');
        Navigator.of(context).pop(true);
      }
    } on DioException catch (e) {
      final detail = e.response?.data is Map
          ? (e.response!.data as Map)['detail']?.toString()
          : null;
      Fluttertoast.showToast(
        msg: detail != null
            ? '수정 실패 (${e.response?.statusCode}): $detail'
            : '수정 실패: ${e.type.name} ${e.message ?? ''}',
      );
    } catch (e) {
      Fluttertoast.showToast(msg: '수정 실패: $e');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.65,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      expand: false,
      builder: (_, scrollController) {
        return Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 12, 12, 4),
              child: Row(
                children: [
                  const Expanded(
                    child: Text(
                      '내 정보 수정',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: AppColors.darkBrown,
                      ),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(LucideIcons.x),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),
            Expanded(
              child: ListView(
                controller: scrollController,
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.peach,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(
                      children: [
                        const Icon(LucideIcons.mail,
                            size: 14, color: AppColors.brandOrange),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            widget.user.email,
                            style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.subBrown2,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        Text(
                          '${widget.user.provider} 로그인',
                          style: const TextStyle(
                            fontSize: 11,
                            color: AppColors.brandOrange,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  const _Label(text: '닉네임'),
                  TextField(
                    controller: _nicknameCtrl,
                    decoration: const InputDecoration(hintText: '예: 가을쥐'),
                    maxLength: 30,
                  ),
                  const SizedBox(height: 8),
                  const _Label(text: '생일'),
                  InkWell(
                    onTap: _pickBirthDate,
                    borderRadius: BorderRadius.circular(8),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 14),
                      decoration: BoxDecoration(
                        border: Border.all(color: AppColors.beige),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          const Icon(LucideIcons.calendar,
                              size: 16, color: AppColors.brandOrange),
                          const SizedBox(width: 8),
                          Text(
                            _birthDate == null
                                ? '미입력'
                                : _formatDate(_birthDate!),
                            style: TextStyle(
                              color: _birthDate == null
                                  ? AppColors.mutedForeground
                                  : AppColors.darkBrown,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  const _Label(text: '성별'),
                  Wrap(
                    spacing: 8,
                    children: [
                      ChoiceChip(
                        label: const Text('남성'),
                        selected: _gender == Gender.male,
                        selectedColor: AppColors.peach,
                        onSelected: (_) => setState(() => _gender = Gender.male),
                      ),
                      ChoiceChip(
                        label: const Text('여성'),
                        selected: _gender == Gender.female,
                        selectedColor: AppColors.peach,
                        onSelected: (_) => setState(() => _gender = Gender.female),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const _Label(text: '라이프스타일'),
                  // 사용자 요청 (2026-05-04 밤): step page 의 보호자 정보와 일치 —
                  // userKeywords (category=USER) multi-select
                  _LifestyleTagPicker(
                    selected: _selectedTags,
                    onChanged: (tags) => setState(() {
                      _selectedTags
                        ..clear()
                        ..addAll(tags);
                    }),
                  ),
                  const SizedBox(height: 24),
                  FilledButton(
                    onPressed: _saving ? null : _save,
                    style: FilledButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: _saving
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('저장'),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }

  static String _formatDate(DateTime d) =>
      '${d.year}.${d.month.toString().padLeft(2, '0')}.${d.day.toString().padLeft(2, '0')}';
}

class _Label extends StatelessWidget {
  const _Label({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.bold,
          color: AppColors.subBrown2,
        ),
      ),
    );
  }
}

class _LifestyleTagPicker extends ConsumerWidget {
  const _LifestyleTagPicker({required this.selected, required this.onChanged});

  final Set<String> selected;
  final ValueChanged<Set<String>> onChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(userKeywordsProvider);
    return async.when(
      data: (keywords) {
        return Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final kw in keywords)
              FilterChip(
                label: Text(kw.name),
                selected: selected.contains(kw.name),
                selectedColor: AppColors.peach,
                onSelected: (on) {
                  final next = {...selected};
                  if (on) {
                    next.add(kw.name);
                  } else {
                    next.remove(kw.name);
                  }
                  onChanged(next);
                },
              ),
          ],
        );
      },
      loading: () => const Padding(
        padding: EdgeInsets.symmetric(vertical: 12),
        child: Center(
          child: SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
      ),
      error: (e, _) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Text(
          '라이프스타일 태그 로드 실패: $e',
          style: const TextStyle(color: AppColors.destructive, fontSize: 12),
        ),
      ),
    );
  }
}
