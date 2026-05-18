import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

/// 외부 지도 앱 길찾기 딥링크 서비스.
///
/// 우선순위: 카카오맵 앱 → 네이버지도 앱 → 카카오맵 웹 (최종 fallback).
class DirectionsService {
  DirectionsService._();

  /// 목적지까지 길찾기를 외부 지도 앱으로 열어준다.
  ///
  /// [startLat]/[startLng]: 출발지 좌표 (null이면 앱에서 현재 위치 사용).
  /// [endLat]/[endLng]: 목적지 좌표 (필수).
  /// [destinationName]: 목적지 이름 (URL 인코딩됨).
  static Future<void> open({
    required BuildContext context,
    required double endLat,
    required double endLng,
    required String destinationName,
    double? startLat,
    double? startLng,
  }) async {
    final encName = Uri.encodeComponent(destinationName);

    // ── 1) 카카오맵 앱 딥링크 ──────────────────────────────────────────────
    // sp 없으면 현재 위치를 출발로 자동 사용 (카카오맵 기본 동작).
    final kakaoAppUri = startLat != null && startLng != null
        ? Uri.parse(
            'kakaomap://route?sp=$startLat,$startLng&ep=$endLat,$endLng&by=CAR',
          )
        : Uri.parse(
            'kakaomap://route?ep=$endLat,$endLng&by=CAR',
          );

    if (await canLaunchUrl(kakaoAppUri)) {
      await launchUrl(kakaoAppUri, mode: LaunchMode.externalApplication);
      return;
    }

    // ── 2) 네이버지도 앱 딥링크 ───────────────────────────────────────────
    final naverAppUri = startLat != null && startLng != null
        ? Uri.parse(
            'nmap://route/car'
            '?slat=$startLat&slng=$startLng&sname=${Uri.encodeComponent("출발지")}'
            '&dlat=$endLat&dlng=$endLng&dname=$encName'
            '&appname=com.withdog.app',
          )
        : Uri.parse(
            'nmap://route/car'
            '?dlat=$endLat&dlng=$endLng&dname=$encName'
            '&appname=com.withdog.app',
          );

    if (await canLaunchUrl(naverAppUri)) {
      await launchUrl(naverAppUri, mode: LaunchMode.externalApplication);
      return;
    }

    // ── 3) 카카오맵 웹 fallback ────────────────────────────────────────────
    final kakaoWebUri = Uri.parse(
      'https://map.kakao.com/link/to/$encName,$endLat,$endLng',
    );

    if (await canLaunchUrl(kakaoWebUri)) {
      await launchUrl(kakaoWebUri, mode: LaunchMode.externalApplication);
      return;
    }

    // ── 4) 모두 실패 ──────────────────────────────────────────────────────
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('지도 앱을 열 수 없습니다. 카카오맵 또는 네이버지도를 설치해 주세요.')),
      );
    }
  }
}
