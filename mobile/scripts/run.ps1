# mobile/scripts/run.ps1
# `flutter run` 래퍼 — 콘솔 출력 + 타임스탬프 로그 파일 동시 저장.
#
# 사용:
#   ./scripts/run.ps1                       # debug 모드, 자동 device 선택
#   ./scripts/run.ps1 --release             # release 모드
#   ./scripts/run.ps1 -d emulator-5554      # 특정 device 지정
#   ./scripts/run.ps1 --profile -v          # 추가 인자 자유롭게 forward
#
# 산출물:
#   mobile/logs/flutter-run-YYYYMMDD-HHmmss.log  (UTF-8, .gitignore *.log 매칭 → 커밋 차단)
#
# 디자인 메모:
#   - `2>&1 | ForEach-Object { Write-Host + Add-Content -Encoding utf8 }` 패턴.
#     PS 5.1 의 `Tee-Object` 는 `-Encoding` 미지원 (default UTF-16 LE BOM) — 헤더 UTF-8
#     과 섞이면 파일 인코딩 혼합으로 외부 도구(AI/grep) 가 못 읽음. ForEach 우회로 UTF-8
#     일관 유지. 라인별 flush 라 실시간성도 더 좋음.
#   - 자식 프로세스 cwd = mobile/. 스크립트 어디서 호출해도 동작.

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$FlutterArgs = @()
)

$ErrorActionPreference = 'Continue'

# 경로 해석 — script 위치 기준 mobile/ 와 root 식별
$mobileRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $mobileRoot
$envFile = Join-Path $repoRoot '.env'
$logsDir = Join-Path $mobileRoot 'logs'

# logs/ 자동 생성
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

# 타임스탬프 로그 파일
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$logFile = Join-Path $logsDir "flutter-run-$timestamp.log"

# `--dart-define-from-file` + 사용자 인자 합성
$baseArgs = @('run', "--dart-define-from-file=$envFile")
$allArgs = $baseArgs + $FlutterArgs

# 헤더 출력 (콘솔 + 로그)
$header = @"
==============================================================================
 flutter $($allArgs -join ' ')
 cwd      : $mobileRoot
 envFile  : $envFile
 logFile  : $logFile
 started  : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
==============================================================================
"@
Write-Host $header -ForegroundColor Cyan
Set-Content -Path $logFile -Value $header -Encoding utf8

Push-Location $mobileRoot
try {
    # 핵심: stdout+stderr 합쳐 라인별로 콘솔 출력 + UTF-8 로그 append
    & flutter @allArgs 2>&1 | ForEach-Object {
        $line = $_.ToString()
        Write-Host $line
        Add-Content -Path $logFile -Value $line -Encoding utf8
    }
}
finally {
    Pop-Location
    $footer = "`n[done] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -- saved: $logFile"
    Write-Host $footer -ForegroundColor Green
    Add-Content -Path $logFile -Value $footer -Encoding utf8
}
