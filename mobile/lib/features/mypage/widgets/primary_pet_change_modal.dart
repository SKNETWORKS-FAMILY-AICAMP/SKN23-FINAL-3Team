import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../../core/theme/app_colors.dart';
import '../../../shared/models/pet.dart';
import '../../../shared/models/user.dart';
import '../../auth/auth_providers.dart';
import '../../onboarding/onboarding_providers.dart';

/// 대표 반려견 변경 — 리스트 라디오 모달 시트.
///
/// UI 디테일 #1 (사용자 결정 2026-05-03): 리스트 라디오 (반려견 카드 그리드와
/// 자연스럽게 결합). 확인 시 `PATCH /api/users/{id}` body `{primary_pet_id}` →
/// `auth.refreshUser()` 로 nested `primary_pet` 갱신.
class PrimaryPetChangeModal extends ConsumerStatefulWidget {
  const PrimaryPetChangeModal({super.key, required this.user});

  final User user;

  @override
  ConsumerState<PrimaryPetChangeModal> createState() =>
      _PrimaryPetChangeModalState();
}

class _PrimaryPetChangeModalState extends ConsumerState<PrimaryPetChangeModal> {
  int? _selectedPetId;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _selectedPetId = widget.user.primaryPetId;
  }

  Future<void> _save() async {
    final id = _selectedPetId;
    if (id == null || id == widget.user.primaryPetId) {
      Navigator.of(context).pop();
      return;
    }
    setState(() => _saving = true);
    try {
      final userApi = ref.read(userApiProvider);
      await userApi.update(widget.user.id, UserUpdate(primaryPetId: id));
      // nested primary_pet 갱신 — userApi.update 응답엔 일관 안 되므로 me 재조회
      await ref.read(authProvider.notifier).refreshUser();
      if (!mounted) return;
      Navigator.of(context).pop();
      Fluttertoast.showToast(msg: '대표 반려견이 변경됐어요');
    } catch (e) {
      if (!mounted) return;
      Fluttertoast.showToast(msg: '대표 변경 실패: $e');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final pets = ref.watch(userPetsProvider);
    return DraggableScrollableSheet(
      initialChildSize: 0.6,
      minChildSize: 0.4,
      maxChildSize: 0.9,
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
                      '대표 반려견 변경',
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
              child: pets.when(
                data: (list) {
                  if (list.isEmpty) {
                    return const Center(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: Text(
                          '등록된 반려견이 없어요',
                          style: TextStyle(color: AppColors.mutedForeground),
                        ),
                      ),
                    );
                  }
                  return ListView.builder(
                    controller: scrollController,
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    itemCount: list.length,
                    itemBuilder: (_, i) => _PetRadioTile(
                      pet: list[i],
                      groupValue: _selectedPetId,
                      onChanged: (v) => setState(() => _selectedPetId = v),
                    ),
                  );
                },
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (e, _) => Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Text(
                      '반려견 목록 로드 실패: $e',
                      style: const TextStyle(color: AppColors.destructive),
                    ),
                  ),
                ),
              ),
            ),
            SafeArea(
              top: false,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                child: FilledButton(
                  onPressed: _saving ? null : _save,
                  style: FilledButton.styleFrom(
                    minimumSize: const Size.fromHeight(48),
                  ),
                  child: _saving
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : const Text('대표로 설정'),
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _PetRadioTile extends StatelessWidget {
  const _PetRadioTile({
    required this.pet,
    required this.groupValue,
    required this.onChanged,
  });

  final Pet pet;
  final int? groupValue;
  final ValueChanged<int?> onChanged;

  @override
  Widget build(BuildContext context) {
    return RadioListTile<int>(
      value: pet.id,
      // ignore: deprecated_member_use
      groupValue: groupValue,
      // ignore: deprecated_member_use
      onChanged: onChanged,
      activeColor: AppColors.brandOrange,
      title: Text(
        pet.name,
        style: const TextStyle(
          fontWeight: FontWeight.bold,
          color: AppColors.darkBrown,
        ),
      ),
      subtitle: Text(
        '${pet.age != null ? '${pet.age}세' : ''}'
        '${pet.gender != null ? ' · ${pet.gender!.label}' : ''}',
        style: const TextStyle(fontSize: 12, color: AppColors.mutedForeground),
      ),
    );
  }
}
