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

// ── 온보딩 인트로 이미지 경로 ──────────────────────────────────────────────────
const _introImages = [
  'assets/onboarding/onboarding_01_welcome.png',
  'assets/onboarding/onboarding_02_map.png',
  'assets/onboarding/onboarding_03_diary.png',
  'assets/onboarding/onboarding_04_diary_graph.png',
  'assets/onboarding/onboarding_05_profile_image.png',
];

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  /// true = 인트로 캐러셀, false = 기존 정보 입력 폼
  bool _showIntro = true;

  void _onIntroFinished() {
    setState(() => _showIntro = false);
  }

  @override
  Widget build(BuildContext context) {
    if (_showIntro) {
      return _IntroCarousel(onFinished: _onIntroFinished);
    }
    return const _OnboardingForm();
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 인트로 캐러셀 — 5장 이미지, 좌우 스와이프 + 화살표 + 도트 인디케이터
// ═══════════════════════════════════════════════════════════════════════════════

class _IntroCarousel extends StatefulWidget {
  const _IntroCarousel({required this.onFinished});

  final VoidCallback onFinished;

  @override
  State<_IntroCarousel> createState() => _IntroCarouselState();
}

class _IntroCarouselState extends State<_IntroCarousel> {
  final _pageCtrl = PageController();
  int _currentPage = 0;

  @override
  void dispose() {
    _pageCtrl.dispose();
    super.dispose();
  }

  void _goTo(int page) {
    _pageCtrl.animateToPage(
      page,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  @override
  Widget build(BuildContext context) {
    final isLast = _currentPage == _introImages.length - 1;

    return Scaffold(
      backgroundColor: AppColors.peach,
      body: SafeArea(
        child: Column(
          children: [
            // 상단 건너뛰기 버튼
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: widget.onFinished,
                child: const Text(
                  '건너뛰기',
                  style: TextStyle(
                    color: AppColors.subBrown,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ),

            // 이미지 캐러셀
            Expanded(
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // PageView
                  PageView.builder(
                    controller: _pageCtrl,
                    itemCount: _introImages.length,
                    onPageChanged: (i) => setState(() => _currentPage = i),
                    itemBuilder: (_, i) => Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 24),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(20),
                        child: Image.asset(
                          _introImages[i],
                          fit: BoxFit.contain,
                        ),
                      ),
                    ),
                  ),

                  // 왼쪽 화살표
                  if (_currentPage > 0)
                    Positioned(
                      left: 4,
                      child: _ArrowButton(
                        icon: Icons.chevron_left_rounded,
                        onTap: () => _goTo(_currentPage - 1),
                      ),
                    ),

                  // 오른쪽 화살표
                  if (!isLast)
                    Positioned(
                      right: 4,
                      child: _ArrowButton(
                        icon: Icons.chevron_right_rounded,
                        onTap: () => _goTo(_currentPage + 1),
                      ),
                    ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // 도트 인디케이터
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                _introImages.length,
                (i) => AnimatedContainer(
                  duration: const Duration(milliseconds: 250),
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: i == _currentPage ? 10 : 8,
                  height: i == _currentPage ? 10 : 8,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: i == _currentPage
                        ? AppColors.brandOrange
                        : AppColors.beige,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 20),

            // 하단 버튼
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: isLast
                      ? widget.onFinished
                      : () => _goTo(_currentPage + 1),
                  style: FilledButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    backgroundColor: AppColors.brandOrange,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  child: Text(
                    isLast ? '시작하기' : '다음',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}

class _ArrowButton extends StatelessWidget {
  const _ArrowButton({required this.icon, required this.onTap});

  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.8),
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.08),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Icon(icon, color: AppColors.darkBrown, size: 24),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 기존 온보딩 폼 (보호자 + 반려견 정보 입력)
// ═══════════════════════════════════════════════════════════════════════════════

class _OnboardingForm extends ConsumerStatefulWidget {
  const _OnboardingForm();

  @override
  ConsumerState<_OnboardingForm> createState() => _OnboardingFormState();
}

class _OnboardingFormState extends ConsumerState<_OnboardingForm> {
  final _formKey = GlobalKey<FormState>();

  // 보호자
  final _ownerNicknameCtrl = TextEditingController();
  DateTime? _ownerBirthDate;
  Gender? _ownerGender;
  final Set<int> _ownerKeywordIds = {};
  String? _ownerPhotoPath;

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

  Future<void> _pickOwnerPhoto() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 80,
    );

    if (picked != null && mounted) {
      setState(() => _ownerPhotoPath = picked.path);
    }
  }

  Future<void> _pickBirthDate({required bool owner}) async {
    final now = DateTime.now();

    final initial = owner
        ? (_ownerBirthDate ?? DateTime(now.year - 30))
        : (_petBirthDate ?? DateTime(now.year - 3));

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

      // 1-a. 보호자 프로필 사진 업로드
      int? ownerProfileId;
      if (_ownerPhotoPath != null) {
        final fileSize = await io.File(_ownerPhotoPath!).length();
        if (fileSize > 5 * 1024 * 1024) {
          throw Exception('5MB 이하 이미지만 업로드 가능합니다');
        }
        final uploaded = await imageApi.upload(_ownerPhotoPath!);
        ownerProfileId = uploaded.id;
      }

      // 1-b. 보호자 프로필 갱신
      final updatedUser = await userApi.update(
        auth.user.id,
        UserUpdate(
          nickname: _ownerNicknameCtrl.text.trim(),
          birthDate: _ownerBirthDate,
          gender: _ownerGender,
          selectedTags: _ownerKeywordIds.toList(),
          profileId: ownerProfileId,
        ),
      );

      // 2. 반려견 사진 업로드 → image_id 캡처
      int? imageId;
      if (_petPhotoPath != null) {
        final fileSize = await io.File(_petPhotoPath!).length();
        if (fileSize > 5 * 1024 * 1024) {
          throw Exception('5MB 이하 이미지만 업로드 가능합니다');
        }
        final uploaded = await imageApi.upload(_petPhotoPath!);
        imageId = uploaded.id;
      }

      // 3. 반려견 등록
      final pet = await petApi.create(
        PetCreate(
          breedId: _selectedBreed!.id,
          name: _petNameCtrl.text.trim(),
          birthDate: _petBirthDate,
          gender: _petGender,
          isNeutered: _petNeutered,
          selectedTags: _petKeywordIds.toList(),
          imageId: imageId,
        ),
      );

      // 4. AuthProvider user 갱신
      ref.read(authProvider.notifier).updateUser(updatedUser);

      // 5. primary_pet_id 동기화
      await ref.read(authProvider.notifier).refreshUser();

      if (!mounted) return;

      Fluttertoast.showToast(msg: '${pet.name}와의 추억을 시작합니다!');
      context.go(AppRoutes.home);
    } catch (e) {
      if (!mounted) return;
      Fluttertoast.showToast(msg: '등록 실패: $e');
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
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
                onGenderChanged: (gender) {
                  setState(() => _ownerGender = gender);
                },
                selectedKeywordIds: _ownerKeywordIds,
                onKeywordIdsChanged: (ids) {
                  setState(() {
                    _ownerKeywordIds
                      ..clear()
                      ..addAll(ids);
                  });
                },
                photoPath: _ownerPhotoPath,
                onPhotoTap: _pickOwnerPhoto,
              ),
              const SizedBox(height: 16),
              _PetSection(
                nameCtrl: _petNameCtrl,
                birthDate: _petBirthDate,
                onBirthDateTap: () => _pickBirthDate(owner: false),
                selectedBreed: _selectedBreed,
                onBreedSelected: (breed) {
                  setState(() => _selectedBreed = breed);
                },
                gender: _petGender,
                onGenderChanged: (gender) {
                  setState(() => _petGender = gender);
                },
                neutered: _petNeutered,
                onNeuteredChanged: (neutered) {
                  setState(() => _petNeutered = neutered);
                },
                selectedKeywordIds: _petKeywordIds,
                onKeywordIdsChanged: (ids) {
                  setState(() {
                    _petKeywordIds
                      ..clear()
                      ..addAll(ids);
                  });
                },
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
                        '시작하기!',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 기존 하위 위젯들 (변경 없음)
// ═══════════════════════════════════════════════════════════════════════════════

class _OwnerSection extends ConsumerWidget {
  const _OwnerSection({
    required this.nicknameCtrl,
    required this.birthDate,
    required this.onBirthDateTap,
    required this.gender,
    required this.onGenderChanged,
    required this.selectedKeywordIds,
    required this.onKeywordIdsChanged,
    required this.photoPath,
    required this.onPhotoTap,
  });

  final TextEditingController nicknameCtrl;
  final DateTime? birthDate;
  final VoidCallback onBirthDateTap;
  final Gender? gender;
  final ValueChanged<Gender> onGenderChanged;
  final Set<int> selectedKeywordIds;
  final ValueChanged<Set<int>> onKeywordIdsChanged;
  final String? photoPath;
  final VoidCallback onPhotoTap;

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
            Center(
              child: _OwnerPhotoPicker(path: photoPath, onTap: onPhotoTap),
            ),
            const SizedBox(height: 16),
            const _FieldLabel('닉네임'),
            TextFormField(
              controller: nicknameCtrl,
              decoration: const InputDecoration(hintText: '보호자님'),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return '닉네임을 입력하세요';
                }
                return null;
              },
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
              label: '라이프스타일',
              count: selectedKeywordIds.length,
            ),
            const SizedBox(height: 8),
            keywords.when(
              data: (list) => _KeywordSelectorField(
                title: '내 성향 고르기',
                bottomSheetTitle: '내 성향 고르기',
                description: '나의 외출 스타일과 취향을 최대 5개까지 선택하세요.',
                keywords: list,
                selectedIds: selectedKeywordIds,
                onChanged: onKeywordIdsChanged,
              ),
              loading: () => const Padding(
                padding: EdgeInsets.all(8),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (_, __) => const Text(
                '태그를 불러오지 못했어요. 잠시 후 다시 시도해주세요.',
                style: TextStyle(color: AppColors.mutedForeground, fontSize: 12),
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
    required this.onKeywordIdsChanged,
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
  final ValueChanged<Set<int>> onKeywordIdsChanged;
  final String? photoPath;
  final VoidCallback onPhotoTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final popularBreeds = ref.watch(popularBreedsProvider);
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
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return '이름을 입력하세요';
                }
                return null;
              },
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
            _BreedSelectField(
              selectedBreed: selectedBreed,
              onTap: () async {
                final selected = await showModalBottomSheet<Breed>(
                  context: context,
                  isScrollControlled: true,
                  backgroundColor: Colors.transparent,
                  builder: (_) => const _BreedPickerBottomSheet(),
                );

                if (selected != null) {
                  onBreedSelected(selected);
                }
              },
            ),
            const SizedBox(height: 12),
            const Text(
              '인기 견종',
              style: TextStyle(
                fontSize: 13,
                color: AppColors.subBrown2,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            popularBreeds.when(
              data: (list) => _BreedChips(
                breeds: list,
                selected: selectedBreed,
                onSelected: onBreedSelected,
              ),
              loading: () => const Padding(
                padding: EdgeInsets.all(8),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (error, _) => Text(
                '견종 로드 실패: $error',
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
            _KeywordChipsLabel(label: '성격', count: selectedKeywordIds.length),
            const SizedBox(height: 8),
            petKeywords.when(
              data: (list) => _KeywordSelectorField(
                title: '반려견 성향 고르기',
                bottomSheetTitle: '반려견 성향 고르기',
                description: '우리 강아지의 성격을 최대 5개까지 선택하세요.',
                keywords: list,
                selectedIds: selectedKeywordIds,
                onChanged: onKeywordIdsChanged,
              ),
              loading: () => const Padding(
                padding: EdgeInsets.all(8),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (_, __) => const Text(
                '태그를 불러오지 못했어요. 잠시 후 다시 시도해주세요.',
                style: TextStyle(color: AppColors.mutedForeground, fontSize: 12),
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
            color: date == null
                ? AppColors.mutedForeground
                : AppColors.darkBrown,
          ),
        ),
      ),
    );
  }

  static String _formatDate(DateTime date) {
    final year = date.year.toString().padLeft(4, '0');
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');

    return '$year-$month-$day';
  }
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
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (selected) ...[
              const Icon(Icons.check, size: 18, color: AppColors.brandOrange),
              const SizedBox(width: 4),
            ],
            Text(
              label,
              style: TextStyle(
                color: selected ? AppColors.brandOrange : AppColors.darkBrown,
                fontWeight: selected ? FontWeight.bold : FontWeight.normal,
              ),
            ),
          ],
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
    final isMax = count >= _maxKeywordSelections;

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          '$label (최대 $_maxKeywordSelections개)',
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
            color: isMax ? AppColors.brandOrange : AppColors.mutedForeground,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}

class _KeywordSelectorField extends StatelessWidget {
  const _KeywordSelectorField({
    required this.title,
    required this.bottomSheetTitle,
    required this.description,
    required this.keywords,
    required this.selectedIds,
    required this.onChanged,
  });

  final String title;
  final String bottomSheetTitle;
  final String description;
  final List<Keyword> keywords;
  final Set<int> selectedIds;
  final ValueChanged<Set<int>> onChanged;

  @override
  Widget build(BuildContext context) {
    final selectedKeywords = keywords
        .where((keyword) => selectedIds.contains(keyword.id))
        .take(_maxKeywordSelections)
        .toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: () async {
            final result = await showModalBottomSheet<Set<int>>(
              context: context,
              isScrollControlled: true,
              backgroundColor: Colors.transparent,
              builder: (_) => _KeywordPickerBottomSheet(
                title: bottomSheetTitle,
                description: description,
                keywords: keywords,
                selectedIds: selectedIds,
              ),
            );

            if (result != null) {
              onChanged(result);
            }
          },
          borderRadius: BorderRadius.circular(14),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border.all(color: AppColors.beige),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      fontSize: 15,
                      color: AppColors.darkBrown,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                Text(
                  '${selectedIds.length}/$_maxKeywordSelections',
                  style: TextStyle(
                    fontSize: 13,
                    color: selectedIds.isEmpty
                        ? AppColors.mutedForeground
                        : AppColors.brandOrange,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(width: 6),
                const Icon(
                  Icons.keyboard_arrow_down_rounded,
                  color: AppColors.subBrown2,
                ),
              ],
            ),
          ),
        ),
        if (selectedKeywords.isNotEmpty) ...[
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final keyword in selectedKeywords)
                InputChip(
                  label: Text(keyword.name),
                  selected: true,
                  selectedColor: AppColors.peach,
                  backgroundColor: Colors.white,
                  checkmarkColor: AppColors.brandOrange,
                  deleteIconColor: AppColors.brandOrange,
                  onDeleted: () {
                    final next = {...selectedIds};
                    next.remove(keyword.id);
                    onChanged(next);
                  },
                ),
            ],
          ),
        ] else ...[
          const SizedBox(height: 8),
          const Text(
            '선택한 성향이 아직 없어요.',
            style: TextStyle(fontSize: 12, color: AppColors.mutedForeground),
          ),
        ],
      ],
    );
  }
}

class _KeywordPickerBottomSheet extends StatefulWidget {
  const _KeywordPickerBottomSheet({
    required this.title,
    required this.description,
    required this.keywords,
    required this.selectedIds,
  });

  final String title;
  final String description;
  final List<Keyword> keywords;
  final Set<int> selectedIds;

  @override
  State<_KeywordPickerBottomSheet> createState() =>
      _KeywordPickerBottomSheetState();
}

class _KeywordPickerBottomSheetState extends State<_KeywordPickerBottomSheet> {
  late final Set<int> _tempSelectedIds;

  @override
  void initState() {
    super.initState();
    _tempSelectedIds = {...widget.selectedIds};
  }

  void _toggleKeyword(int id) {
    setState(() {
      if (_tempSelectedIds.contains(id)) {
        _tempSelectedIds.remove(id);
        return;
      }

      if (_tempSelectedIds.length >= _maxKeywordSelections) {
        Fluttertoast.showToast(msg: '최대 $_maxKeywordSelections개까지 선택 가능합니다.');
        return;
      }

      _tempSelectedIds.add(id);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.76,
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 42,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.beige,
                borderRadius: BorderRadius.circular(99),
              ),
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: Text(
                  widget.title,
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: AppColors.darkBrown,
                  ),
                ),
              ),
              IconButton(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close_rounded),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            widget.description,
            style: const TextStyle(
              fontSize: 14,
              color: AppColors.mutedForeground,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            '${_tempSelectedIds.length}/$_maxKeywordSelections 선택됨',
            style: TextStyle(
              fontSize: 13,
              color: _tempSelectedIds.isEmpty
                  ? AppColors.mutedForeground
                  : AppColors.brandOrange,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: SingleChildScrollView(
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final keyword in widget.keywords)
                    FilterChip(
                      label: Text(keyword.name),
                      selected: _tempSelectedIds.contains(keyword.id),
                      onSelected: (_) => _toggleKeyword(keyword.id),
                      selectedColor: AppColors.peach,
                      checkmarkColor: AppColors.brandOrange,
                      backgroundColor: Colors.white,
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () {
                    setState(() {
                      _tempSelectedIds.clear();
                    });
                  },
                  child: const Text('초기화'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                flex: 2,
                child: FilledButton(
                  onPressed: () {
                    Navigator.pop(context, {..._tempSelectedIds});
                  },
                  child: const Text('선택 완료'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _BreedSelectField extends StatelessWidget {
  const _BreedSelectField({required this.selectedBreed, required this.onTap});

  final Breed? selectedBreed;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final hasSelected = selectedBreed != null;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: AppColors.beige),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          children: [
            Expanded(
              child: Text(
                hasSelected ? selectedBreed!.nameKo : '우리 강아지는 어떤 견종인가요?',
                style: TextStyle(
                  fontSize: 15,
                  color: hasSelected
                      ? AppColors.darkBrown
                      : AppColors.mutedForeground,
                  fontWeight: hasSelected ? FontWeight.w600 : FontWeight.normal,
                ),
              ),
            ),
            const Icon(
              Icons.keyboard_arrow_down_rounded,
              color: AppColors.subBrown2,
            ),
          ],
        ),
      ),
    );
  }
}

class _BreedPickerBottomSheet extends ConsumerStatefulWidget {
  const _BreedPickerBottomSheet();

  @override
  ConsumerState<_BreedPickerBottomSheet> createState() =>
      _BreedPickerBottomSheetState();
}

class _BreedPickerBottomSheetState
    extends ConsumerState<_BreedPickerBottomSheet> {
  final _searchCtrl = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final breedsAsync = ref.watch(breedSearchProvider(_query));

    return Container(
      height: MediaQuery.of(context).size.height * 0.82,
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 42,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.beige,
                borderRadius: BorderRadius.circular(99),
              ),
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              const Expanded(
                child: Text(
                  '견종 선택',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: AppColors.darkBrown,
                  ),
                ),
              ),
              IconButton(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close_rounded),
              ),
            ],
          ),
          const SizedBox(height: 4),
          const Text(
            '이름으로 검색하거나 목록에서 선택하세요',
            style: TextStyle(fontSize: 14, color: AppColors.mutedForeground),
          ),
          const SizedBox(height: 18),
          TextField(
            controller: _searchCtrl,
            onChanged: (value) {
              setState(() {
                _query = value.trim();
              });
            },
            decoration: InputDecoration(
              hintText: '견종 이름 검색...',
              prefixIcon: const Icon(Icons.search_rounded),
              filled: true,
              fillColor: Colors.white,
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 14,
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16),
                borderSide: const BorderSide(color: AppColors.beige),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16),
                borderSide: const BorderSide(
                  color: AppColors.brandOrange,
                  width: 1.5,
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: breedsAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => Center(
                child: Text(
                  '견종 목록을 불러오지 못했어요.\n$error',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppColors.destructive),
                ),
              ),
              data: (breeds) {
                if (breeds.isEmpty) {
                  return const Center(
                    child: Text(
                      '검색 결과가 없어요.',
                      style: TextStyle(color: AppColors.mutedForeground),
                    ),
                  );
                }

                return GridView.builder(
                  itemCount: breeds.length,
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    mainAxisExtent: 48,
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 6,
                  ),
                  itemBuilder: (context, index) {
                    final breed = breeds[index];

                    return InkWell(
                      onTap: () => Navigator.pop(context, breed),
                      borderRadius: BorderRadius.circular(10),
                      child: Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          breed.nameKo,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 15,
                            color: AppColors.darkBrown,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
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
            style: TextStyle(fontSize: 12, color: AppColors.mutedForeground),
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

/// 보호자 프로필 사진 picker — 반려견 수정 모달과 동일한 UX.
/// 동그란 아바타 + 우하단 주황 카메라 배지, 탭하면 갤러리 열림.
class _OwnerPhotoPicker extends StatelessWidget {
  const _OwnerPhotoPicker({required this.path, required this.onTap});

  final String? path;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    ImageProvider? bgImage;
    if (path != null) {
      bgImage = path!.startsWith('http')
          ? NetworkImage(path!)
          : FileImage(io.File(path!));
    }

    return GestureDetector(
      onTap: onTap,
      child: Stack(
        alignment: Alignment.bottomRight,
        children: [
          CircleAvatar(
            radius: 48,
            backgroundColor: AppColors.peach,
            backgroundImage: bgImage,
            child: bgImage == null
                ? const Icon(LucideIcons.user,
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
