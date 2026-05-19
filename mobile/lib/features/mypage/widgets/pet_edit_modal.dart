import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:image_picker/image_picker.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../../core/theme/app_colors.dart';
import '../../../shared/models/enums.dart';
import '../../../shared/models/pet.dart';
import '../../auth/auth_providers.dart';
import '../../onboarding/onboarding_providers.dart';

const _kCreamBg = Color(0xFFFFF8F3);
const _kOrangeBorder = Color(0xFFFFD2C2);
const _kMaxTags = 5;

/// 반려견 정보 수정 모달.
///
/// 6 필드: 이름 / 견종 / 생일 / 성별 / 중성화 (O/X) / 성격 태그.
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
  XFile? _profileImage;
  int? _breedId;
  String? _breedName; // null = 아직 picker로 변경 안 됨 → build에서 allBreedsProvider 로 표시
  DateTime? _birthDate;
  PetGender? _gender;
  bool? _isNeutered;
  late Set<String> _selectedTags;
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

  Future<void> _pickProfileImage() async {
    final picker = ImagePicker();
    final image = await picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 512,
      maxHeight: 512,
      imageQuality: 85,
    );
    if (image != null && mounted) setState(() => _profileImage = image);
  }

  Future<void> _pickBirthDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _birthDate ?? DateTime(now.year - 3, now.month, now.day),
      firstDate: DateTime(1990),
      lastDate: now,
    );
    if (picked != null && mounted) setState(() => _birthDate = picked);
  }

  Future<void> _openBreedSheet() async {
    final result = await showModalBottomSheet<({int id, String name})>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const _BreedPickerSheet(),
    );
    if (result != null && mounted) {
      setState(() {
        _breedId = result.id;
        _breedName = result.name;
      });
    }
  }

  Future<void> _openAllTagsSheet() async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _AllTagsSheet(
        initialSelected: {..._selectedTags},
        onChanged: (tags) {
          if (mounted) {
            setState(() {
              _selectedTags
                ..clear()
                ..addAll(tags);
            });
          }
        },
      ),
    );
  }

  Future<void> _save() async {
    final name = _nameCtrl.text.trim();
    if (name.isEmpty) {
      Fluttertoast.showToast(msg: '이름을 입력해주세요.');
      return;
    }
    setState(() => _saving = true);
    try {
      // 새 프로필 사진 업로드 (변경된 경우만)
      int? imageId;
      if (_profileImage != null) {
        final fileSize = await File(_profileImage!.path).length();
        if (fileSize > 5 * 1024 * 1024) {
          throw Exception('5MB 이하 이미지만 업로드 가능합니다');
        }
        final uploaded =
            await ref.read(imageApiProvider).upload(_profileImage!.path);
        imageId = uploaded.id;
      }
      final data = PetUpdate(
              breedId: _breedId == widget.pet.breedId ? null : _breedId,
              name: name == widget.pet.name ? null : name,
              birthDate: _birthDate,
              gender: _gender,
              isNeutered: _isNeutered,
              selectedTags: _selectedTags.toList(),
              imageId: imageId,
            );
      await ref.read(petApiProvider).update(widget.pet.id, data);
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
    // allBreedsProvider로 현재 breedId의 한국어 이름 조회 (picker 변경 전 초기 표시용)
    final breedsAsync = ref.watch(allBreedsProvider);
    final displayBreedName = _breedName ??
        breedsAsync.whenOrNull(
          data: (breeds) {
            try {
              return breeds.firstWhere((b) => b.id == _breedId).nameKo;
            } catch (_) {
              return null;
            }
          },
        );

    return DraggableScrollableSheet(
      initialChildSize: 0.88,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      expand: false,
      builder: (_, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: _kCreamBg,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              const _DragHandle(),
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 4, 12, 4),
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
                    // 프로필 사진
                    Center(
                      child: _ProfilePhotoPicker(
                        image: _profileImage,
                        existingUrl: widget.pet.imageUrl,
                        onTap: _pickProfileImage,
                      ),
                    ),
                    const SizedBox(height: 20),

                    // 이름
                    const _Label(text: '이름'),
                    _StyledTextField(
                      controller: _nameCtrl,
                      hintText: '예: 코코',
                      maxLength: 30,
                    ),
                    const SizedBox(height: 16),

                    // 견종
                    const _Label(text: '견종'),
                    _TappableRow(
                      onTap: _openBreedSheet,
                      child: Text(
                        displayBreedName ?? '견종을 선택하세요',
                        style: TextStyle(
                          color: displayBreedName == null
                              ? AppColors.mutedForeground
                              : AppColors.darkBrown,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // 생일
                    const _Label(text: '생일'),
                    _TappableRow(
                      onTap: _pickBirthDate,
                      child: Row(
                        children: [
                          const Icon(
                            LucideIcons.calendar,
                            size: 16,
                            color: AppColors.brandOrange,
                          ),
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
                    const SizedBox(height: 16),

                    // 성별
                    const _Label(text: '성별'),
                    Wrap(
                      spacing: 8,
                      children: [
                        for (final g in PetGender.values)
                          _SelectChip(
                            label: g.label,
                            selected: _gender == g,
                            onTap: () => setState(() => _gender = g),
                          ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // 중성화 여부
                    const _Label(text: '중성화 여부'),
                    Wrap(
                      spacing: 8,
                      children: [
                        _SelectChip(
                          label: 'O',
                          selected: _isNeutered == true,
                          onTap: () => setState(() => _isNeutered = true),
                        ),
                        _SelectChip(
                          label: 'X',
                          selected: _isNeutered == false,
                          onTap: () => setState(() => _isNeutered = false),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // 성격 태그
                    _TagSection(
                      selected: _selectedTags,
                      onChanged: (tags) => setState(() {
                        _selectedTags
                          ..clear()
                          ..addAll(tags);
                      }),
                      onMoreTap: _openAllTagsSheet,
                    ),
                    const SizedBox(height: 24),

                    FilledButton(
                      onPressed: _saving ? null : _save,
                      style: FilledButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        backgroundColor: AppColors.brandOrange,
                      ),
                      child: _saving
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Text('저장'),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  static String _formatDate(DateTime d) =>
      '${d.year}.${d.month.toString().padLeft(2, '0')}.${d.day.toString().padLeft(2, '0')}';
}

// ─── 견종 선택 시트 ────────────────────────────────────────────────────────────

class _BreedPickerSheet extends ConsumerStatefulWidget {
  const _BreedPickerSheet({super.key});

  @override
  ConsumerState<_BreedPickerSheet> createState() => _BreedPickerSheetState();
}

class _BreedPickerSheetState extends ConsumerState<_BreedPickerSheet> {
  final _searchCtrl = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final popularAsync = ref.watch(popularBreedsProvider);
    final searchAsync = ref.watch(breedSearchProvider(_query));

    return DraggableScrollableSheet(
      initialChildSize: 0.75,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      expand: false,
      builder: (_, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: _kCreamBg,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              const _DragHandle(),
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 4, 12, 8),
                child: Row(
                  children: [
                    const Expanded(
                      child: Text(
                        '견종 선택',
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
              Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                child: TextField(
                  controller: _searchCtrl,
                  decoration: InputDecoration(
                    hintText: '견종 검색',
                    prefixIcon: const Icon(LucideIcons.search, size: 18),
                    filled: true,
                    fillColor: Colors.white,
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 12, vertical: 10),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: _kOrangeBorder),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: _kOrangeBorder),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(
                          color: AppColors.brandOrange, width: 1.5),
                    ),
                  ),
                  onChanged: (v) => setState(() => _query = v),
                ),
              ),
              Expanded(
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                  children: [
                    if (_query.isEmpty) ...[
                      const Padding(
                        padding: EdgeInsets.only(bottom: 8),
                        child: Text(
                          '인기 견종',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: AppColors.subBrown2,
                          ),
                        ),
                      ),
                      popularAsync.when(
                        data: (breeds) => Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            for (final b in breeds.take(6))
                              ActionChip(
                                label: Text(b.nameKo),
                                backgroundColor: Colors.white,
                                side: const BorderSide(color: _kOrangeBorder),
                                onPressed: () => Navigator.of(context)
                                    .pop((id: b.id, name: b.nameKo)),
                              ),
                          ],
                        ),
                        loading: () => const Center(
                          child: Padding(
                            padding: EdgeInsets.all(12),
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                        ),
                        error: (_, __) => const Text('인기 견종을 불러오지 못했어요.'),
                      ),
                      const SizedBox(height: 16),
                      const Padding(
                        padding: EdgeInsets.only(bottom: 8),
                        child: Text(
                          '전체 견종',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: AppColors.subBrown2,
                          ),
                        ),
                      ),
                    ],
                    searchAsync.when(
                      data: (breeds) => Column(
                        children: [
                          for (final b in breeds)
                            ListTile(
                              dense: true,
                              title: Text(b.nameKo,
                                  style: const TextStyle(
                                      color: AppColors.darkBrown)),
                              subtitle: Text(b.nameEn,
                                  style: const TextStyle(fontSize: 11)),
                              trailing: const Icon(LucideIcons.chevronRight,
                                  size: 16,
                                  color: AppColors.mutedForeground),
                              onTap: () => Navigator.of(context)
                                  .pop((id: b.id, name: b.nameKo)),
                            ),
                          if (breeds.isEmpty)
                            const Padding(
                              padding: EdgeInsets.all(16),
                              child: Text(
                                '검색 결과가 없어요',
                                style: TextStyle(
                                    color: AppColors.mutedForeground),
                              ),
                            ),
                        ],
                      ),
                      loading: () => const Center(
                        child: Padding(
                          padding: EdgeInsets.all(16),
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      ),
                      error: (_, __) => const Padding(
                        padding: EdgeInsets.all(16),
                        child: Text('견종 목록을 불러오지 못했어요.'),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

// ─── 성격 태그 섹션 (인라인 최대 8개 + 더보기) ─────────────────────────────────

class _TagSection extends ConsumerWidget {
  const _TagSection({
    required this.selected,
    required this.onChanged,
    required this.onMoreTap,
  });

  final Set<String> selected;
  final ValueChanged<Set<String>> onChanged;
  final VoidCallback onMoreTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(petKeywordsProvider);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Expanded(child: _Label(text: '성격 태그')),
            Text(
              '${selected.length} / $_kMaxTags',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: selected.length >= _kMaxTags
                    ? AppColors.brandOrange
                    : AppColors.mutedForeground,
              ),
            ),
          ],
        ),
        async.when(
          data: (keywords) {
            final displayed = keywords.take(8).toList();
            return Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final kw in displayed)
                  _TagChip(
                    label: kw.name,
                    selected: selected.contains(kw.name),
                    onTap: () {
                      final next = {...selected};
                      if (next.contains(kw.name)) {
                        next.remove(kw.name);
                        onChanged(next);
                      } else if (next.length < _kMaxTags) {
                        next.add(kw.name);
                        onChanged(next);
                      } else {
                        Fluttertoast.showToast(
                          msg: '성격 태그는 최대 $_kMaxTags개까지 선택할 수 있어요.',
                        );
                      }
                    },
                  ),
                if (keywords.length > 8)
                  ActionChip(
                    label: const Text('더보기'),
                    avatar: const Icon(LucideIcons.plus, size: 14),
                    backgroundColor: Colors.white,
                    side: const BorderSide(color: _kOrangeBorder),
                    onPressed: onMoreTap,
                  ),
              ],
            );
          },
          loading: () => const Center(
            child: Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            ),
          ),
          error: (_, __) => Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Row(
              children: [
                const Text('태그를 불러오지 못했어요.',
                    style: TextStyle(
                        color: AppColors.mutedForeground, fontSize: 12)),
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: () => ref.invalidate(petKeywordsProvider),
                  child: const Text('다시 시도',
                      style: TextStyle(
                          color: AppColors.brandOrange,
                          fontSize: 12,
                          decoration: TextDecoration.underline)),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

// ─── 성격 태그 전체 시트 ──────────────────────────────────────────────────────

class _AllTagsSheet extends ConsumerStatefulWidget {
  const _AllTagsSheet({
    super.key,
    required this.initialSelected,
    required this.onChanged,
  });

  final Set<String> initialSelected;
  final ValueChanged<Set<String>> onChanged;

  @override
  ConsumerState<_AllTagsSheet> createState() => _AllTagsSheetState();
}

class _AllTagsSheetState extends ConsumerState<_AllTagsSheet> {
  late Set<String> _selected;

  @override
  void initState() {
    super.initState();
    _selected = {...widget.initialSelected};
  }

  void _toggle(String name) {
    final next = {..._selected};
    if (next.contains(name)) {
      next.remove(name);
    } else if (next.length < _kMaxTags) {
      next.add(name);
    } else {
      Fluttertoast.showToast(msg: '성격 태그는 최대 $_kMaxTags개까지 선택할 수 있어요.');
      return;
    }
    setState(() => _selected = next);
    widget.onChanged(next);
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(petKeywordsProvider);
    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.4,
      maxChildSize: 0.9,
      expand: false,
      builder: (_, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: _kCreamBg,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              const _DragHandle(),
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 4, 12, 4),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            '성격 태그',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: AppColors.darkBrown,
                            ),
                          ),
                          Text(
                            '${_selected.length} / $_kMaxTags 선택됨',
                            style: TextStyle(
                              fontSize: 12,
                              color: _selected.length >= _kMaxTags
                                  ? AppColors.brandOrange
                                  : AppColors.mutedForeground,
                            ),
                          ),
                        ],
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
                child: async.when(
                  data: (keywords) => ListView(
                    controller: scrollController,
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                    children: [
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          for (final kw in keywords)
                            _TagChip(
                              label: kw.name,
                              selected: _selected.contains(kw.name),
                              onTap: () => _toggle(kw.name),
                            ),
                        ],
                      ),
                    ],
                  ),
                  loading: () =>
                      const Center(child: CircularProgressIndicator()),
                  error: (_, __) =>
                      const Center(child: Text('태그를 불러오지 못했어요.')),
                ),
              ),
              SafeArea(
                top: false,
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                  child: FilledButton(
                    onPressed: () => Navigator.of(context).pop(),
                    style: FilledButton.styleFrom(
                      minimumSize: const Size.fromHeight(48),
                      backgroundColor: AppColors.brandOrange,
                    ),
                    child: const Text('확인'),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

// ─── 공통 위젯 ────────────────────────────────────────────────────────────────

class _DragHandle extends StatelessWidget {
  const _DragHandle();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        margin: const EdgeInsets.only(top: 8, bottom: 4),
        width: 36,
        height: 4,
        decoration: BoxDecoration(
          color: Colors.grey.shade300,
          borderRadius: BorderRadius.circular(2),
        ),
      ),
    );
  }
}

class _ProfilePhotoPicker extends StatelessWidget {
  const _ProfilePhotoPicker({
    required this.image,
    required this.onTap,
    this.existingUrl,
  });

  final XFile? image;
  final String? existingUrl;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    ImageProvider? bgImage;
    if (image != null) {
      bgImage = FileImage(File(image!.path));
    } else if (existingUrl != null && existingUrl!.isNotEmpty) {
      bgImage = NetworkImage(existingUrl!);
    }

    return GestureDetector(
      onTap: onTap,
      child: Stack(
        alignment: Alignment.bottomRight,
        children: [
          CircleAvatar(
            radius: 48,
            backgroundColor: _kOrangeBorder,
            backgroundImage: bgImage,
            child: bgImage == null
                ? const Icon(LucideIcons.dog,
                    size: 36, color: AppColors.brandOrange)
                : null,
          ),
          Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              color: AppColors.brandOrange,
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 2),
            ),
            child: const Icon(LucideIcons.camera,
                size: 14, color: Colors.white),
          ),
        ],
      ),
    );
  }
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

class _TappableRow extends StatelessWidget {
  const _TappableRow({required this.child, required this.onTap});

  final Widget child;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: _kOrangeBorder),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Expanded(child: child),
            const Icon(LucideIcons.chevronRight,
                size: 16, color: AppColors.mutedForeground),
          ],
        ),
      ),
    );
  }
}

class _StyledTextField extends StatelessWidget {
  const _StyledTextField({
    required this.controller,
    required this.hintText,
    this.maxLength,
  });

  final TextEditingController controller;
  final String hintText;
  final int? maxLength;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      maxLength: maxLength,
      decoration: InputDecoration(
        hintText: hintText,
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: _kOrangeBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: _kOrangeBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide:
              const BorderSide(color: AppColors.brandOrange, width: 1.5),
        ),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      ),
    );
  }
}

class _SelectChip extends StatelessWidget {
  const _SelectChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      selectedColor: AppColors.peach,
      backgroundColor: Colors.white,
      side: BorderSide(
        color: selected ? AppColors.brandOrange : _kOrangeBorder,
      ),
      onSelected: (_) => onTap(),
    );
  }
}

class _TagChip extends StatelessWidget {
  const _TagChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return FilterChip(
      label: Text(label),
      selected: selected,
      selectedColor: AppColors.peach,
      checkmarkColor: AppColors.brandOrange,
      backgroundColor: Colors.white,
      side: BorderSide(
        color: selected ? AppColors.brandOrange : _kOrangeBorder,
      ),
      onSelected: (_) => onTap(),
    );
  }
}
