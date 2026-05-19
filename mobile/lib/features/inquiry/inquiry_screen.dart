import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/theme/app_colors.dart';
import 'inquiry_service.dart';

class InquiryScreen extends StatefulWidget {
  const InquiryScreen({super.key});

  @override
  State<InquiryScreen> createState() => _InquiryScreenState();
}

class _InquiryScreenState extends State<InquiryScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _messageCtrl = TextEditingController();
  bool _sending = false;

  @override
  void dispose() {
    _nameCtrl.dispose();
    _emailCtrl.dispose();
    _messageCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _sending = true);
    try {
      final ok = await sendInquiry(
        name: _nameCtrl.text.trim(),
        email: _emailCtrl.text.trim(),
        message: _messageCtrl.text.trim(),
      );
      if (!mounted) return;
      if (ok) {
        Fluttertoast.showToast(msg: '문의가 전송되었습니다!');
        Navigator.of(context).pop();
      } else {
        Fluttertoast.showToast(msg: '전송에 실패했습니다. 다시 시도해주세요.');
      }
    } catch (e) {
      Fluttertoast.showToast(msg: '오류가 발생했습니다: $e');
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9F5F0),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(LucideIcons.arrowLeft, color: AppColors.darkBrown),
          onPressed: () => Navigator.of(context).pop(),
        ),
        centerTitle: true,
        title: const Text(
          '고객센터',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: AppColors.darkBrown,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 40),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── 안내 카드 ──
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFFFFF7ED), Color(0xFFFFEDD5)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.beige),
                ),
                child: const Row(
                  children: [
                    Icon(LucideIcons.mailQuestion, size: 28,
                        color: AppColors.brandOrange),
                    SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '무엇이든 물어보세요!',
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w800,
                              color: AppColors.darkBrown,
                            ),
                          ),
                          SizedBox(height: 2),
                          Text(
                            '버그 제보, 기능 제안, 이용 문의 등',
                            style: TextStyle(
                              fontSize: 12,
                              color: AppColors.subBrown,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // ── 이름 ──
              const _FieldLabel(text: '이름'),
              const SizedBox(height: 6),
              TextFormField(
                controller: _nameCtrl,
                decoration: _inputDecoration('이름을 입력해주세요'),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? '이름을 입력해주세요' : null,
              ),
              const SizedBox(height: 18),

              // ── 이메일 ──
              const _FieldLabel(text: '이메일'),
              const SizedBox(height: 6),
              TextFormField(
                controller: _emailCtrl,
                keyboardType: TextInputType.emailAddress,
                decoration: _inputDecoration('답변 받을 이메일을 입력해주세요'),
                validator: (v) {
                  if (v == null || v.trim().isEmpty) return '이메일을 입력해주세요';
                  if (!v.contains('@')) return '올바른 이메일 형식이 아닙니다';
                  return null;
                },
              ),
              const SizedBox(height: 18),

              // ── 문의 내용 ──
              const _FieldLabel(text: '문의 내용'),
              const SizedBox(height: 6),
              TextFormField(
                controller: _messageCtrl,
                maxLines: 6,
                decoration: _inputDecoration('문의 내용을 입력해주세요'),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? '문의 내용을 입력해주세요' : null,
              ),
              const SizedBox(height: 28),

              // ── 전송 버튼 ──
              SizedBox(
                width: double.infinity,
                height: 50,
                child: FilledButton(
                  onPressed: _sending ? null : _submit,
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.brandOrange,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  child: _sending
                      ? const SizedBox(
                          width: 22,
                          height: 22,
                          child: CircularProgressIndicator(
                            strokeWidth: 2.5,
                            color: Colors.white,
                          ),
                        )
                      : const Text(
                          '문의 보내기',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  InputDecoration _inputDecoration(String hint) {
    return InputDecoration(
      hintText: hint,
      hintStyle: const TextStyle(
        fontSize: 14,
        color: AppColors.mutedForeground,
      ),
      filled: true,
      fillColor: Colors.white,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.beige),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.beige),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.brandOrange, width: 1.5),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.destructive),
      ),
    );
  }
}

class _FieldLabel extends StatelessWidget {
  const _FieldLabel({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w700,
        color: AppColors.darkBrown,
      ),
    );
  }
}
