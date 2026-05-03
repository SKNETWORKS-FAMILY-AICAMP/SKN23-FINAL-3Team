import 'package:flutter/material.dart';

class AppColors {
  // theme.css :root 토큰
  static const primary = Color(0xFF030213);
  static const accent = Color(0xFFE9EBEF);
  static const muted = Color(0xFFECECF0);
  static const mutedForeground = Color(0xFF717182);
  static const destructive = Color(0xFFD4183D);
  static const inputBackground = Color(0xFFF3F3F5);

  // 코드 inline 브랜드 컬러 (theme.css 미등록 — Flutter 측 추출)
  static const brandOrange = Color(0xFFF4845F);
  static const darkBrown = Color(0xFF3D2B1F);
  static const subBrown = Color(0xFF7A5C4D);
  static const subBrown2 = Color(0xFF8B6355);
  static const peach = Color(0xFFFFF0E6);
  static const beige = Color(0xFFEEDFD3);

  // 메인 배경 그라데이션 (HomePage 등)
  static const gradientStart = Color(0xFFF1F1F3);
  static const gradientEnd = Color(0xFFECEDEA);

  AppColors._();
}
