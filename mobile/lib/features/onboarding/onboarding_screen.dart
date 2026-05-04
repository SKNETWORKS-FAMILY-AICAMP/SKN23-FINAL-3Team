import 'dart:io' as io;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/router/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/models/breed.dart';
import '../../shared/models/enums.dart';
import '../../shared/models/keyword.dart';
import '../../shared/models/pet.dart';
import '../../shared/models/user.dart';
import '../auth/auth_providers.dart';
import 'onboarding_providers.dart';

const _maxKeywordSelections = 5;

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final _formKey = GlobalKey<FormState>();

  // 보호자
  final _ownerNicknameCtrl = TextEditingController();
  DateTime? _ownerBirthDate;
  Gender? _ownerGender;
  final Set<int> _ownerKeywordIds = {};

  // 반려견
  final _petNameCtrl = TextEditingController();
  DateTime? _petBirthDate;
  Breed? _selectedBreed;
  PetGender? _petGender;
  bool? _petNeutered;
  final Set<int> _petKeywordIds = {};
  String? _petPhotoPath;

  bool _submitting = false;

  @override
  void dispose() {
    _ownerNicknameCtrl.dispose();
    _petNameCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickPetPhoto() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 80,
    );
    if (picked != null && mounted) {
      setState(() => _petPhotoPath = picked.path);
    }
  }

  Future<void> _pickBirthDate({required bool owner}) async {
    final now = DateTime.now();
    final initial = owner ? (_ownerBirthDate ?? DateTime(now.year - 30)) : (_petBirthDate ?? DateTime(now.year - 3));
    final picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(1900),
      lastDate: now,
    );
    if (picked != null && mounted) {
      setState(() {
        if (owner) {
          _ownerBirthDate = picked;
        } else {
          _petBirthDate = picked;
        }
      });
    }
  }

  void _toggleKeyword(Set<int> selected, int id) {
    setState(() {
      if (selected.contains(id)) {
        selected.remove(id);
      } else if (selected.length < _maxKeywordSelections) {
        selected.add(id);
      } else {
        Fluttertoast.showToast(
          msg: '최대 $_maxKeywordSelections개까지 선택 가능합니다.',
        );
      }
    });
  }

  Future<void> _submit() async {
    if (_submitting) return;
    if (!_formKey.currentState!.validate()) return;
    if (_selectedBreed == null) {
      Fluttertoast.showToast(msg: '견종을 선택해주세요.');
      return;
    }
    final auth = ref.read(authProvider);
    if (auth is! AuthAuthenticated) {
      Fluttertoast.showToast(msg: '로그인 세션이 만료되었습니다.');
      return;
    }
    setState(() => _submitting = true);
    try {
      final userApi = ref.read(userApiProvider);
      final petApi = ref.read(petApiProvider);
      final imageApi = ref.read(imageApiProvider);

      // 1. 보호자 프로필 갱신 (PATCH /users/{id})
      final updatedUser = await userApi.update(
        auth.user.id,
        UserUpdate(
          nickname: _ownerNicknameCtrl.text.trim(),
          birthDate: _ownerBirthDate,
          gender: _ownerGender,
          selectedTags: _ownerKeywordIds.toList(),
        ),
      );

      // 2. 반려견 사진 업로드 (선택)
      // 현재 PetCreate 스키마는 photo 필드 X — 사진은 별도 등록 후
      // 추후 마이페이지에서 user.profile_id 처럼 연결될 가능성. 본 단계에선 업로드만.
      if (_petPhotoPath != null) {
        await imageApi.upload(_petPhotoPath!);
      }

      // 3. 반려견 등록 (POST /pets)
      final pet = await petApi.create(
        PetCreate(
          breedId: _selectedBreed!.id,
          name: _petNameCtrl.text.trim(),
          birthDate: _petBirthDate,
          gender: _petGender,
          isNeutered: _petNeutered,
          selectedTags: _petKeywordIds.toList(),
        ),
      );
      // primary_pet_id 자동 설정 — 백엔드 [[feature-primary-pet]] §자동 정책
      // (첫 pet 자동 대표). 클라이언트는 추가 PATCH 불필요.

      // 4. AuthProvider user 갱신 — userApi.update 결과 반영
      ref.read(authProvider.notifier).updateUser(updatedUser);

      // 5. 백엔드 자동 처리 (primary_pet_id) 동기화 — GET /api/users/me 재조회.
      //    Step 1 잔여 의문 (2026-05-03) → Step 4 본격 구현 시 자연 검증·정정.
      //    auth.user.primaryPet nested 가 채워져야 MyPage 대표 카드 정상 표시.
      await ref.read(authProvider.notifier).refreshUser();

      if (!mounted) return;
      Fluttertoast.showToast(msg: '${pet.name}와의 추억을 시작합니다!');
      context.go(AppRoutes.home);
    } catch (e) {
      if (!mounted) return;
      Fluttertoast.showToast(msg: '등록 실패: $e');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('시작하기'),
        elevation: 0,
        backgroundColor: Colors.transparent,
        foregroundColor: AppColors.darkBrown,
      ),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _OwnerSection(
                nicknameCtrl: _ownerNicknameCtrl,
                birthDate: _ownerBirthDate,
                onBirthDateTap: () => _pickBirthDate(owner: true),
                gender: _ownerGender,
                onGenderChanged: (g) => setState(() => _ownerGender = g),
                selectedKeywordIds: _ownerKeywordIds,
                onKeywordToggle: (id) =>
                    _toggleKeyword(_ownerKeywordIds, id),
              ),
              const SizedBox(height: 16),
              _PetSection(
                nameCtrl: _petNameCtrl,
                birthDate: _petBirthDate,
                onBirthDateTap: () => _pickBirthDate(owner: false),
                selectedBreed: _selectedBreed,
                onBreedSelected: (b) => setState(() => _selectedBreed = b),
                gender: _petGender,
                onGenderChanged: (g) => setState(() => _petGender = g),
                neutered: _petNeutered,
                onNeuteredChanged: (n) => setState(() => _petNeutered = n),
                selectedKeywordIds: _petKeywordIds,
                onKeywordToggle: (id) => _toggleKeyword(_petKeywordIds, id),
                photoPath: _petPhotoPath,
                onPhotoTap: _pickPetPhoto,
              ),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: _submitting ? null : _submit,
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: _submitting
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2,
                        ),
                      )
                    : const Text(
                        '시작하기! 🐾',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _OwnerSection extends ConsumerWidget {
  const _OwnerSection({
    required this.nicknameCtrl,
    required this.birthDate,
    required this.onBirthDateTap,
    required this.gender,
    required this.onGenderChanged,
    required this.selectedKeywordIds,
    required this.onKeywordToggle,
  });

  final TextEditingController nicknameCtrl;
  final DateTime? birthDate;
  final VoidCallback onBirthDateTap;
  final Gender? gender;
  final ValueChanged<Gender> onGenderChanged;
  final Set<int> selectedKeywordIds;
  final ValueChanged<int> onKeywordToggle;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final keywords = ref.watch(userKeywordsProvider);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '보호자 정보',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            const _FieldLabel('닉네임'),
            TextFormField(
              controller: nicknameCtrl,
              decoration: const InputDecoration(hintText: '보호자님'),
              validator: (v) => (v == null || v.trim().isEmpty) ? '닉네임을 입력하세요' : null,
            ),
            const SizedBox(height: 16),
            const _FieldLabel('생년월일'),
            _DatePickerField(
              date: birthDate,
              onTap: onBirthDateTap,
              hint: '연도-월-일',
            ),
            const SizedBox(height: 16),
            const _FieldLabel('성별'),
            Row(
              children: [
                Expanded(
                  child: _GenderToggle(
                    label: '남성',
                    selected: gender == Gender.male,
                    onTap: () => onGenderChanged(Gender.male),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _GenderToggle(
                    label: '여성',
                    selected: gender == Gender.female,
                    onTap: () => onGenderChanged(Gender.female),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _KeywordChipsLabel(
              label: '라이프스타일 (중복 선택 가능)',
              count: selectedKeywordIds.length,
            ),
            const SizedBox(height: 8),
            keywords.when(
              data: (list) => _KeywordChips(
                keywords: list,
                selectedIds: selectedKeywordIds,
                onToggle: onKeywordToggle,
              ),
              loading: () => const Padding(
                padding: EdgeInsets.all(8),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => Text(
                '라이프스타일 로드 실패: $e',
                style: const TextStyle(color: AppColors.destructive),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PetSection extends ConsumerWidget {
  const _PetSection({
    required this.nameCtrl,
    required this.birthDate,
    required this.onBirthDateTap,
    required this.selectedBreed,
    required this.onBreedSelected,
    required this.gender,
    required this.onGenderChanged,
    required this.neutered,
    required this.onNeuteredChanged,
    required this.selectedKeywordIds,
    required this.onKeywordToggle,
    required this.photoPath,
    required this.onPhotoTap,
  });

  final TextEditingController nameCtrl;
  final DateTime? birthDate;
  final VoidCallback onBirthDateTap;
  final Breed? selectedBreed;
  final ValueChanged<Breed> onBreedSelected;
  final PetGender? gender;
  final ValueChanged<PetGender> onGenderChanged;
  final bool? neutered;
  final ValueChanged<bool> onNeuteredChanged;
  final Set<int> selectedKeywordIds;
  final ValueChanged<int> onKeywordToggle;
  final String? photoPath;
  final VoidCallback onPhotoTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final breeds = ref.watch(popularBreedsProvider);
    final petKeywords = ref.watch(petKeywordsProvider);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '반려견 정보',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Center(
              child: _PetPhotoPicker(path: photoPath, onTap: onPhotoTap),
            ),
            const SizedBox(height: 16),
            const _FieldLabel('강아지 이름'),
            TextFormField(
              controller: nameCtrl,
              decoration: const InputDecoration(hintText: '예: 코코'),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? '이름을 입력하세요' : null,
            ),
            const SizedBox(height: 16),
            const _FieldLabel('생년월일'),
            _DatePickerField(
              date: birthDate,
              onTap: onBirthDateTap,
              hint: '연도-월-일',
            ),
            const SizedBox(height: 16),
            const _FieldLabel('견종'),
            breeds.when(
              data: (list) => _BreedChips(
                breeds: list,
                selected: selectedBreed,
                onSelected: onBreedSelected,
              ),
              loading: () => const Padding(
                padding: EdgeInsets.all(8),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => Text(
                '견종 로드 실패: $e',
                style: const TextStyle(color: AppColors.destructive),
              ),
            ),
            const SizedBox(height: 16),
            const _FieldLabel('성별'),
            Row(
              children: [
                Expanded(
                  child: _GenderToggle(
                    label: '남아',
                    selected: gender == PetGender.male,
                    onTap: () => onGenderChanged(PetGender.male),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _GenderToggle(
                    label: '여아',
                    selected: gender == PetGender.female,
                    onTap: () => onGenderChanged(PetGender.female),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            const _FieldLabel('중성화 여부'),
            Row(
              children: [
                Expanded(
                  child: _GenderToggle(
                    label: 'O',
                    selected: neutered == true,
                    onTap: () => onNeuteredChanged(true),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _GenderToggle(
                    label: 'X',
                    selected: neutered == false,
                    onTap: () => onNeuteredChanged(false),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _KeywordChipsLabel(
              label: '성격 (중복 선택 가능)',
              count: selectedKeywordIds.length,
            ),
            const SizedBox(height: 8),
            petKeywords.when(
              data: (list) => _KeywordChips(
                keywords: list,
                selectedIds: selectedKeywordIds,
                onToggle: onKeywordToggle,
              ),
              loading: () => const Padding(
                padding: EdgeInsets.all(8),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => Text(
                '성격 로드 실패: $e',
                style: const TextStyle(color: AppColors.destructive),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FieldLabel extends StatelessWidget {
  const _FieldLabel(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 13,
          color: AppColors.subBrown2,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}

class _DatePickerField extends StatelessWidget {
  const _DatePickerField({
    required this.date,
    required this.onTap,
    required this.hint,
  });

  final DateTime? date;
  final VoidCallback onTap;
  final String hint;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: InputDecorator(
        decoration: const InputDecoration(),
        child: Text(
          date == null ? hint : _formatDate(date!),
          style: TextStyle(
            color: date == null ? AppColors.mutedForeground : AppColors.darkBrown,
          ),
        ),
      ),
    );
  }

  static String _formatDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
}

class _GenderToggle extends StatelessWidget {
  const _GenderToggle({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Container(
        height: 48,
        decoration: BoxDecoration(
          color: selected ? AppColors.peach : Colors.white,
          border: Border.all(
            color: selected ? AppColors.brandOrange : AppColors.beige,
            width: selected ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(10),
        ),
        alignment: Alignment.center,
        child: Text(
          label,
          style: TextStyle(
            color: selected ? AppColors.brandOrange : AppColors.darkBrown,
            fontWeight: selected ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ),
    );
  }
}

class _KeywordChipsLabel extends StatelessWidget {
  const _KeywordChipsLabel({required this.label, required this.count});

  final String label;
  final int count;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 13,
            color: AppColors.subBrown2,
            fontWeight: FontWeight.w500,
          ),
        ),
        Text(
          '$count/$_maxKeywordSelections',
          style: TextStyle(
            fontSize: 12,
            color: count >= _maxKeywordSelections
                ? AppColors.brandOrange
                : AppColors.mutedForeground,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}

class _KeywordChips extends StatelessWidget {
  const _KeywordChips({
    required this.keywords,
    required this.selectedIds,
    required this.onToggle,
  });

  final List<Keyword> keywords;
  final Set<int> selectedIds;
  final ValueChanged<int> onToggle;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final kw in keywords)
          FilterChip(
            label: Text(kw.name),
            selected: selectedIds.contains(kw.id),
            onSelected: (_) => onToggle(kw.id),
            selectedColor: AppColors.peach,
            checkmarkColor: AppColors.brandOrange,
            backgroundColor: Colors.white,
          ),
      ],
    );
  }
}

class _BreedChips extends StatelessWidget {
  const _BreedChips({
    required this.breeds,
    required this.selected,
    required this.onSelected,
  });

  final List<Breed> breeds;
  final Breed? selected;
  final ValueChanged<Breed> onSelected;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final breed in breeds)
          ChoiceChip(
            label: Text(breed.nameKo),
            selected: selected?.id == breed.id,
            onSelected: (_) => onSelected(breed),
            selectedColor: AppColors.peach,
            backgroundColor: Colors.white,
          ),
      ],
    );
  }
}

class _PetPhotoPicker extends StatelessWidget {
  const _PetPhotoPicker({required this.path, required this.onTap});

  final String? path;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(60),
      child: Column(
        children: [
          Container(
            width: 96,
            height: 96,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.peach,
              image: path == null
                  ? null
                  : DecorationImage(
                      image: _imageProvider(path!),
                      fit: BoxFit.cover,
                    ),
            ),
            alignment: Alignment.center,
            child: path == null
                ? const Icon(
                    LucideIcons.camera,
                    color: AppColors.brandOrange,
                    size: 32,
                  )
                : null,
          ),
          const SizedBox(height: 8),
          const Text(
            '클릭하여 사진 추가',
            style: TextStyle(
              fontSize: 12,
              color: AppColors.mutedForeground,
            ),
          ),
        ],
      ),
    );
  }

  static ImageProvider _imageProvider(String path) {
    return path.startsWith('http')
        ? NetworkImage(path)
        : FileImage(io.File(path));
  }
}
