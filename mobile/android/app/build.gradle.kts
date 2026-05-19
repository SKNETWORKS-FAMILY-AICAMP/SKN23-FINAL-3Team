plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.withdog.app"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        applicationId = "com.withdog.app"
        // flutter_inappwebview 6.x 는 minSdk 21+ 필요 (Flutter 기본도 21 이상)
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName

        // flutter_appauth — Google InstalledApp client 의 reverse client ID 스킴.
        // Cloud Console 발급 client id `<prefix>.apps.googleusercontent.com` 의
        // reverse 형식 `com.googleusercontent.apps.<prefix>` 로 deep link 등록.
        // 시연 단계 = 하드코딩 (사용자 결정 옵션 (c) 2026-05-04). 발표 후 (b) 자동화 후보.
        manifestPlaceholders["appAuthRedirectScheme"] =
            "com.googleusercontent.apps.151754567014-7jih9bh5en3um8f9h04ceguao91ne5la"
    }

    buildTypes {
        release {
            // TODO: Add your own signing config for the release build.
            // Signing with the debug keys for now, so `flutter run --release` works.
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

flutter {
    source = "../.."
}
