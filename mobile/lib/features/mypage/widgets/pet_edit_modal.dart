import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../../core/theme/app_colors.dart';
import '../../../shared/models/enums.dart';
import '../../../shared/models/pet.dart';
import '../../auth/auth_providers.dart';
import '../../onboarding/keyword_api.dart';
import '../../onboarding/onboarding_providers.dart';

/// 반려견 정보 수정 모달 (Bug #4 + 추가 요청 2026-05-04 밤).
///
/// step page 와 일치 — 6 필드: 이름 / 견종 / 생일 / 성별 / 중성화 (O/X 만) / 성격 태그.
/// 저장 → `PATCH /api/pets/{id}` → 성공 시 `userPetsProvider` invalidate +
/// `auth.refreshUser()` (대표 반려견인 경우 nested `primary_pet` 동기화).
class PetEditModal extends ConsumerStatefulWidget {
  const PetEditModal({super.key, required this.pet});

  final Pet pet;

  @override
  ConsumerState<PetEditModal> createState() => _PetEditModalState();
}

class _PetEditModalState extends ConsumerState<PetEditModal> {
  late final TextEditingController _nameCtrl;
  int? _breedId;
  DateTime? _birthDate;
  PetGender? _gender;
  bool? _isNeutered;
  late final Set<String> _selectedTags;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _nameCtrl = TextEditingController(text: widget.pet.name);
    _breedId = widget.pet.breedId;
    _birthDate = widget.pet.birthDate;
    _gender = widget.pet.gender;
    _isNeutered = widget.pet.isNeutered;
    _selectedTags = (widget.pet.selectedTags ?? const [])
        .map((e) => e.toString())
        .toSet();
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickBirthDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _birthDate ?? DateTime(now.year - 3, now.month, now.day),
      firstDate: DateTime(1990),
      lastDate: now,
    );
    if (picked != null) setState(() => _birthDate = picked);
  }

  Future<void> _save() async {
    final name = _nameCtrl.text.trim();
    if (name.isEmpty) {
      Fluttertoast.showToast(msg: '이름을 입력해주세요.');
      return;
    }
    setState(() => _saving = true);
    try {
      await ref.read(petApiProvider).update(
            widget.pet.id,
            PetUpdate(
              breedId: _breedId == widget.pet.breedId ? null : _breedId,
              name: name == widget.pet.name ? null : name,
              birthDate: _birthDate,
              gender: _gender,
              isNeutered: _isNeutered,
              selectedTags: _selectedTags.toList(),
            ),
          );
      ref.invalidate(userPetsProvider);
      await ref.read(authProvider.notifier).refreshUser();
      if (mounted) {
        Fluttertoast.showToast(msg: '반려견 정보가 수정됐어요');
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
      initialChildSize: 0.85,
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
                      '반려견 정보 수정',
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
                  const _Label(text: '이름'),
                  TextField(
                    controller: _nameCtrl,
                    decoration: const InputDecoration(hintText: '예: 코코'),
                    maxLength: 30,
                  ),
                  const SizedBox(height: 8),
                  const _Label(text: '견종'),
                  _BreedPicker(
                    selectedBreedId: _breedId,
                    onChanged: (id) => setState(() => _breedId = id),
                  ),
                  const SizedBox(height: 16),
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
                      for (final g in PetGender.values)
                        ChoiceChip(
                          label: Text(g.label),
                          selected: _gender == g,
                          selectedColor: AppColors.peach,
                          onSelected: (_) => setState(() => _gender = g),
                        ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const _Label(text: '중성화 여부'),
                  // 사용자 요청 (2026-05-04 밤): O/X 만, 미상 옵션 삭제
                  Wrap(
                    spacing: 8,
                    children: [
                      ChoiceChip(
                        label: const Text('O'),
                        selected: _isNeutered == true,
                        selectedColor: AppColors.peach,
                        onSelected: (_) => setState(() => _isNeutered = true),
                      ),
                      ChoiceChip(
                        label: const Text('X'),
                        selected: _isNeutered == false,
                        selectedColor: AppColors.peach,
                        onSelected: (_) => setState(() => _isNeutered = false),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const _Label(text: '성격 태그'),
                  _TagPicker(
                    category: KeywordCategory.pet,
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

/// 견종 dropdown — `allBreedsProvider` watch. 한국어명 정렬.
class _BreedPicker extends ConsumerWidget {
  const _BreedPicker({
    required this.selectedBreedId,
    required this.onChanged,
  });

  final int? selectedBreedId;
  final ValueChanged<int?> onChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(allBreedsProvider);
    return async.when(
      data: (breeds) {
        final sorted = [...breeds]..sort((a, b) => a.nameKo.compareTo(b.nameKo));
        return DropdownButtonFormField<int>(
          initialValue: sorted.any((b) => b.id == selectedBreedId)
              ? selectedBreedId
              : null,
          isExpanded: true,
          decoration: const InputDecoration(hintText: '견종을 선택하세요'),
          items: [
            for (final b in sorted)
              DropdownMenuItem(
                value: b.id,
                child: Text(b.nameKo),
              ),
          ],
          onChanged: onChanged,
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
          '견종 목록 로드 실패: $e',
          style: const TextStyle(color: AppColors.destructive, fontSize: 12),
        ),
      ),
    );
  }
}

/// 성격·라이프스타일 태그 multi-select — 카테고리별 keyword API watch.
class _TagPicker extends ConsumerWidget {
  const _TagPicker({
    required this.category,
    required this.selected,
    required this.onChanged,
  });

  final KeywordCategory category;
  final Set<String> selected;
  final ValueChanged<Set<String>> onChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = category == KeywordCategory.pet
        ? ref.watch(petKeywordsProvider)
        : ref.watch(userKeywordsProvider);
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
          '태그 목록 로드 실패: $e',
          style: const TextStyle(color: AppColors.destructive, fontSize: 12),
        ),
      ),
    );
  }
}
