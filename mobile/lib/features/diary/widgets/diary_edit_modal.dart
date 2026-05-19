import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../../core/theme/app_colors.dart';
import '../../../shared/models/diary.dart';
import '../diary_types.dart';
import '../diary_providers.dart';

const _kCreamBg = Color(0xFFFFF8F3);
const _kOrangeBorder = Color(0xFFFFD2C2);

/// 다이어리 수정 모달 — DiaryDetailModalSheet 에서 연필 아이콘으로 진입.
/// 저장 성공 시 `Navigator.pop(updatedDiary)` 로 수정된 Diary 를 반환합니다.
class DiaryEditModal extends ConsumerStatefulWidget {
  const DiaryEditModal({super.key, required this.diary});

  final Diary diary;

  @override
  ConsumerState<DiaryEditModal> createState() => _DiaryEditModalState();
}

class _DiaryEditModalState extends ConsumerState<DiaryEditModal> {
  late final TextEditingController _titleCtrl;
  late final TextEditingController _contentCtrl;
  late final TextEditingController _summaryCtrl;
  String? _emotion;
  late DateTime _diaryDate;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _titleCtrl = TextEditingController(text: widget.diary.title ?? '');
    _contentCtrl = TextEditingController(text: widget.diary.content ?? '');
    _summaryCtrl = TextEditingController(text: widget.diary.summary ?? '');
    _emotion = widget.diary.emotion;
    _diaryDate = widget.diary.diaryDate;
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _contentCtrl.dispose();
    _summaryCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _diaryDate,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
    );
    if (picked != null && mounted) setState(() => _diaryDate = picked);
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      final updated = await ref.read(diaryApiProvider).update(
        widget.diary.id,
        DiaryUpdate(
          title: _titleCtrl.text.trim().isNotEmpty
              ? _titleCtrl.text.trim()
              : null,
          content: _contentCtrl.text.trim().isNotEmpty
              ? _contentCtrl.text.trim()
              : null,
          summary: _summaryCtrl.text.trim().isNotEmpty
              ? _summaryCtrl.text.trim()
              : null,
          emotion: _emotion,
          diaryDate: _diaryDate,
        ),
      );
      if (mounted) {
        Fluttertoast.showToast(msg: '일기가 수정됐어요');
        Navigator.of(context).pop(updated);
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
              // 드래그 핸들
              const _DragHandle(),

              // 헤더
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 4, 12, 4),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        '일기 수정',
                        style: GoogleFonts.gaegu(
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

              const Divider(height: 1, color: _kOrangeBorder),

              // 본문 폼
              Expanded(
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
                  children: [
                    // 날짜
                    const _Label(text: '날짜'),
                    InkWell(
                      onTap: _pickDate,
                      borderRadius: BorderRadius.circular(8),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 12,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: _kOrangeBorder),
                        ),
                        child: Row(
                          children: [
                            const Icon(
                              Icons.calendar_today,
                              size: 16,
                              color: AppColors.brandOrange,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              _formatDate(_diaryDate),
                              style: const TextStyle(
                                fontSize: 14,
                                color: AppColors.darkBrown,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                    const SizedBox(height: 16),

                    // 감정
                    const _Label(text: '감정'),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        for (final e in DiaryEmotion.all)
                          ChoiceChip(
                            label: Text(
                              '${e.emoji} ${e.label}',
                              style: TextStyle(
                                fontSize: 12,
                                color: _emotion == e.emoji
                                    ? AppColors.brandOrange
                                    : AppColors.darkBrown,
                              ),
                            ),
                            selected: _emotion == e.emoji,
                            selectedColor: AppColors.peach,
                            backgroundColor: Colors.white,
                            side: BorderSide(
                              color: _emotion == e.emoji
                                  ? AppColors.brandOrange
                                  : _kOrangeBorder,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(20),
                            ),
                            onSelected: (_) =>
                                setState(() => _emotion = e.emoji),
                          ),
                      ],
                    ),

                    const SizedBox(height: 16),

                    // 제목
                    const _Label(text: '제목'),
                    _StyledField(
                      controller: _titleCtrl,
                      hintText: '제목을 입력하세요',
                      useGaegu: true,
                    ),

                    const SizedBox(height: 16),

                    // 요약
                    const _Label(text: '한줄 요약'),
                    _StyledField(
                      controller: _summaryCtrl,
                      hintText: '한줄 요약을 입력하세요',
                      useGaegu: true,
                    ),

                    const SizedBox(height: 16),

                    // 본문
                    const _Label(text: '본문'),
                    _StyledField(
                      controller: _contentCtrl,
                      hintText: '본문을 입력하세요',
                      maxLines: 8,
                      useGaegu: true,
                    ),

                    const SizedBox(height: 24),

                    // 저장 버튼
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: _saving ? null : _save,
                        style: FilledButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          backgroundColor: AppColors.brandOrange,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
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
                            : const Text(
                                '저장',
                                style: TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
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

  static String _formatDate(DateTime d) =>
      '${d.year}.${d.month.toString().padLeft(2, '0')}.${d.day.toString().padLeft(2, '0')}';
}

// ── 공용 위젯 ──────────────────────────────────────────────────────────────

class _DragHandle extends StatelessWidget {
  const _DragHandle();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 10),
        width: 36,
        height: 4,
        decoration: BoxDecoration(
          color: AppColors.beige,
          borderRadius: BorderRadius.circular(2),
        ),
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

class _StyledField extends StatelessWidget {
  const _StyledField({
    required this.controller,
    required this.hintText,
    this.maxLines = 1,
    this.useGaegu = false,
  });

  final TextEditingController controller;
  final String hintText;
  final int maxLines;
  final bool useGaegu;

  @override
  Widget build(BuildContext context) {
    final baseStyle = useGaegu
        ? GoogleFonts.gaegu(fontSize: 14, color: AppColors.darkBrown)
        : const TextStyle(fontSize: 14, color: AppColors.darkBrown);

    return TextField(
      controller: controller,
      maxLines: maxLines,
      style: baseStyle,
      decoration: InputDecoration(
        hintText: hintText,
        hintStyle: TextStyle(
          fontSize: 14,
          color: AppColors.mutedForeground.withValues(alpha: 0.6),
        ),
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
          borderSide: const BorderSide(
            color: AppColors.brandOrange,
            width: 1.5,
          ),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 12,
          vertical: 12,
        ),
      ),
    );
  }
}
