import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:withdog_app/core/theme/app_colors.dart';

void main() {
  test('AppColors brand orange matches design token', () {
    // 브랜드 주황 컬러 토큰 회귀 가드
    expect(AppColors.brandOrange, const Color(0xFFF4845F));
  });

  test('AppColors primary matches theme.css --primary', () {
    expect(AppColors.primary, const Color(0xFF030213));
  });
}
